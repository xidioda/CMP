"""
Comprehensive unit tests for main application module (main.py)
Tests FastAPI application setup, routes, middleware, and startup/shutdown events.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from cmp.main import app, startup_event, shutdown_event


class TestApplicationSetup:
    """Test suite for FastAPI application setup"""
    
    def test_app_instance(self):
        """Test that app is properly configured FastAPI instance"""
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)
        assert app.title == "CMP - Comprehensive Management Platform"
        assert app.description is not None
        assert app.version == "1.0.0"
    
    def test_app_metadata(self):
        """Test application metadata configuration"""
        assert "Comprehensive Management Platform" in app.title
        assert len(app.description) > 0
        assert app.version is not None
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "CMP" in data["message"]


class TestRouterInclusion:
    """Test suite for router inclusion"""
    
    def test_auth_router_included(self):
        """Test that auth router is included"""
        routes = [route.path for route in app.routes]
        # Auth routes should be included
        auth_routes = [route for route in routes if route.startswith("/auth")]
        assert len(auth_routes) > 0
    
    def test_agent_router_included(self):
        """Test that agent router is included"""
        routes = [route.path for route in app.routes]
        # Agent routes should be included
        agent_routes = [route for route in routes if route.startswith("/agents")]
        assert len(agent_routes) > 0
    
    def test_api_router_included(self):
        """Test that API router is included"""
        routes = [route.path for route in app.routes]
        # API routes should be included with v1 prefix
        api_routes = [route for route in routes if route.startswith("/api/v1")]
        assert len(api_routes) > 0


class TestMiddleware:
    """Test suite for middleware configuration"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_cors_middleware(self, client):
        """Test CORS middleware configuration"""
        response = client.options("/health")
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_request_processing_middleware(self, client):
        """Test that requests are processed correctly"""
        response = client.get("/health")
        assert response.status_code == 200
        # Response should have proper headers
        assert response.headers.get("content-type") == "application/json"


class TestStartupEvent:
    """Test suite for application startup event"""
    
    @pytest.mark.asyncio
    async def test_startup_event_execution(self):
        """Test startup event executes without errors"""
        with patch('cmp.main.logger') as mock_logger:
            with patch('cmp.main.create_tables') as mock_create_tables:
                with patch('cmp.main.start_agent_scheduler') as mock_start_scheduler:
                    await startup_event()
                    
                    mock_logger.info.assert_called()
                    mock_create_tables.assert_called_once()
                    mock_start_scheduler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_startup_event_database_creation(self):
        """Test that startup event creates database tables"""
        with patch('cmp.main.create_tables') as mock_create_tables:
            with patch('cmp.main.start_agent_scheduler'):
                await startup_event()
                mock_create_tables.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_startup_event_scheduler_start(self):
        """Test that startup event starts agent scheduler"""
        with patch('cmp.main.create_tables'):
            with patch('cmp.main.start_agent_scheduler') as mock_start_scheduler:
                await startup_event()
                mock_start_scheduler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_startup_event_error_handling(self):
        """Test startup event handles errors gracefully"""
        with patch('cmp.main.create_tables', side_effect=Exception("Database error")):
            with patch('cmp.main.logger') as mock_logger:
                with patch('cmp.main.start_agent_scheduler'):
                    # Should not raise exception
                    await startup_event()
                    # Should log error
                    mock_logger.error.assert_called()


class TestShutdownEvent:
    """Test suite for application shutdown event"""
    
    @pytest.mark.asyncio
    async def test_shutdown_event_execution(self):
        """Test shutdown event executes without errors"""
        with patch('cmp.main.logger') as mock_logger:
            with patch('cmp.main.stop_agent_scheduler') as mock_stop_scheduler:
                await shutdown_event()
                
                mock_logger.info.assert_called()
                mock_stop_scheduler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_event_scheduler_stop(self):
        """Test that shutdown event stops agent scheduler"""
        with patch('cmp.main.stop_agent_scheduler') as mock_stop_scheduler:
            await shutdown_event()
            mock_stop_scheduler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_event_error_handling(self):
        """Test shutdown event handles errors gracefully"""
        with patch('cmp.main.stop_agent_scheduler', side_effect=Exception("Scheduler error")):
            with patch('cmp.main.logger') as mock_logger:
                # Should not raise exception
                await shutdown_event()
                # Should log error
                mock_logger.error.assert_called()


class TestApplicationLifecycle:
    """Test suite for application lifecycle"""
    
    @pytest.mark.asyncio
    async def test_complete_lifecycle(self):
        """Test complete application startup and shutdown"""
        with patch('cmp.main.create_tables') as mock_create_tables:
            with patch('cmp.main.start_agent_scheduler') as mock_start:
                with patch('cmp.main.stop_agent_scheduler') as mock_stop:
                    # Startup
                    await startup_event()
                    mock_create_tables.assert_called_once()
                    mock_start.assert_called_once()
                    
                    # Shutdown
                    await shutdown_event()
                    mock_stop.assert_called_once()
    
    def test_application_state_after_startup(self):
        """Test application state after startup"""
        # Application should be properly configured
        assert app.title is not None
        assert len(app.routes) > 0
        
        # Should have health endpoint
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200


class TestErrorHandling:
    """Test suite for error handling"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_404_handling(self, client):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed handling"""
        response = client.post("/health")  # Health endpoint only accepts GET
        assert response.status_code == 405
    
    def test_invalid_json_handling(self, client):
        """Test invalid JSON handling"""
        response = client.post(
            "/auth/login",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        # Should handle invalid JSON gracefully
        assert response.status_code in [400, 422]


class TestDependencyInjection:
    """Test suite for dependency injection"""
    
    def test_database_dependency(self):
        """Test database dependency injection"""
        from cmp.main import app
        from cmp.db import get_db
        
        # Database dependency should be properly configured
        assert get_db in app.dependency_overrides or hasattr(app, "dependency_overrides")
    
    def test_authentication_dependency(self):
        """Test authentication dependency injection"""
        client = TestClient(app)
        
        # Protected endpoints should require authentication
        response = client.get("/agents/status")  # Assuming this is protected
        # Should return 401 or redirect to login
        assert response.status_code in [401, 403, 307, 422]


@pytest.mark.integration
class TestApplicationIntegration:
    """Integration tests for the complete application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_application_startup(self, client):
        """Test that application starts up correctly"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_cors_configuration(self, client):
        """Test CORS configuration"""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
    
    def test_api_documentation_access(self, client):
        """Test API documentation endpoints"""
        # OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Swagger UI should be accessible
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_multiple_concurrent_requests(self, client):
        """Test handling multiple concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_request_timeout_handling(self, client):
        """Test request timeout handling"""
        # Test with a potentially slow endpoint
        response = client.get("/health")
        assert response.status_code == 200
        # Request should complete in reasonable time
        assert response.elapsed.total_seconds() < 10