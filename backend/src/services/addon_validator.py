"""
Add-on Validator Service
Validates add-on compatibility and business rules
"""
import re
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.addon_compatibility import AddonCompatibility
from ..repositories.addon_compatibility_repository import AddonCompatibilityRepository

logger = structlog.get_logger(__name__)


class AddonValidator:
    """Service for validating add-on compatibility and business rules"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.addon_repo = AddonCompatibilityRepository(session)

    async def validate_addon_compatibility(
        self,
        addon_sku_id: str,
        base_sku_id: str,
        quantity: int,
        tenant_id: Optional[str] = None,
        domain_name: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation of add-on compatibility

        Args:
            addon_sku_id: Partner Center SKU ID for the add-on
            base_sku_id: Partner Center SKU ID for the base product
            quantity: Quantity of add-ons to validate
            tenant_id: Microsoft tenant ID (optional)
            domain_name: Domain name for validation (optional)

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        validation_errors = []

        # Step 1: Validate basic compatibility mapping exists
        mapping = await self.addon_repo.get_specific_mapping(addon_sku_id, base_sku_id)
        if not mapping:
            validation_errors.append(
                f"No compatibility mapping found between add-on '{addon_sku_id}' and base SKU '{base_sku_id}'"
            )
            return False, validation_errors

        # Step 2: Validate mapping is active and available
        if not mapping.is_active:
            validation_errors.append(
                f"Compatibility mapping is inactive for add-on '{addon_sku_id}'"
            )

        if not mapping.is_available():
            validation_errors.append(
                f"Compatibility mapping is not currently available for add-on '{addon_sku_id}'"
            )

        # Step 3: Validate quantity rules
        quantity_valid, quantity_errors = self._validate_quantity_rules(
            mapping, quantity
        )
        if not quantity_valid:
            validation_errors.extend(quantity_errors)

        # Step 4: Validate tenant/domain requirements
        tenant_valid, tenant_errors = await self._validate_tenant_requirements(
            mapping, tenant_id, domain_name
        )
        if not tenant_valid:
            validation_errors.extend(tenant_errors)

        # Step 5: Validate business rules
        business_valid, business_errors = await self._validate_business_rules(
            addon_sku_id, base_sku_id, quantity, tenant_id
        )
        if not business_valid:
            validation_errors.extend(business_errors)

        # Step 6: Validate service limits
        limits_valid, limits_errors = await self._validate_service_limits(
            addon_sku_id, base_sku_id, quantity, tenant_id
        )
        if not limits_valid:
            validation_errors.extend(limits_errors)

        is_valid = len(validation_errors) == 0

        if is_valid:
            logger.info(
                "addon_validation_passed",
                addon_sku_id=addon_sku_id,
                base_sku_id=base_sku_id,
                quantity=quantity,
                tenant_id=tenant_id,
            )
        else:
            logger.warning(
                "addon_validation_failed",
                addon_sku_id=addon_sku_id,
                base_sku_id=base_sku_id,
                quantity=quantity,
                tenant_id=tenant_id,
                errors=validation_errors,
            )

        return is_valid, validation_errors

    def _validate_quantity_rules(
        self, mapping: AddonCompatibility, quantity: int
    ) -> Tuple[bool, List[str]]:
        """Validate quantity rules for add-on"""
        errors = []

        # Check minimum quantity
        if quantity < mapping.min_quantity:
            errors.append(
                f"Quantity {quantity} is below minimum required {mapping.min_quantity}"
            )

        # Check maximum quantity
        if mapping.max_quantity is not None and quantity > mapping.max_quantity:
            errors.append(
                f"Quantity {quantity} exceeds maximum allowed {mapping.max_quantity}"
            )

        # Check quantity multiplier
        if quantity % mapping.quantity_multiplier != 0:
            errors.append(
                f"Quantity {quantity} must be a multiple of {mapping.quantity_multiplier}"
            )

        # Validate reasonable quantity ranges
        if quantity <= 0:
            errors.append("Quantity must be greater than 0")
        elif quantity > 10000:
            errors.append("Quantity exceeds reasonable maximum of 10000")

        return len(errors) == 0, errors

    async def _validate_tenant_requirements(
        self,
        mapping: AddonCompatibility,
        tenant_id: Optional[str],
        domain_name: Optional[str],
    ) -> Tuple[bool, List[str]]:
        """Validate tenant and domain requirements"""
        errors = []

        if mapping.requires_tenant_validation and not tenant_id:
            errors.append("Tenant ID is required for this add-on validation")

        if mapping.requires_domain_validation and not domain_name:
            errors.append("Domain name is required for this add-on validation")

        # Validate tenant ID format if provided
        if tenant_id and not self._is_valid_tenant_id(tenant_id):
            errors.append(f"Invalid tenant ID format: {tenant_id}")

        # Validate domain name format if provided
        if domain_name and not self._is_valid_domain_name(domain_name):
            errors.append(f"Invalid domain name format: {domain_name}")

        return len(errors) == 0, errors

    def _is_valid_tenant_id(self, tenant_id: str) -> bool:
        """Validate Microsoft tenant ID format"""
        # Microsoft tenant IDs are GUIDs
        guid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        return bool(re.match(guid_pattern, tenant_id))

    def _is_valid_domain_name(self, domain_name: str) -> bool:
        """Validate domain name format"""
        # Basic domain validation
        domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        return bool(re.match(domain_pattern, domain_name))

    async def _validate_business_rules(
        self,
        addon_sku_id: str,
        base_sku_id: str,
        quantity: int,
        tenant_id: Optional[str],
    ) -> Tuple[bool, List[str]]:
        """Validate business rules and constraints"""
        errors = []

        # Rule 1: Check for conflicting add-ons
        conflicts = await self._check_addon_conflicts(
            addon_sku_id, base_sku_id, tenant_id
        )
        if conflicts:
            errors.append(f"Add-on conflicts detected: {', '.join(conflicts)}")

        # Rule 2: Check for prerequisite add-ons
        missing_prerequisites = await self._check_prerequisites(
            addon_sku_id, base_sku_id, tenant_id
        )
        if missing_prerequisites:
            errors.append(
                f"Missing prerequisite add-ons: {', '.join(missing_prerequisites)}"
            )

        # Rule 3: Check for service type compatibility
        service_compatible = await self._check_service_type_compatibility(
            addon_sku_id, base_sku_id
        )
        if not service_compatible:
            errors.append("Service type incompatibility detected")

        return len(errors) == 0, errors

    async def _check_addon_conflicts(
        self, addon_sku_id: str, base_sku_id: str, tenant_id: Optional[str]
    ) -> List[str]:
        """Check for conflicting add-ons"""
        # Get the compatibility mapping
        mapping = await self.addon_repo.get_specific_mapping(addon_sku_id, base_sku_id)
        if not mapping:
            return []

        # Define known conflicts (this would typically come from configuration)
        conflicts = {
            "CFQ7TTC0P0HQ": [
                "CFQ7TTC0P0HS"
            ],  # Phone System vs Phone System with Calling Plan
            "CFQ7TTC0P0HR": ["CFQ7TTC0P0HS"],  # Domestic vs International Calling Plan
        }

        _conflicting_skus = conflicts.get(addon_sku_id, [])

        # In a real implementation, we would check what add-ons the tenant already has
        # against _conflicting_skus and return actual conflicts
        # For now, return empty list
        return []

    async def _check_prerequisites(
        self, addon_sku_id: str, base_sku_id: str, tenant_id: Optional[str]
    ) -> List[str]:
        """Check for missing prerequisite add-ons"""
        # Define known prerequisites (this would typically come from configuration)
        prerequisites = {
            "CFQ7TTC0P0HR": ["CFQ7TTC0P0HQ"],  # Calling Plan requires Phone System
        }

        _required_skus = prerequisites.get(addon_sku_id, [])

        # In a real implementation, we would check what add-ons the tenant already has
        # against _required_skus and return missing prerequisites
        # For now, return empty list
        # For now, return empty list
        return []

    async def _check_service_type_compatibility(
        self, addon_sku_id: str, base_sku_id: str
    ) -> bool:
        """Check service type compatibility"""
        mapping = await self.addon_repo.get_specific_mapping(addon_sku_id, base_sku_id)
        if not mapping:
            return False

        # Get all mappings for the same service type
        service_mappings = await self.addon_repo.get_by_service_type(
            mapping.service_type
        )

        # Check if there are any active mappings
        active_mappings = [m for m in service_mappings if m.is_active]

        return len(active_mappings) > 0

    async def _validate_service_limits(
        self,
        addon_sku_id: str,
        base_sku_id: str,
        quantity: int,
        tenant_id: Optional[str],
    ) -> Tuple[bool, List[str]]:
        """Validate service-specific limits"""
        errors = []

        mapping = await self.addon_repo.get_specific_mapping(addon_sku_id, base_sku_id)
        if not mapping:
            return False, ["No compatibility mapping found"]

        # Check service-specific limits based on add-on category
        if mapping.addon_category == "Calling Plan":
            # Validate calling plan limits
            if quantity > 1000:  # Example limit
                errors.append("Calling plan quantity exceeds maximum limit of 1000")

        elif mapping.addon_category == "Storage":
            # Validate storage limits
            if quantity > 5000:  # Example limit
                errors.append("Storage add-on quantity exceeds maximum limit of 5000")

        elif mapping.addon_category == "Audio Conferencing":
            # Validate audio conferencing limits
            if quantity > 2000:  # Example limit
                errors.append(
                    "Audio conferencing quantity exceeds maximum limit of 2000"
                )

        return len(errors) == 0, errors

    async def validate_bulk_addons(
        self,
        addons: List[Dict[str, Any]],
        base_sku_id: str,
        tenant_id: Optional[str] = None,
        domain_name: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate multiple add-ons in bulk

        Args:
            addons: List of dicts with 'sku_id' and 'quantity' keys
            base_sku_id: Base SKU ID for all add-ons
            tenant_id: Microsoft tenant ID (optional)
            domain_name: Domain name for validation (optional)

        Returns:
            Tuple of (all_valid, dict_of_sku_to_errors)
        """
        all_errors = {}
        all_valid = True

        for addon in addons:
            addon_sku_id = addon.get("sku_id")
            quantity = addon.get("quantity", 1)

            if not addon_sku_id:
                continue

            is_valid, errors = await self.validate_addon_compatibility(
                addon_sku_id, base_sku_id, quantity, tenant_id, domain_name
            )

            if not is_valid:
                all_valid = False
                all_errors[addon_sku_id] = errors

        return all_valid, all_errors

    async def get_validation_requirements(
        self, addon_sku_id: str, base_sku_id: str
    ) -> Dict[str, Any]:
        """
        Get validation requirements for an add-on

        Returns:
            Dict with validation requirements
        """
        mapping = await self.addon_repo.get_specific_mapping(addon_sku_id, base_sku_id)

        if not mapping:
            return {
                "requires_validation": False,
                "reason": "No compatibility mapping found",
            }

        requirements: Dict[str, Any] = {
            "requires_validation": True,
            "min_quantity": mapping.min_quantity,
            "max_quantity": mapping.max_quantity,
            "quantity_multiplier": mapping.quantity_multiplier,
            "requires_tenant_validation": mapping.requires_tenant_validation,
            "requires_domain_validation": mapping.requires_domain_validation,
            "service_type": mapping.service_type,
            "addon_category": mapping.addon_category,
            "is_active": mapping.is_active,
            "is_available": mapping.is_available(),
        }

        # Add specific validation rules
        validation_rules = []

        if mapping.requires_tenant_validation:
            validation_rules.append("Microsoft tenant ID required")

        if mapping.requires_domain_validation:
            validation_rules.append("Domain name required")

        if mapping.min_quantity > 1:
            validation_rules.append(f"Minimum quantity: {mapping.min_quantity}")

        if mapping.max_quantity is not None:
            validation_rules.append(f"Maximum quantity: {mapping.max_quantity}")

        if mapping.quantity_multiplier > 1:
            validation_rules.append(
                f"Quantity must be multiple of {mapping.quantity_multiplier}"
            )

        requirements["validation_rules"] = validation_rules

        return requirements

    async def get_sku_validation_summary(self, sku_id: str) -> Dict[str, Any]:
        """Get validation summary for all add-ons compatible with a SKU"""
        # Get all compatible add-ons
        compatible_addons = await self.addon_repo.get_compatible_addons(sku_id)

        summary: Dict[str, Any] = {
            "total_compatible_addons": len(compatible_addons),
            "active_mappings": sum(1 for addon in compatible_addons if addon.is_active),
            "validation_requirements": {},
            "service_types": set(),
            "addon_categories": set(),
        }

        for addon in compatible_addons:
            requirements = await self.get_validation_requirements(
                addon.addon_sku_id, sku_id
            )

            summary["validation_requirements"][addon.addon_sku_id] = requirements
            summary["service_types"].add(addon.service_type)
            summary["addon_categories"].add(addon.addon_category)

        # Convert sets to lists for JSON serialization
        summary["service_types"] = list(summary["service_types"])  # type: ignore
        summary["addon_categories"] = list(summary["addon_categories"])  # type: ignore

        return summary
