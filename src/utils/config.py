"""
Configuration management using Pydantic settings.

This module handles loading and validating configuration from environment
variables and .env files.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Config(BaseSettings):
    """
    Application configuration settings.
    
    Loads configuration from environment variables or .env file. Provides
    type validation and default values for all settings.
    
    Attributes:
        llm_provider: LLM provider to use (ollama, openai, anthropic, google, azure)
        ollama_base_url: Base URL for Ollama API
        ollama_model: Model name to use with Ollama
        openai_api_key: OpenAI API key
        openai_model: OpenAI model name
        anthropic_api_key: Anthropic API key
        anthropic_model: Anthropic model name
        google_api_key: Google API key
        google_model: Google model name
        azure_openai_api_key: Azure OpenAI API key
        azure_openai_endpoint: Azure OpenAI endpoint
        azure_openai_deployment: Azure OpenAI deployment name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # General
    llm_provider: str = "ollama"
    log_level: str = "INFO"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    
    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Google
    google_api_key: Optional[str] = None
    google_model: str = "gemini-pro"
    
    # Azure OpenAI
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Global configuration instance
config = Config()