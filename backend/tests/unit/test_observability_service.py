"""
Unit tests for Observability Service (LOT 11)
Tests system metrics collection using psutil.
"""
import platform
from unittest.mock import MagicMock, patch

import pytest

from src.services.observability_service import (
    ObservabilityService,
    PSUTIL_AVAILABLE,
    get_observability_service,
)


class TestObservabilityService:
    """Test suite for ObservabilityService."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service = ObservabilityService()

    def test_initialization(self):
        """Test service initialization."""
        assert self.service is not None
        assert self.service._start_time > 0

    def test_uptime_seconds(self):
        """Test uptime calculation."""
        uptime = self.service.uptime_seconds
        assert uptime >= 0
        assert isinstance(uptime, float)

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_get_cpu_metrics(self):
        """Test CPU metrics collection."""
        metrics = self.service.get_cpu_metrics()
        
        assert "percent" in metrics
        assert isinstance(metrics["percent"], (int, float))
        assert 0 <= metrics["percent"] <= 100
        
        if "count_physical" in metrics and metrics["count_physical"]:
            assert metrics["count_physical"] >= 1
        
        if "count_logical" in metrics and metrics["count_logical"]:
            assert metrics["count_logical"] >= 1

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_get_memory_metrics(self):
        """Test memory metrics collection."""
        metrics = self.service.get_memory_metrics()
        
        assert "total_bytes" in metrics
        assert "available_bytes" in metrics
        assert "percent" in metrics
        
        if "error" not in metrics:
            assert metrics["total_bytes"] > 0
            assert metrics["available_bytes"] >= 0
            assert 0 <= metrics["percent"] <= 100

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_get_disk_metrics(self):
        """Test disk metrics collection."""
        # Use appropriate path for the OS
        path = "C:\\" if platform.system() == "Windows" else "/"
        metrics = self.service.get_disk_metrics(path)
        
        assert "path" in metrics
        
        if "error" not in metrics:
            assert metrics["total_bytes"] > 0
            assert metrics["free_bytes"] >= 0
            assert 0 <= metrics["percent"] <= 100

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_get_network_metrics(self):
        """Test network metrics collection."""
        metrics = self.service.get_network_metrics()
        
        if "error" not in metrics:
            assert "bytes_sent" in metrics
            assert "bytes_recv" in metrics
            assert metrics["bytes_sent"] >= 0
            assert metrics["bytes_recv"] >= 0

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_get_process_metrics(self):
        """Test process metrics collection."""
        metrics = self.service.get_process_metrics()
        
        if "error" not in metrics:
            assert "pid" in metrics
            assert metrics["pid"] > 0
            assert "memory_rss_bytes" in metrics
            assert "num_threads" in metrics

    def test_get_system_info(self):
        """Test system info collection."""
        info = self.service.get_system_info()
        
        assert "platform" in info
        assert "platform_release" in info
        assert "python_version" in info
        assert "psutil_available" in info
        
        assert info["platform"] in ["Windows", "Linux", "Darwin"]
        assert info["python_version"]  # Non-empty string

    def test_get_all_metrics(self):
        """Test comprehensive metrics collection."""
        metrics = self.service.get_all_metrics()
        
        assert "timestamp" in metrics
        assert "uptime_seconds" in metrics
        assert "system" in metrics
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "network" in metrics
        assert "process" in metrics
        
        # Verify timestamp is ISO format
        assert "T" in metrics["timestamp"]
        
        # Verify uptime is positive
        assert metrics["uptime_seconds"] >= 0

    def test_get_observability_service_singleton(self):
        """Test singleton pattern for observability service."""
        service1 = get_observability_service()
        service2 = get_observability_service()
        
        assert service1 is service2


class TestObservabilityServiceWithoutPsutil:
    """Test observability service behavior when psutil is not available."""

    @patch('src.services.observability_service.PSUTIL_AVAILABLE', False)
    def test_cpu_metrics_without_psutil(self):
        """Test CPU metrics returns error when psutil unavailable."""
        service = ObservabilityService()
        metrics = service.get_cpu_metrics()
        
        assert "error" in metrics
        assert metrics["percent"] == 0

    @patch('src.services.observability_service.PSUTIL_AVAILABLE', False)
    def test_memory_metrics_without_psutil(self):
        """Test memory metrics returns error when psutil unavailable."""
        service = ObservabilityService()
        metrics = service.get_memory_metrics()
        
        assert "error" in metrics

    @patch('src.services.observability_service.PSUTIL_AVAILABLE', False)
    def test_disk_metrics_without_psutil(self):
        """Test disk metrics returns error when psutil unavailable."""
        service = ObservabilityService()
        metrics = service.get_disk_metrics()
        
        assert "error" in metrics

    @patch('src.services.observability_service.PSUTIL_AVAILABLE', False)
    def test_network_metrics_without_psutil(self):
        """Test network metrics returns error when psutil unavailable."""
        service = ObservabilityService()
        metrics = service.get_network_metrics()
        
        assert "error" in metrics

    @patch('src.services.observability_service.PSUTIL_AVAILABLE', False)
    def test_process_metrics_without_psutil(self):
        """Test process metrics returns error when psutil unavailable."""
        service = ObservabilityService()
        metrics = service.get_process_metrics()
        
        assert "error" in metrics


class TestObservabilityServiceErrorHandling:
    """Test error handling in observability service."""

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_disk_metrics_invalid_path(self):
        """Test disk metrics with invalid path."""
        service = ObservabilityService()
        metrics = service.get_disk_metrics("/nonexistent/path/that/does/not/exist")
        
        # Should return error instead of raising exception
        assert "error" in metrics or "path" in metrics

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    @patch('psutil.cpu_percent')
    def test_cpu_metrics_exception_handling(self, mock_cpu):
        """Test CPU metrics handles exceptions gracefully."""
        mock_cpu.side_effect = Exception("Test error")
        
        service = ObservabilityService()
        metrics = service.get_cpu_metrics()
        
        assert "error" in metrics

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    @patch('psutil.virtual_memory')
    def test_memory_metrics_exception_handling(self, mock_mem):
        """Test memory metrics handles exceptions gracefully."""
        mock_mem.side_effect = Exception("Test error")
        
        service = ObservabilityService()
        metrics = service.get_memory_metrics()
        
        assert "error" in metrics
