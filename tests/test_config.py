"""
Comprehensive unit tests for configuration module (config.py)
Tests configuration loading, validation, and environment variable handling.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from cmp.config import (
    get_database_url, 
    get_zoho_config, 
    get_jwt_config,
    get_n8n_config,
    get_github_config,
    load_environment_config
)


class TestDatabaseConfig:
    """Test suite for database configuration"""
    
    def test_get_database_url_default(self):
        """Test database URL with default value"""
        with patch.dict(os.environ, {}, clear=True):
            url = get_database_url()
            assert url == "sqlite:///./cmp.db"  # Default value
    
    def test_get_database_url_from_env(self):
        """Test database URL from environment variable"""
        test_url = "postgresql://user:pass@localhost/testdb"
        with patch.dict(os.environ, {"DATABASE_URL": test_url}):
            url = get_database_url()
            assert url == test_url
    
    def test_get_database_url_empty_env(self):
        """Test database URL when environment variable is empty"""
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            url = get_database_url()
            assert url == "sqlite:///./cmp.db"  # Should fall back to default


class TestZohoConfig:
    """Test suite for Zoho configuration"""
    
    def test_get_zoho_config_complete(self):
        """Test Zoho configuration with all values set"""
        env_vars = {
            "ZOHO_CLIENT_ID": "test_client_id",
            "ZOHO_CLIENT_SECRET": "test_client_secret",
            "ZOHO_REFRESH_TOKEN": "test_refresh_token",
            "ZOHO_ORGANIZATION_ID": "test_org_id",
            "ZOHO_BOOKS_URL": "https://books.zoho.com/api/v3"
        }
        
        with patch.dict(os.environ, env_vars):
            config = get_zoho_config()
            
            assert config["client_id"] == "test_client_id"
            assert config["client_secret"] == "test_client_secret"
            assert config["refresh_token"] == "test_refresh_token"
            assert config["organization_id"] == "test_org_id"
            assert config["base_url"] == "https://books.zoho.com/api/v3"
    
    def test_get_zoho_config_missing_values(self):
        """Test Zoho configuration with missing values"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_zoho_config()
            
            assert config["client_id"] is None
            assert config["client_secret"] is None
            assert config["refresh_token"] is None
            assert config["organization_id"] is None
            assert config["base_url"] == "https://books.zoho.com/api/v3"  # Has default
    
    def test_get_zoho_config_partial(self):
        """Test Zoho configuration with some values set"""
        env_vars = {
            "ZOHO_CLIENT_ID": "test_client_id",
            "ZOHO_ORGANIZATION_ID": "test_org_id"
        }
        
        with patch.dict(os.environ, env_vars):
            config = get_zoho_config()
            
            assert config["client_id"] == "test_client_id"
            assert config["client_secret"] is None
            assert config["refresh_token"] is None
            assert config["organization_id"] == "test_org_id"


class TestJWTConfig:
    """Test suite for JWT configuration"""
    
    def test_get_jwt_config_with_secret(self):
        """Test JWT configuration with secret key set"""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key"}):
            config = get_jwt_config()
            
            assert config["secret_key"] == "test_secret_key"
            assert config["algorithm"] == "HS256"  # Default
            assert config["access_token_expire_minutes"] == 30  # Default
    
    def test_get_jwt_config_without_secret(self):
        """Test JWT configuration without secret key"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_jwt_config()
            
            assert config["secret_key"] is None
            assert config["algorithm"] == "HS256"
            assert config["access_token_expire_minutes"] == 30
    
    def test_get_jwt_config_custom_values(self):
        """Test JWT configuration with custom values"""
        env_vars = {
            "JWT_SECRET_KEY": "custom_secret",
            "JWT_ALGORITHM": "RS256",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60"
        }
        
        with patch.dict(os.environ, env_vars):
            config = get_jwt_config()
            
            assert config["secret_key"] == "custom_secret"
            assert config["algorithm"] == "RS256"
            assert config["access_token_expire_minutes"] == 60


class TestN8NConfig:
    """Test suite for N8N configuration"""
    
    def test_get_n8n_config_complete(self):
        """Test N8N configuration with all values"""
        env_vars = {
            "N8N_URL": "http://localhost:5678",
            "N8N_API_KEY": "test_api_key"
        }
        
        with patch.dict(os.environ, env_vars):
            config = get_n8n_config()
            
            assert config["url"] == "http://localhost:5678"
            assert config["api_key"] == "test_api_key"
    
    def test_get_n8n_config_defaults(self):
        """Test N8N configuration with default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_n8n_config()
            
            assert config["url"] == "http://localhost:5678"  # Default
            assert config["api_key"] is None


class TestGitHubConfig:
    """Test suite for GitHub configuration"""
    
    def test_get_github_config_complete(self):
        """Test GitHub configuration with all values"""
        env_vars = {
            "GITHUB_TOKEN": "test_token",
            "GITHUB_REPO_OWNER": "test_owner",
            "GITHUB_REPO_NAME": "test_repo"
        }
        
        with patch.dict(os.environ, env_vars):
            config = get_github_config()
            
            assert config["token"] == "test_token"
            assert config["repo_owner"] == "test_owner"
            assert config["repo_name"] == "test_repo"
    
    def test_get_github_config_defaults(self):
        """Test GitHub configuration with default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_github_config()
            
            assert config["token"] is None
            assert config["repo_owner"] == "xidioda"  # Default
            assert config["repo_name"] == "CMP"  # Default


class TestEnvironmentConfig:
    """Test suite for environment configuration loading"""
    
    def test_load_environment_config_success(self):
        """Test successful environment configuration loading"""
        with patch('cmp.config.load_dotenv') as mock_load_dotenv:
            mock_load_dotenv.return_value = True
            
            result = load_environment_config()
            
            assert result is True
            mock_load_dotenv.assert_called_once()
    
    def test_load_environment_config_file_not_found(self):
        """Test environment configuration when .env file not found"""
        with patch('cmp.config.load_dotenv') as mock_load_dotenv:
            mock_load_dotenv.return_value = False
            
            result = load_environment_config()
            
            assert result is False
            mock_load_dotenv.assert_called_once()
    
    @patch('cmp.config.load_dotenv')
    def test_load_environment_config_with_override(self, mock_load_dotenv):
        """Test environment configuration with override parameter"""
        mock_load_dotenv.return_value = True
        
        load_environment_config(override=True)
        
        mock_load_dotenv.assert_called_once_with(override=True)


@pytest.mark.integration
class TestConfigIntegration:
    """Integration tests for configuration functionality"""
    
    def test_all_config_functions_work_together(self):
        """Test that all configuration functions work together"""
        env_vars = {
            "DATABASE_URL": "sqlite:///./test.db",
            "ZOHO_CLIENT_ID": "test_zoho_id",
            "JWT_SECRET_KEY": "test_jwt_secret",
            "N8N_URL": "http://localhost:5678",
            "GITHUB_TOKEN": "test_github_token"
        }
        
        with patch.dict(os.environ, env_vars):
            # All config functions should work without errors
            db_url = get_database_url()
            zoho_config = get_zoho_config()
            jwt_config = get_jwt_config()
            n8n_config = get_n8n_config()
            github_config = get_github_config()
            
            assert db_url == "sqlite:///./test.db"
            assert zoho_config["client_id"] == "test_zoho_id"
            assert jwt_config["secret_key"] == "test_jwt_secret"
            assert n8n_config["url"] == "http://localhost:5678"
            assert github_config["token"] == "test_github_token"
    
    def test_config_validation(self):
        """Test configuration validation for required fields"""
        # Test that missing critical config is handled gracefully
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise exceptions even with missing config
            db_url = get_database_url()
            zoho_config = get_zoho_config()
            jwt_config = get_jwt_config()
            
            assert db_url is not None  # Has default
            assert isinstance(zoho_config, dict)
            assert isinstance(jwt_config, dict)
    
    def test_environment_override_behavior(self):
        """Test that environment variables properly override defaults"""
        # Set initial environment
        with patch.dict(os.environ, {"DATABASE_URL": "initial_url"}):
            initial_url = get_database_url()
            assert initial_url == "initial_url"
            
            # Override with new value
            with patch.dict(os.environ, {"DATABASE_URL": "new_url"}):
                new_url = get_database_url()
                assert new_url == "new_url"
                assert new_url != initial_url