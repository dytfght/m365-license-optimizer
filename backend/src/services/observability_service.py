"""
Observability Service for LOT 11: System Metrics Collection
Provides system metrics using psutil for monitoring and observability.
"""
import os
import platform
import time
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)

# psutil will be imported conditionally to handle environments without it
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, system metrics will be limited")


class ObservabilityService:
    """
    Service for collecting system metrics and observability data.
    Uses psutil for cross-platform system information.
    """

    def __init__(self) -> None:
        """Initialize observability service."""
        self._start_time = time.time()

    @property
    def uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self._start_time

    def get_cpu_metrics(self) -> dict[str, Any]:
        """
        Get CPU usage metrics.

        Returns:
            Dictionary with CPU usage information
        """
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available", "percent": 0}

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()

            return {
                "percent": cpu_percent,
                "count_physical": cpu_count,
                "count_logical": cpu_count_logical,
                "frequency_mhz": cpu_freq.current if cpu_freq else None,
                "frequency_max_mhz": cpu_freq.max if cpu_freq else None,
            }
        except Exception as e:
            logger.error("cpu_metrics_error", error=str(e))
            return {"error": str(e), "percent": 0}

    def get_memory_metrics(self) -> dict[str, Any]:
        """
        Get memory usage metrics.

        Returns:
            Dictionary with memory usage information
        """
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            mem = psutil.virtual_memory()
            return {
                "total_bytes": mem.total,
                "available_bytes": mem.available,
                "used_bytes": mem.used,
                "percent": mem.percent,
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
            }
        except Exception as e:
            logger.error("memory_metrics_error", error=str(e))
            return {"error": str(e)}

    def get_disk_metrics(self, path: str = "/") -> dict[str, Any]:
        """
        Get disk usage metrics.

        Args:
            path: Path to check disk usage for

        Returns:
            Dictionary with disk usage information
        """
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            # On Windows, use C: as default
            if platform.system() == "Windows" and path == "/":
                path = "C:\\"

            disk = psutil.disk_usage(path)
            return {
                "path": path,
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
                "percent": disk.percent,
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
            }
        except Exception as e:
            logger.error("disk_metrics_error", error=str(e))
            return {"error": str(e), "path": path}

    def get_network_metrics(self) -> dict[str, Any]:
        """
        Get network I/O statistics.

        Returns:
            Dictionary with network I/O information
        """
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
            }
        except Exception as e:
            logger.error("network_metrics_error", error=str(e))
            return {"error": str(e)}

    def get_process_metrics(self) -> dict[str, Any]:
        """
        Get current process metrics.

        Returns:
            Dictionary with process information
        """
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            proc = psutil.Process(os.getpid())
            mem_info = proc.memory_info()
            return {
                "pid": proc.pid,
                "memory_rss_bytes": mem_info.rss,
                "memory_rss_mb": round(mem_info.rss / (1024**2), 2),
                "memory_vms_bytes": mem_info.vms,
                "memory_vms_mb": round(mem_info.vms / (1024**2), 2),
                "cpu_percent": proc.cpu_percent(),
                "num_threads": proc.num_threads(),
                "create_time": datetime.fromtimestamp(
                    proc.create_time(), tz=timezone.utc
                ).isoformat(),
            }
        except Exception as e:
            logger.error("process_metrics_error", error=str(e))
            return {"error": str(e)}

    def get_system_info(self) -> dict[str, Any]:
        """
        Get system information.

        Returns:
            Dictionary with system info
        """
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "psutil_available": PSUTIL_AVAILABLE,
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get all system metrics in a single call.

        Returns:
            Dictionary with all system metrics
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(self.uptime_seconds, 2),
            "system": self.get_system_info(),
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics(),
            "process": self.get_process_metrics(),
        }


# Singleton instance for the application
_observability_service: Optional[ObservabilityService] = None


def get_observability_service() -> ObservabilityService:
    """
    Get or create the observability service singleton.

    Returns:
        ObservabilityService instance
    """
    global _observability_service
    if _observability_service is None:
        _observability_service = ObservabilityService()
    return _observability_service
