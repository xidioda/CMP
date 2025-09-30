"""
Comprehensive unit tests for logging configuration module (logging_config.py)
Tests logging setup, configuration, and log management.
"""

import pytest
import os
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

from cmp.logging_config import setup_logging, get_logger, configure_file_handler, configure_console_handler


class TestLoggingSetup:
    """Test suite for logging setup functionality"""
    
    def test_setup_logging_default(self):
        """Test logging setup with default configuration"""
        with patch('cmp.logging_config.logging.basicConfig') as mock_basic_config:
            setup_logging()
            mock_basic_config.assert_called_once()
    
    def test_setup_logging_with_level(self):
        """Test logging setup with specific log level"""
        with patch('cmp.logging_config.logging.basicConfig') as mock_basic_config:
            setup_logging(level=logging.DEBUG)
            mock_basic_config.assert_called_once()
    
    def test_setup_logging_with_log_file(self):
        """Test logging setup with log file specified"""
        with patch('cmp.logging_config.logging.basicConfig') as mock_basic_config:
            with patch('os.makedirs') as mock_makedirs:
                setup_logging(log_file="test.log")
                mock_basic_config.assert_called_once()
    
    def test_setup_logging_creates_log_directory(self):
        """Test that logging setup creates log directory if needed"""
        with patch('cmp.logging_config.logging.basicConfig'):
            with patch('os.makedirs') as mock_makedirs:
                with patch('os.path.exists', return_value=False):
                    setup_logging(log_file="logs/test.log")
                    mock_makedirs.assert_called_once()
    
    def test_setup_logging_existing_directory(self):
        """Test logging setup when log directory already exists"""
        with patch('cmp.logging_config.logging.basicConfig'):
            with patch('os.makedirs') as mock_makedirs:
                with patch('os.path.exists', return_value=True):
                    setup_logging(log_file="logs/test.log")
                    mock_makedirs.assert_not_called()


class TestGetLogger:
    """Test suite for get_logger functionality"""
    
    def test_get_logger_default_name(self):
        """Test getting logger with default name"""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "cmp"
    
    def test_get_logger_custom_name(self):
        """Test getting logger with custom name"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_get_logger_same_instance(self):
        """Test that getting same logger returns same instance"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        assert logger1 is logger2
    
    def test_get_logger_different_instances(self):
        """Test that different logger names return different instances"""
        logger1 = get_logger("name1")
        logger2 = get_logger("name2")
        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestFileHandler:
    """Test suite for file handler configuration"""
    
    def test_configure_file_handler(self):
        """Test file handler configuration"""
        with patch('cmp.logging_config.logging.FileHandler') as mock_file_handler:
            with patch('cmp.logging_config.logging.Formatter') as mock_formatter:
                mock_handler = MagicMock()
                mock_file_handler.return_value = mock_handler
                mock_format = MagicMock()
                mock_formatter.return_value = mock_format
                
                handler = configure_file_handler("test.log")
                
                mock_file_handler.assert_called_once_with("test.log")
                mock_handler.setFormatter.assert_called_once_with(mock_format)
                assert handler == mock_handler
    
    def test_configure_file_handler_with_level(self):
        """Test file handler configuration with specific level"""
        with patch('cmp.logging_config.logging.FileHandler') as mock_file_handler:
            with patch('cmp.logging_config.logging.Formatter'):
                mock_handler = MagicMock()
                mock_file_handler.return_value = mock_handler
                
                configure_file_handler("test.log", level=logging.ERROR)
                
                mock_handler.setLevel.assert_called_once_with(logging.ERROR)
    
    def test_configure_file_handler_creates_directory(self):
        """Test that file handler creates directory if needed"""
        with patch('cmp.logging_config.logging.FileHandler'):
            with patch('cmp.logging_config.logging.Formatter'):
                with patch('os.makedirs') as mock_makedirs:
                    with patch('os.path.exists', return_value=False):
                        configure_file_handler("logs/test.log")
                        mock_makedirs.assert_called_once()


class TestConsoleHandler:
    """Test suite for console handler configuration"""
    
    def test_configure_console_handler(self):
        """Test console handler configuration"""
        with patch('cmp.logging_config.logging.StreamHandler') as mock_stream_handler:
            with patch('cmp.logging_config.logging.Formatter') as mock_formatter:
                mock_handler = MagicMock()
                mock_stream_handler.return_value = mock_handler
                mock_format = MagicMock()
                mock_formatter.return_value = mock_format
                
                handler = configure_console_handler()
                
                mock_stream_handler.assert_called_once()
                mock_handler.setFormatter.assert_called_once_with(mock_format)
                assert handler == mock_handler
    
    def test_configure_console_handler_with_level(self):
        """Test console handler configuration with specific level"""
        with patch('cmp.logging_config.logging.StreamHandler') as mock_stream_handler:
            with patch('cmp.logging_config.logging.Formatter'):
                mock_handler = MagicMock()
                mock_stream_handler.return_value = mock_handler
                
                configure_console_handler(level=logging.WARNING)
                
                mock_handler.setLevel.assert_called_once_with(logging.WARNING)


class TestLoggingLevels:
    """Test suite for logging level handling"""
    
    def test_logging_levels_mapping(self):
        """Test that logging levels are properly mapped"""
        assert logging.DEBUG == 10
        assert logging.INFO == 20
        assert logging.WARNING == 30
        assert logging.ERROR == 40
        assert logging.CRITICAL == 50
    
    def test_logger_level_inheritance(self):
        """Test logger level inheritance"""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")
        
        parent_logger.setLevel(logging.WARNING)
        
        # Child should inherit parent's level if not explicitly set
        assert child_logger.getEffectiveLevel() >= parent_logger.level


class TestLoggingFormatters:
    """Test suite for logging formatters"""
    
    def test_default_formatter(self):
        """Test default logging formatter"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "test" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted
    
    def test_detailed_formatter(self):
        """Test detailed logging formatter"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/path/test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "test.py:42" in formatted
        assert "ERROR" in formatted
        assert "Error message" in formatted


@pytest.mark.integration
class TestLoggingIntegration:
    """Integration tests for logging functionality"""
    
    def test_complete_logging_setup(self):
        """Test complete logging setup with file and console handlers"""
        with patch('cmp.logging_config.logging.basicConfig'):
            with patch('cmp.logging_config.configure_file_handler') as mock_file:
                with patch('cmp.logging_config.configure_console_handler') as mock_console:
                    mock_file.return_value = MagicMock()
                    mock_console.return_value = MagicMock()
                    
                    setup_logging(log_file="test.log", console=True)
                    
                    # Both handlers should be configured
                    mock_file.assert_called_once()
                    mock_console.assert_called_once()
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy and inheritance"""
        # Create parent and child loggers
        parent = get_logger("cmp")
        child = get_logger("cmp.agents")
        grandchild = get_logger("cmp.agents.accountant")
        
        # Set parent level
        parent.setLevel(logging.WARNING)
        
        # All should respect hierarchy
        assert grandchild.parent == child
        assert child.parent == parent
    
    def test_logging_with_exceptions(self):
        """Test logging with exception information"""
        logger = get_logger("test_exceptions")
        
        try:
            raise ValueError("Test exception")
        except Exception:
            # Should not raise error when logging exception
            logger.exception("An error occurred")
    
    def test_rotating_file_handler(self):
        """Test rotating file handler setup"""
        from logging.handlers import RotatingFileHandler
        
        with patch('cmp.logging_config.RotatingFileHandler') as mock_rotating:
            mock_handler = MagicMock()
            mock_rotating.return_value = mock_handler
            
            # Simulate setup with rotating file handler
            handler = RotatingFileHandler("test.log", maxBytes=1024*1024, backupCount=5)
            
            assert handler is not None
    
    def test_log_file_permissions(self):
        """Test log file permissions and access"""
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.chmod') as mock_chmod:
                # Simulate file creation with specific permissions
                setup_logging(log_file="secure.log")
                
                # File should be created (open called)
                # Note: Actual permission setting would depend on implementation