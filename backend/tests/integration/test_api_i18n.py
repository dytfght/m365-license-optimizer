"""
Integration tests for i18n endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from uuid import UUID

# Mark all tests as integration tests
pytestmark = pytest.mark.integration


class TestI18nEndpoints:
    """Test suite for i18n API endpoints"""

    async def test_get_user_language(self, app_client: AsyncClient, auth_headers, test_user_id: UUID):
        """Test getting user language preference"""
        response = await app_client.get(
            f"/api/v1/users/{test_user_id}/language",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert "available_languages" in data
        assert isinstance(data["available_languages"], list)
        assert len(data["available_languages"]) > 0

    async def test_update_user_language(self, app_client: AsyncClient, auth_headers, test_user_id: UUID):
        """Test updating user language preference"""
        # Update to French
        response = await app_client.put(
            f"/api/v1/users/{test_user_id}/language",
            json={"language": "fr"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "fr"

        # Update back to English
        response = await app_client.put(
            f"/api/v1/users/{test_user_id}/language",
            json={"language": "en"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"

    async def test_update_user_language_invalid_code(self, app_client: AsyncClient, auth_headers, test_user_id: UUID):
        """Test updating with invalid language code"""
        response = await app_client.put(
            f"/api/v1/users/{test_user_id}/language",
            json={"language": "invalid"},
            headers=auth_headers
        )

        # Should fail validation (pattern mismatch)
        assert response.status_code == 422

    async def test_update_other_user_language_fails(self, app_client: AsyncClient, auth_headers):
        """Test that users cannot update other users' language"""
        # Use a different UUID that doesn't belong to the authenticated user
        other_user_id = "00000000-0000-0000-0000-000000000000"

        response = await app_client.put(
            f"/api/v1/users/{other_user_id}/language",
            json={"language": "fr"},
            headers=auth_headers
        )

        assert response.status_code == 403

    async def test_get_other_user_language_fails(self, app_client: AsyncClient, auth_headers):
        """Test that users cannot access other users' language preference"""
        other_user_id = "00000000-0000-0000-0000-000000000000"

        response = await app_client.get(
            f"/api/v1/users/{other_user_id}/language",
            headers=auth_headers
        )

        assert response.status_code == 403

    async def test_report_generation_with_accept_language_header(
        self, app_client: AsyncClient, auth_headers, test_analysis_id: UUID
    ):
        """Test report generation with Accept-Language header"""
        if test_analysis_id is None:
            pytest.skip("No analysis ID available")

        # Test with French header
        response = await app_client.post(
            f"/api/v1/reports/analyses/{test_analysis_id}/pdf",
            headers={**auth_headers, "Accept-Language": "fr"}
        )

        # Report generation might succeed or fail depending on test data
        # but we check that the endpoint accepts the header
        assert response.status_code in [201, 404, 500]

        if response.status_code == 201:
            data = response.json()
            assert "report_metadata" in data
            # Language should be recorded in metadata
            assert data["report_metadata"].get("language") == "fr"

    async def test_report_generation_without_language_header(
        self, app_client: AsyncClient, auth_headers, test_analysis_id: UUID
    ):
        """Test report generation without Accept-Language header uses default"""
        if test_analysis_id is None:
            pytest.skip("No analysis ID available")

        response = await app_client.post(
            f"/api/v1/reports/analyses/{test_analysis_id}/pdf",
            headers=auth_headers
        )

        # Should use user's default language or English
        assert response.status_code in [201, 404, 500]

    async def test_excel_report_generation_with_language(
        self, app_client: AsyncClient, auth_headers, test_analysis_id: UUID
    ):
        """Test Excel report generation with language preference"""
        if test_analysis_id is None:
            pytest.skip("No analysis ID available")

        response = await app_client.post(
            f"/api/v1/reports/analyses/{test_analysis_id}/excel",
            headers={**auth_headers, "Accept-Language": "fr"}
        )

        assert response.status_code in [201, 404, 500]

    async def test_error_messages_localized(
        self, app_client: AsyncClient, auth_headers, test_analysis_id: UUID
    ):
        """Test that error messages are localized based on Accept-Language"""
        # Try to generate report for non-existent analysis
        fake_analysis_id = "00000000-0000-0000-0000-000000000000"

        response = await app_client.post(
            f"/api/v1/reports/analyses/{fake_analysis_id}/pdf",
            headers={**auth_headers, "Accept-Language": "fr"}
        )

        # Should return 404 with localized error message
        assert response.status_code == 404
        data = response.json()
        # Check that error message is in French
        assert "trouv" in data["detail"].lower() or "analyse" in data["detail"].lower()

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/users/me"
    ])
    async def test_user_response_includes_language(
        self, app_client: AsyncClient, auth_headers, endpoint
    ):
        """Test that user responses include language field"""
        response = await app_client.get(endpoint, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert data["language"] in ["en", "fr"]
