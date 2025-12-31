"""
Unit tests for utility functions.

Tests configuration and logging utilities.
"""

import pytest
import logging
from src.utils.config import Config
from src.utils.logger import get_logger


class TestConfig:
    """Test suite for configuration management."""
    
    def test_default_config_values(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.llm_provider == "ollama"
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.ollama_model == "llama3"
        assert config.log_level == "INFO"
    
    def test_config_from_env(self, monkeypatch):
        """Test configuration loading from environment variables."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OLLAMA_MODEL", "mistral")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        
        config = Config()
        
        assert config.llm_provider == "openai"
        assert config.ollama_model == "mistral"
        assert config.log_level == "DEBUG"


class TestLogger:
    """Test suite for logging functionality."""
    
    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_logger_has_handler(self):
        """Test logger has configured handler."""
        logger = get_logger("test_handler")
        
        assert len(logger.handlers) > 0
    
    def test_logger_singleton(self):
        """Test logger returns same instance for same name."""
        logger1 = get_logger("singleton_test")
        logger2 = get_logger("singleton_test")
        
        assert logger1 is logger2
    
    def test_logger_level(self):
        """Test logger respects configured level."""
        logger = get_logger("level_test")
        
        # Default level should be INFO
        assert logger.level == logging.INFO