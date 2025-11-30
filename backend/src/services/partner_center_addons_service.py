"""
Partner Center Add-ons Service
Handles integration with Microsoft Partner Center for add-on management
"""
from typing import Dict, List, Optional, Tuple

import aiohttp
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.addon_compatibility import AddonCompatibility
from ..models.microsoft_product import MicrosoftProduct
from ..repositories.addon_compatibility_repository import AddonCompatibilityRepository
from ..repositories.product_repository import ProductRepository
from ..schemas.sku_mapping import AddonRecommendationResponse

logger = structlog.get_logger(__name__)


class PartnerCenterAddonsService:
    """Service for managing Partner Center add-ons integration"""

    def __init__(self, session: AsyncSession, access_token: Optional[str] = None):
        self.session = session
        self.product_repo = ProductRepository(session)
        self.addon_repo = AddonCompatibilityRepository(session)
        self.access_token = access_token
        self.base_url = "https://api.partnercenter.microsoft.com/v1"

    async def set_access_token(self, token: str) -> None:
        """Set Partner Center access token"""
        self.access_token = token

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[Dict]:
        """Make authenticated request to Partner Center API"""
        if not self.access_token:
            logger.error("no_access_token_provided")
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(
                            "partner_center_resource_not_found", endpoint=endpoint
                        )
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(
                            "partner_center_request_failed",
                            status=response.status,
                            error=error_text,
                            endpoint=endpoint,
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error(
                "partner_center_request_error", error=str(e), endpoint=endpoint
            )
            return None
        except Exception as e:
            logger.error(
                "partner_center_request_exception", error=str(e), endpoint=endpoint
            )
            return None

    async def fetch_partner_center_products(
        self, country: str = "US", currency: str = "USD"
    ) -> List[Dict]:
        """Fetch products from Partner Center"""
        # For now, return mock data
        # In a real implementation, this would call:
        # GET /products?country={country}&currency={currency}

        mock_products = [
            {
                "id": "CFQ7TTC0LF8S",
                "title": "Microsoft 365 Business Premium",
                "productType": {
                    "id": "OnlineServices",
                    "displayName": "Online Services",
                },
                "skus": [
                    {
                        "id": "0001",
                        "title": "Microsoft 365 Business Premium",
                        "description": "Complete productivity and collaboration solution for small businesses",
                        "minimumQuantity": 1,
                        "maximumQuantity": 300,
                        "isAddon": False,
                    }
                ],
            },
            {
                "id": "CFQ7TTC0LH0B",
                "title": "Microsoft 365 E3",
                "productType": {
                    "id": "OnlineServices",
                    "displayName": "Online Services",
                },
                "skus": [
                    {
                        "id": "0001",
                        "title": "Microsoft 365 E3",
                        "description": "Enterprise productivity suite with advanced security",
                        "minimumQuantity": 1,
                        "maximumQuantity": None,
                        "isAddon": False,
                    }
                ],
            },
            {
                "id": "CFQ7TTC0LH0C",
                "title": "Microsoft 365 E5",
                "productType": {
                    "id": "OnlineServices",
                    "displayName": "Online Services",
                },
                "skus": [
                    {
                        "id": "0001",
                        "title": "Microsoft 365 E5",
                        "description": "Most comprehensive Microsoft 365 plan with advanced analytics",
                        "minimumQuantity": 1,
                        "maximumQuantity": None,
                        "isAddon": False,
                    }
                ],
            },
            {
                "id": "CFQ7TTC0P0HP",
                "title": "Microsoft 365 Audio Conferencing",
                "productType": {
                    "id": "OnlineServices",
                    "displayName": "Online Services",
                },
                "skus": [
                    {
                        "id": "0001",
                        "title": "Microsoft 365 Audio Conferencing",
                        "description": "Enable PSTN conferencing for Microsoft Teams",
                        "minimumQuantity": 1,
                        "maximumQuantity": None,
                        "isAddon": True,
                        "addonType": "Audio Conferencing",
                    }
                ],
            },
            {
                "id": "CFQ7TTC0P0HQ",
                "title": "Microsoft 365 Phone System",
                "productType": {
                    "id": "OnlineServices",
                    "displayName": "Online Services",
                },
                "skus": [
                    {
                        "id": "0001",
                        "title": "Microsoft 365 Phone System",
                        "description": "Cloud-based phone system for Microsoft Teams",
                        "minimumQuantity": 1,
                        "maximumQuantity": None,
                        "isAddon": True,
                        "addonType": "Phone System",
                    }
                ],
            },
            {
                "id": "CFQ7TTC0P0HR",
                "title": "Microsoft 365 Domestic Calling Plan",
                "productType": {
                    "id": "OnlineServices",
                    "displayName": "Online Services",
                },
                "skus": [
                    {
                        "id": "0001",
                        "title": "Microsoft 365 Domestic Calling Plan",
                        "description": "Domestic calling minutes for Microsoft Teams",
                        "minimumQuantity": 1,
                        "maximumQuantity": None,
                        "isAddon": True,
                        "addonType": "Calling Plan",
                    }
                ],
            },
        ]

        return mock_products

    async def fetch_addon_compatibility_rules(
        self, addon_product_id: str, addon_sku_id: str
    ) -> List[Dict]:
        """Fetch compatibility rules for a specific add-on from Partner Center"""
        # Mock compatibility rules
        # In a real implementation, this would call:
        # GET /products/{addon_product_id}/skus/{addon_sku_id}/compatibility

        compatibility_rules = {
            ("CFQ7TTC0P0HP", "0001"): [  # Audio Conferencing
                {
                    "baseProductId": "CFQ7TTC0LF8S",
                    "baseSkuId": "0001",
                    "serviceType": "Microsoft 365",
                    "addonCategory": "Audio Conferencing",
                    "minQuantity": 1,
                    "maxQuantity": None,
                    "quantityMultiplier": 1,
                    "requiresDomainValidation": False,
                    "requiresTenantValidation": False,
                },
                {
                    "baseProductId": "CFQ7TTC0LH0B",
                    "baseSkuId": "0001",
                    "serviceType": "Microsoft 365",
                    "addonCategory": "Audio Conferencing",
                    "minQuantity": 1,
                    "maxQuantity": None,
                    "quantityMultiplier": 1,
                    "requiresDomainValidation": False,
                    "requiresTenantValidation": False,
                },
                {
                    "baseProductId": "CFQ7TTC0LH0C",
                    "baseSkuId": "0001",
                    "serviceType": "Microsoft 365",
                    "addonCategory": "Audio Conferencing",
                    "minQuantity": 1,
                    "maxQuantity": None,
                    "quantityMultiplier": 1,
                    "requiresDomainValidation": False,
                    "requiresTenantValidation": False,
                },
            ],
            ("CFQ7TTC0P0HQ", "0001"): [  # Phone System
                {
                    "baseProductId": "CFQ7TTC0LH0B",
                    "baseSkuId": "0001",
                    "serviceType": "Microsoft 365",
                    "addonCategory": "Phone System",
                    "minQuantity": 1,
                    "maxQuantity": None,
                    "quantityMultiplier": 1,
                    "requiresDomainValidation": True,
                    "requiresTenantValidation": True,
                },
                {
                    "baseProductId": "CFQ7TTC0LH0C",
                    "baseSkuId": "0001",
                    "serviceType": "Microsoft 365",
                    "addonCategory": "Phone System",
                    "minQuantity": 1,
                    "maxQuantity": None,
                    "quantityMultiplier": 1,
                    "requiresDomainValidation": True,
                    "requiresTenantValidation": True,
                },
            ],
            ("CFQ7TTC0P0HR", "0001"): [  # Domestic Calling Plan
                {
                    "baseProductId": "CFQ7TTC0P0HQ",
                    "baseSkuId": "0001",
                    "serviceType": "Microsoft 365",
                    "addonCategory": "Calling Plan",
                    "minQuantity": 1,
                    "maxQuantity": None,
                    "quantityMultiplier": 1,
                    "requiresDomainValidation": False,
                    "requiresTenantValidation": False,
                }
            ],
        }

        key = (addon_product_id, addon_sku_id)
        return compatibility_rules.get(key, [])

    async def sync_partner_center_products(self) -> Tuple[int, int]:
        """Sync products from Partner Center to local database"""
        products = await self.fetch_partner_center_products()

        created_count = 0
        updated_count = 0

        for product in products:
            for sku in product.get("skus", []):
                # Check if product already exists
                existing_product = await self.product_repo.get_by_product_sku(
                    product["id"], sku["id"]
                )

                product_data = {
                    "product_id": product["id"],
                    "sku_id": sku["id"],
                    "product_title": product["title"],
                    "sku_title": sku["title"],
                    "sku_description": sku.get("description"),
                    "publisher": "Microsoft Corporation",
                }

                if existing_product:
                    # Update existing product
                    await self.product_repo.update(existing_product, **product_data)
                    updated_count += 1
                else:
                    # Create new product
                    await self.product_repo.create(**product_data)
                    created_count += 1

        logger.info(
            "partner_center_products_synced",
            created=created_count,
            updated=updated_count,
            total=len(products),
        )

        return created_count, updated_count

    async def sync_addon_compatibility_rules(self) -> Tuple[int, int]:
        """Sync add-on compatibility rules from Partner Center"""
        products = await self.fetch_partner_center_products()

        created_count = 0
        updated_count = 0

        for product in products:
            for sku in product.get("skus", []):
                if sku.get("isAddon"):
                    # Fetch compatibility rules for this add-on
                    rules = await self.fetch_addon_compatibility_rules(
                        product["id"], sku["id"]
                    )

                    for rule in rules:
                        # Check if compatibility mapping already exists
                        existing_mapping = await self.addon_repo.get_specific_mapping(
                            sku["id"], rule["baseSkuId"]
                        )

                        mapping_data = {
                            "addon_sku_id": sku["id"],
                            "addon_product_id": product["id"],
                            "base_sku_id": rule["baseSkuId"],
                            "base_product_id": rule["baseProductId"],
                            "service_type": rule["serviceType"],
                            "addon_category": rule["addonCategory"],
                            "min_quantity": rule["minQuantity"],
                            "max_quantity": rule.get("maxQuantity") or None,
                            "quantity_multiplier": rule["quantityMultiplier"],
                            "requires_domain_validation": rule[
                                "requiresDomainValidation"
                            ],
                            "requires_tenant_validation": rule[
                                "requiresTenantValidation"
                            ],
                            "description": f"{sku['title']} compatibility with {rule['serviceType']}",
                            "is_active": True,
                        }

                        if existing_mapping:
                            # Update existing mapping
                            await self.addon_repo.update(
                                existing_mapping, **mapping_data
                            )
                            updated_count += 1
                        else:
                            # Create new mapping
                            await self.addon_repo.create(**mapping_data)
                            created_count += 1

        logger.info(
            "addon_compatibility_rules_synced",
            created=created_count,
            updated=updated_count,
        )

        return created_count, updated_count

    async def get_addon_recommendations(
        self, base_sku_id: str, current_addons: List[str], tenant_size: str = "medium"
    ) -> List[Dict]:
        """Get add-on recommendations based on base SKU and current usage"""
        # Get compatible add-ons
        compatible_addons = await self.addon_repo.get_compatible_addons(base_sku_id)

        recommendations = []

        for addon in compatible_addons:
            # Skip if already has this add-on
            if addon.addon_sku_id in current_addons:
                continue

            # Get product information
            product = await self.product_repo.get_by_product_sku(
                addon.addon_product_id, addon.addon_sku_id
            )

            if not product:
                continue

            # Calculate recommendation score based on various factors
            score = await self._calculate_recommendation_score(
                addon, product, tenant_size
            )

            if score > 0.5:  # Only recommend if score is significant
                recommendations.append(
                    AddonRecommendationResponse(
                        addon_sku_id=addon.addon_sku_id,
                        addon_name=product.sku_title,
                        addon_category=addon.addon_category,
                        service_type=addon.service_type,
                        compatibility_score=score,
                        min_quantity=addon.min_quantity,
                        max_quantity=addon.max_quantity,
                        reason=self._get_recommendation_reason(
                            addon.addon_category, tenant_size
                        ),
                    )
                )

        # Sort by score descending
        recommendations.sort(key=lambda x: x.compatibility_score, reverse=True)

        return [rec.model_dump(exclude_none=True) for rec in recommendations[:5]]  # Return top 5 recommendations as dicts

    async def _calculate_recommendation_score(
        self, addon: AddonCompatibility, product: MicrosoftProduct, tenant_size: str
    ) -> float:
        """Calculate recommendation score for an add-on"""
        score = 0.5  # Base score

        # Adjust based on tenant size
        size_multipliers = {
            "small": 0.8,
            "medium": 1.0,
            "large": 1.2,
            "enterprise": 1.5,
        }

        multiplier = size_multipliers.get(tenant_size, 1.0)
        score *= multiplier

        # Adjust based on add-on category
        category_scores = {
            "Audio Conferencing": 0.9,
            "Phone System": 0.8,
            "Calling Plan": 0.7,
            "Storage": 0.6,
            "Advanced Analytics": 0.5,
        }

        category_score = category_scores.get(addon.addon_category, 0.5)
        score = (score + category_score) / 2

        # Adjust based on validation requirements (lower score if validation required)
        if addon.requires_domain_validation or addon.requires_tenant_validation:
            score *= 0.9

        return min(score, 1.0)  # Cap at 1.0

    def _get_recommendation_reason(self, category: str, tenant_size: str) -> str:
        """Get human-readable recommendation reason"""
        reasons = {
            (
                "Audio Conferencing",
                "small",
            ): "Enhance meeting capabilities for remote team collaboration",
            (
                "Audio Conferencing",
                "medium",
            ): "Improve meeting experience with dial-in options",
            (
                "Audio Conferencing",
                "large",
            ): "Essential for large-scale meetings and webinars",
            (
                "Audio Conferencing",
                "enterprise",
            ): "Critical for enterprise-grade meeting infrastructure",
            (
                "Phone System",
                "small",
            ): "Add cloud phone capabilities for professional communications",
            (
                "Phone System",
                "medium",
            ): "Replace traditional phone system with cloud solution",
            (
                "Phone System",
                "large",
            ): "Scale communications with cloud-based phone system",
            (
                "Phone System",
                "enterprise",
            ): "Enterprise-grade telephony integration with Teams",
            (
                "Calling Plan",
                "small",
            ): "Add calling minutes for business communications",
            ("Calling Plan", "medium"): "Expand calling capabilities for growing team",
            ("Calling Plan", "large"): "Support high-volume calling needs",
            ("Calling Plan", "enterprise"): "Enterprise-scale calling infrastructure",
        }

        return reasons.get(
            (category, tenant_size), f"Enhance your {category.lower()} capabilities"
        )

    async def validate_addon_purchase(
        self,
        addon_sku_id: str,
        base_sku_id: str,
        quantity: int,
        tenant_id: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate if add-on purchase is allowed"""
        validation_errors = []

        # Check basic compatibility
        is_compatible = await self.addon_repo.validate_compatibility(
            addon_sku_id, base_sku_id, quantity
        )

        if not is_compatible:
            validation_errors.append(
                f"Add-on {addon_sku_id} is not compatible with base SKU {base_sku_id} at quantity {quantity}"
            )
            return False, validation_errors

        # Get compatibility mapping for additional validation
        mapping = await self.addon_repo.get_specific_mapping(addon_sku_id, base_sku_id)

        if not mapping:
            validation_errors.append(
                f"No compatibility mapping found for add-on {addon_sku_id} and base SKU {base_sku_id}"
            )
            return False, validation_errors

        # Domain validation
        if mapping.requires_domain_validation and not tenant_id:
            validation_errors.append(
                "Domain validation required but no tenant ID provided"
            )
            return False, validation_errors

        # Tenant validation
        if mapping.requires_tenant_validation and not tenant_id:
            validation_errors.append(
                "Tenant validation required but no tenant ID provided"
            )
            return False, validation_errors

        return len(validation_errors) == 0, validation_errors
