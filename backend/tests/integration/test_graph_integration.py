from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.integrations.graph import GraphAuthService, GraphClient
from src.integrations.graph.exceptions import GraphAuthError


class TestGraphAuthService:
    """Tests pour le service d'authentification Graph"""

    @pytest.mark.asyncio
    async def test_get_token_success(self):
        """Test de récupération réussie d'un token"""

        # Créer un mock pour la réponse
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"access_token": "test_token_123", "expires_in": 3600}
        )

        # Créer un mock pour la session
        mock_session = MagicMock()
        mock_post = MagicMock()

        # Context manager
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_post)
        mock_session.closed = False

        # Patcher ClientSession
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # GraphAuthService() ne prend AUCUN paramètre
            service = GraphAuthService()

            # Les paramètres sont passés à get_token()
            token = await service.get_token(
                tenant_id="test-tenant-id",
                client_id="test-client-id",
                client_secret="test-secret",
            )

            assert token == "test_token_123"

            # Vérifier que post a été appelé
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args
            # Vérifier que l'URL contient le tenant_id
            assert "test-tenant-id" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_token_cached(self):
        """Test du cache de token"""
        service = GraphAuthService()

        # CORRECTION : Utiliser datetime avec timezone.utc (pas utcnow())
        service._token_cache["test-tenant-id:test-client-id"] = {
            "access_token": "cached_token",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        # Mock la session (même si elle ne sera pas utilisée grâce au cache)
        mock_session = MagicMock()
        mock_session.closed = False

        with patch("aiohttp.ClientSession", return_value=mock_session):
            token = await service.get_token(
                tenant_id="test-tenant-id",
                client_id="test-client-id",
                client_secret="test-secret",
            )

            assert token == "cached_token"
            # Vérifier que post n'a PAS été appelé (token en cache)
            mock_session.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_token_auth_error(self):
        """Test d'erreur d'authentification"""

        # Mock pour erreur 401
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(
            return_value={
                "error": "invalid_client",
                "error_description": "Invalid client secret provided",
            }
        )

        mock_session = MagicMock()
        mock_session.closed = False
        mock_post = MagicMock()

        # Context manager
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_post)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # GraphAuthService() ne prend AUCUN paramètre
            service = GraphAuthService()

            # Vérifier qu'une exception GraphAuthError est levée
            with pytest.raises(GraphAuthError) as exc_info:
                await service.get_token(
                    tenant_id="test-tenant-id",
                    client_id="test-client-id",
                    client_secret="wrong-secret",
                )

            # Vérifier le message d'erreur
            assert "Invalid client secret" in str(exc_info.value)


class TestGraphClient:
    """Tests pour le client Graph API"""

    @pytest.mark.asyncio
    async def test_get_users_success(self):
        """Test de récupération des utilisateurs"""

        # Mock de la réponse
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.json = AsyncMock(
            return_value={
                "value": [
                    {
                        "id": "user1",
                        "userPrincipalName": "user1@test.com",
                        "displayName": "User One",
                        "accountEnabled": True,
                        "assignedLicenses": [],
                    }
                ]
            }
        )

        # Mock de la session
        mock_session = MagicMock()
        mock_session.closed = False
        mock_request = MagicMock()

        # Context manager pour request
        mock_request.__aenter__ = AsyncMock(return_value=mock_response)
        mock_request.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_request)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # GraphClient prend un access_token en paramètre
            client = GraphClient(access_token="test_token_123")

            users = await client.get_users()

            assert len(users) == 1
            assert users[0]["id"] == "user1"
            assert users[0]["userPrincipalName"] == "user1@test.com"
            assert users[0]["displayName"] == "User One"

    @pytest.mark.asyncio
    async def test_get_paginated_multiple_pages(self):
        """Test de pagination sur plusieurs pages"""

        # Première page avec nextLink
        mock_response1 = AsyncMock()
        mock_response1.status = 200
        mock_response1.content_type = "application/json"
        mock_response1.json = AsyncMock(
            return_value={
                "value": [{"id": "user1", "displayName": "User 1"}],
                "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?$skip=1",
            }
        )

        # Deuxième page sans nextLink (dernière page)
        mock_response2 = AsyncMock()
        mock_response2.status = 200
        mock_response2.content_type = "application/json"
        mock_response2.json = AsyncMock(
            return_value={
                "value": [{"id": "user2", "displayName": "User 2"}]
                # Pas de @odata.nextLink = dernière page
            }
        )

        # Mock de la session avec plusieurs appels
        mock_session = MagicMock()
        mock_session.closed = False

        # Premier appel
        mock_request1 = MagicMock()
        mock_request1.__aenter__ = AsyncMock(return_value=mock_response1)
        mock_request1.__aexit__ = AsyncMock(return_value=None)

        # Deuxième appel
        mock_request2 = MagicMock()
        mock_request2.__aenter__ = AsyncMock(return_value=mock_response2)
        mock_request2.__aexit__ = AsyncMock(return_value=None)

        # La méthode request retourne alternativement les deux mocks
        mock_session.request = MagicMock(side_effect=[mock_request1, mock_request2])

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # GraphClient prend un access_token
            client = GraphClient(access_token="test_token_123")

            items = await client.get_paginated("/users")

            assert len(items) == 2
            assert items[0]["id"] == "user1"
            assert items[1]["id"] == "user2"

            # Vérifier que request a été appelé 2 fois (2 pages)
            assert mock_session.request.call_count == 2

    @pytest.mark.asyncio
    async def test_throttling_retry(self):
        """Test du retry en cas de throttling (429)"""

        # Première réponse : 429 (throttled)
        mock_response_throttled = AsyncMock()
        mock_response_throttled.status = 429
        mock_response_throttled.headers = {"Retry-After": "1"}
        mock_response_throttled.content_type = "application/json"

        # Deuxième réponse : 200 (succès après retry)
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.content_type = "application/json"
        mock_response_success.json = AsyncMock(
            return_value={"value": [{"id": "user1", "displayName": "User 1"}]}
        )

        mock_session = MagicMock()
        mock_session.closed = False

        # Premier appel (throttled)
        mock_request1 = MagicMock()
        mock_request1.__aenter__ = AsyncMock(return_value=mock_response_throttled)
        mock_request1.__aexit__ = AsyncMock(return_value=None)

        # Deuxième appel (succès)
        mock_request2 = MagicMock()
        mock_request2.__aenter__ = AsyncMock(return_value=mock_response_success)
        mock_request2.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(side_effect=[mock_request1, mock_request2])

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Mock asyncio.sleep pour ne pas attendre réellement
            with patch("asyncio.sleep", new_callable=AsyncMock) as _mock_sleep:
                # GraphClient prend un access_token
                client = GraphClient(access_token="test_token_123")

                items = await client.get_paginated("/users")

                assert len(items) == 1
                assert items[0]["id"] == "user1"

                # Vérifier que request a été appelé 2 fois (1 échec + 1 retry)
                assert mock_session.request.call_count == 2

                # Note: Le sleep est géré par tenacity, pas directement appelé
                # donc on ne peut pas facilement le vérifier ici

    @pytest.mark.asyncio
    async def test_get_organization_success(self):
        """Test de récupération des infos d'organisation"""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.json = AsyncMock(
            return_value={
                "value": [
                    {
                        "id": "tenant-id-123",
                        "displayName": "Test Organization",
                        "verifiedDomains": [{"name": "test.com", "isDefault": True}],
                    }
                ]
            }
        )

        mock_session = MagicMock()
        mock_session.closed = False
        mock_request = MagicMock()

        mock_request.__aenter__ = AsyncMock(return_value=mock_response)
        mock_request.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_request)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            client = GraphClient(access_token="test_token_123")

            org = await client.get_organization()

            assert org["id"] == "tenant-id-123"
            assert org["displayName"] == "Test Organization"

    @pytest.mark.asyncio
    async def test_get_subscribed_skus_success(self):
        """Test de récupération des SKUs"""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.json = AsyncMock(
            return_value={
                "value": [
                    {
                        "id": "sku-123",
                        "skuPartNumber": "ENTERPRISEPACK",
                        "consumedUnits": 10,
                        "prepaidUnits": {"enabled": 25},
                    }
                ]
            }
        )

        mock_session = MagicMock()
        mock_session.closed = False
        mock_request = MagicMock()

        mock_request.__aenter__ = AsyncMock(return_value=mock_response)
        mock_request.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_request)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            client = GraphClient(access_token="test_token_123")

            skus = await client.get_subscribed_skus()

            assert len(skus) == 1
            assert skus[0]["skuPartNumber"] == "ENTERPRISEPACK"
            assert skus[0]["consumedUnits"] == 10
