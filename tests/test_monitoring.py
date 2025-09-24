"""
Tests for the monitoring and performance tracking system
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from cmp.utils.monitoring import (
    PerformanceMetrics,
    ContextualLogger,
    SystemHealthMonitor,
    performance_monitor,
    performance_metrics,
    system_health_monitor
)


class TestPerformanceMetrics:
    """Test performance metrics tracking"""
    
    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initializes correctly"""
        metrics = PerformanceMetrics(max_history=100)
        assert metrics.max_history == 100
        assert len(metrics.request_times) == 0
        assert len(metrics.error_counts) == 0
    
    def test_record_request(self):
        """Test recording request metrics"""
        metrics = PerformanceMetrics()
        
        # Record a successful request
        metrics.record_request("/test", 0.5, 200)
        
        assert len(metrics.request_times) == 1
        assert metrics.request_times[0]["endpoint"] == "/test"
        assert metrics.request_times[0]["duration"] == 0.5
        assert metrics.request_times[0]["status_code"] == 200
        
        # Check endpoint stats
        stats = metrics.endpoint_stats["/test"]
        assert stats["count"] == 1
        assert stats["total_time"] == 0.5
        assert stats["min_time"] == 0.5
        assert stats["max_time"] == 0.5
        assert stats["error_count"] == 0
    
    def test_record_error_request(self):
        """Test recording error request metrics"""
        metrics = PerformanceMetrics()
        
        # Record an error request
        metrics.record_request("/test", 1.0, 500)
        
        assert len(metrics.request_times) == 1
        assert metrics.error_counts[500] == 1
        
        # Check endpoint stats
        stats = metrics.endpoint_stats["/test"]
        assert stats["error_count"] == 1
    
    def test_get_stats(self):
        """Test getting performance statistics"""
        metrics = PerformanceMetrics()
        
        # Record multiple requests
        metrics.record_request("/test1", 0.1, 200)
        metrics.record_request("/test2", 0.2, 200)
        metrics.record_request("/test1", 0.3, 500)
        
        stats = metrics.get_stats()
        
        assert stats["total_requests"] == 3
        assert stats["error_rate"] > 0
        assert "/test1" in stats["endpoint_stats"]
        assert "/test2" in stats["endpoint_stats"]
        
        # Check endpoint-specific stats
        test1_stats = stats["endpoint_stats"]["/test1"]
        assert test1_stats["count"] == 2
        assert test1_stats["error_rate"] == 50.0


class TestContextualLogger:
    """Test contextual logging system"""
    
    def test_logger_initialization(self):
        """Test ContextualLogger initializes correctly"""
        logger = ContextualLogger("test")
        assert logger.context == {}
    
    def test_context_manager(self):
        """Test context manager functionality"""
        logger = ContextualLogger("test")
        
        with logger.context_manager(user="test_user", operation="test"):
            assert logger.context["user"] == "test_user"
            assert logger.context["operation"] == "test"
        
        # Context should be cleared after exiting
        assert logger.context == {}
    
    def test_format_message(self):
        """Test message formatting with context"""
        logger = ContextualLogger("test")
        logger.context = {"user": "test_user", "id": 123}
        
        formatted = logger._format_message("Test message", {"extra": "data"})
        assert "user=test_user" in formatted
        assert "id=123" in formatted
        assert "extra=data" in formatted


class TestSystemHealthMonitor:
    """Test system health monitoring"""
    
    def test_health_monitor_initialization(self):
        """Test SystemHealthMonitor initializes correctly"""
        monitor = SystemHealthMonitor()
        assert monitor.health_checks == {}
        assert monitor.start_time is not None
    
    def test_get_uptime(self):
        """Test uptime calculation"""
        monitor = SystemHealthMonitor()
        time.sleep(0.1)  # Small delay
        
        uptime = monitor.get_uptime()
        assert "start_time" in uptime
        assert "uptime_seconds" in uptime
        assert "uptime_human" in uptime
        assert uptime["uptime_seconds"] >= 0
    
    @patch('cmp.utils.monitoring.PSUTIL_AVAILABLE', True)
    @patch('cmp.utils.monitoring.psutil')
    def test_get_system_metrics_with_psutil(self, mock_psutil):
        """Test system metrics when psutil is available"""
        monitor = SystemHealthMonitor()
        
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0, available=4*1024**3)
        mock_psutil.disk_usage.return_value = MagicMock(percent=45.0, free=100*1024**3)
        
        metrics = monitor.get_system_metrics()
        
        assert metrics["cpu_usage"] == 25.5
        assert metrics["memory_usage"] == 60.0
        assert "memory_available" in metrics
        assert "disk_usage" in metrics
        assert "disk_free" in metrics
    
    @patch('cmp.utils.monitoring.PSUTIL_AVAILABLE', False)
    def test_get_system_metrics_without_psutil(self):
        """Test system metrics when psutil is not available"""
        monitor = SystemHealthMonitor()
        
        metrics = monitor.get_system_metrics()
        assert "error" in metrics
        assert "psutil not available" in metrics["error"]
    
    def test_register_health_check(self):
        """Test registering custom health checks"""
        monitor = SystemHealthMonitor()
        
        def dummy_check():
            return {"status": "healthy"}
        
        monitor.register_health_check("dummy", dummy_check)
        assert "dummy" in monitor.health_checks
        assert monitor.health_checks["dummy"] == dummy_check


class TestPerformanceMonitorDecorator:
    """Test performance monitoring decorator"""
    
    def test_sync_function_monitoring(self):
        """Test performance monitoring on sync functions"""
        @performance_monitor("test.sync_function")
        def test_function(x, y):
            time.sleep(0.01)  # Small delay
            return x + y
        
        result = test_function(1, 2)
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_async_function_monitoring(self):
        """Test performance monitoring on async functions"""
        @performance_monitor("test.async_function")
        async def test_async_function(x, y):
            await asyncio.sleep(0.01)  # Small delay
            return x * y
        
        import asyncio
        result = await test_async_function(3, 4)
        assert result == 12
    
    def test_sync_function_error_monitoring(self):
        """Test performance monitoring when sync function raises error"""
        @performance_monitor("test.error_function")
        def error_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            error_function()


def test_global_instances():
    """Test that global monitoring instances are properly initialized"""
    assert performance_metrics is not None
    assert system_health_monitor is not None
    assert isinstance(performance_metrics, PerformanceMetrics)
    assert isinstance(system_health_monitor, SystemHealthMonitor)


class TestIntegration:
    """Integration tests for monitoring system"""
    
    def test_monitoring_integration(self):
        """Test that monitoring system works end-to-end"""
        # Reset metrics
        performance_metrics.request_times.clear()
        performance_metrics.error_counts.clear()
        performance_metrics.endpoint_stats.clear()
        
        # Simulate some requests
        performance_metrics.record_request("/api/test", 0.1, 200)
        performance_metrics.record_request("/api/test", 0.2, 200)
        performance_metrics.record_request("/api/error", 0.5, 500)
        
        # Get stats
        stats = performance_metrics.get_stats()
        
        assert stats["total_requests"] == 3
        assert stats["error_rate"] > 0
        assert len(stats["endpoint_stats"]) == 2
        
        # Test system health
        health = system_health_monitor.get_uptime()
        assert "uptime_seconds" in health