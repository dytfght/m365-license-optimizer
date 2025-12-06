"""
Unit tests for LoggingService (LOT 10)
Tests log storage, retrieval, and purging.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.logging_service import LoggingService


class TestLoggingService:
    """Tests for LoggingService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a LoggingService instance."""
        return LoggingService(mock_db)

    # ============================================
    # Log Storage Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_log_to_db_success(self, service, mock_db):
        """Test successful log storage."""
        result = await service.log_to_db(
            level="info",
            message="Test log message",
            endpoint="/api/test",
            method="GET",
            request_id="req-123",
            response_status=200,
            duration_ms=50,
        )

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_to_db_with_user_context(self, service, mock_db):
        """Test log storage with user context."""
        user_id = uuid4()
        tenant_id = uuid4()

        result = await service.log_to_db(
            level="warning",
            message="User action logged",
            user_id=user_id,
            tenant_id=tenant_id,
            action="sync",
        )

        assert result is not None
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_to_db_with_extra_data(self, service, mock_db):
        """Test log storage with extra JSON data."""
        result = await service.log_to_db(
            level="error",
            message="Error occurred",
            extra_data={"error_code": "E001", "details": "Something went wrong"},
        )

        assert result is not None
        mock_db.add.assert_called_once()

    # ============================================
    # Log Retrieval Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_get_logs_no_filters(self, service, mock_db):
        """Test log retrieval without filters."""
        mock_logs = [MagicMock() for _ in range(5)]

        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 100

        # Mock data query
        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = mock_logs

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        logs, total = await service.get_logs()

        assert len(logs) == 5
        assert total == 100

    @pytest.mark.asyncio
    async def test_get_logs_with_level_filter(self, service, mock_db):
        """Test log retrieval with level filter."""
        mock_logs = [MagicMock()]

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = mock_logs

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        logs, total = await service.get_logs(level="error")

        assert len(logs) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_logs_with_date_range(self, service, mock_db):
        """Test log retrieval with date range filter."""
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        count_result = MagicMock()
        count_result.scalar.return_value = 50

        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        logs, total = await service.get_logs(
            start_date=start_date,
            end_date=end_date,
        )

        assert total == 50

    @pytest.mark.asyncio
    async def test_get_logs_pagination(self, service, mock_db):
        """Test log retrieval with pagination."""
        count_result = MagicMock()
        count_result.scalar.return_value = 200

        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = [MagicMock() for _ in range(20)]

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        logs, total = await service.get_logs(limit=20, offset=40)

        assert len(logs) == 20
        assert total == 200

    @pytest.mark.asyncio
    async def test_get_log_by_id_found(self, service, mock_db):
        """Test retrieving a specific log by ID."""
        log_id = uuid4()
        mock_log = MagicMock()
        mock_log.id = log_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result

        result = await service.get_log_by_id(log_id)

        assert result is not None
        assert result.id == log_id

    @pytest.mark.asyncio
    async def test_get_log_by_id_not_found(self, service, mock_db):
        """Test retrieving a non-existent log."""
        log_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_log_by_id(log_id)

        assert result is None

    # ============================================
    # Log Purging Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_purge_old_logs_default_retention(self, service, mock_db):
        """Test purging logs with default retention (90 days)."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1000

        mock_db.execute = AsyncMock(return_value=count_result)

        deleted = await service.purge_old_logs()

        assert deleted == 1000
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_old_logs_custom_retention(self, service, mock_db):
        """Test purging logs with custom retention period."""
        count_result = MagicMock()
        count_result.scalar.return_value = 500

        mock_db.execute = AsyncMock(return_value=count_result)

        deleted = await service.purge_old_logs(days=30)

        assert deleted == 500

    @pytest.mark.asyncio
    async def test_purge_old_logs_no_logs_to_delete(self, service, mock_db):
        """Test purging when no old logs exist."""
        count_result = MagicMock()
        count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(return_value=count_result)

        deleted = await service.purge_old_logs()

        assert deleted == 0
        mock_db.commit.assert_not_called()

    # ============================================
    # Statistics Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_get_log_statistics(self, service, mock_db):
        """Test log statistics retrieval."""
        # Mock different query results
        def create_mock_result(value):
            result = MagicMock()
            result.scalar.return_value = value
            return result

        results = [
            create_mock_result(1000),  # Total
            create_mock_result(100),   # Debug
            create_mock_result(500),   # Info
            create_mock_result(200),   # Warning
            create_mock_result(150),   # Error
            create_mock_result(50),    # Critical
        ]

        mock_db.execute = AsyncMock(side_effect=results)

        stats = await service.get_log_statistics(days=7)

        assert stats["period_days"] == 7
        assert stats["total_logs"] == 1000
        assert stats["by_level"]["debug"] == 100
        assert stats["by_level"]["info"] == 500
        assert stats["error_count"] == 200  # error + critical
        assert stats["error_rate_percent"] == 20.0  # 200/1000 * 100

    @pytest.mark.asyncio
    async def test_get_log_statistics_with_tenant_filter(self, service, mock_db):
        """Test log statistics with tenant filter."""
        tenant_id = uuid4()

        results = [MagicMock() for _ in range(6)]
        for r in results:
            r.scalar.return_value = 10

        mock_db.execute = AsyncMock(side_effect=results)

        stats = await service.get_log_statistics(tenant_id=tenant_id, days=30)

        assert stats["period_days"] == 30
