"""
LLM Factory for creating language model instances.

This module provides a factory pattern for creating LLM instances
based on configuration, with support for per-agent overrides.
"""

from typing import Any, Optional
from .config import config
from .logger import get_logger

logger = get_logger(__name__)


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Get an LLM instance based on configuration or explicit parameters.
    
    This function allows both global configuration (via .env) and per-agent
    overrides. API keys and endpoints are always read from config for security.
    
    Args:
        provider: LLM provider override (ollama, openai, anthropic, google, azure).
                 If None, uses config.llm_provider
        model: Model name override. If None, uses provider's default from config
        **kwargs: Additional arguments to pass to the LLM constructor
        
    Returns:
        LLM instance configured based on provider
        
    Raises:
        ValueError: If provider is not supported or missing credentials
        
    Examples:
        # Use global config from .env
        llm = get_llm()
        
        # Override provider only
        llm = get_llm(provider="openai")
        
        # Override model only (keeps provider from config)
        llm = get_llm(model="gpt-3.5-turbo")
        
        # Override both
        llm = get_llm(provider="anthropic", model="claude-3-opus-20240229")
        
        # Per-agent configuration
        class Agent1(BaseAgent):
            def __init__(self, config):
                super().__init__(config)
                self.llm = get_llm(model="gpt-4", temperature=0.7)
        
        class Agent2(BaseAgent):
            def __init__(self, config):
                super().__init__(config)
                self.llm = get_llm(provider="anthropic", model="claude-3-5-sonnet-20241022")
    """
    # Use provided provider or fall back to config
    provider = (provider or config.llm_provider).lower()
    
    if provider == "ollama":
        return _get_ollama_llm(model=model, **kwargs)
    elif provider == "openai":
        return _get_openai_llm(model=model, **kwargs)
    elif provider == "anthropic":
        return _get_anthropic_llm(model=model, **kwargs)
    elif provider == "google":
        return _get_google_llm(model=model, **kwargs)
    elif provider == "azure":
        return _get_azure_llm(model=model, **kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported: ollama, openai, anthropic, google, azure"
        )


def _get_ollama_llm(model: Optional[str] = None, **kwargs):
    """Get Ollama LLM instance."""
    try:
        from langchain_community.llms import Ollama
    except ImportError:
        raise ImportError("Please install: pip install langchain-community")
    
    # Use provided model or fall back to config
    model_name = model or config.ollama_model
    
    logger.info(f"Initializing Ollama with model: {model_name}")
    
    return Ollama(
        base_url=config.ollama_base_url,
        model=model_name,
        **kwargs
    )


def _get_openai_llm(model: Optional[str] = None, **kwargs):
    """Get OpenAI LLM instance."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError("Please install: pip install langchain-openai")
    
    if not config.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY not set in environment. "
            "Add it to your .env file: OPENAI_API_KEY=sk-..."
        )
    
    # Use provided model or fall back to config
    model_name = model or config.openai_model
    
    logger.info(f"Initializing OpenAI with model: {model_name}")
    
    return ChatOpenAI(
        api_key=config.openai_api_key,
        model=model_name,
        **kwargs
    )


def _get_anthropic_llm(model: Optional[str] = None, **kwargs):
    """Get Anthropic LLM instance."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError("Please install: pip install langchain-anthropic")
    
    if not config.anthropic_api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set in environment. "
            "Add it to your .env file: ANTHROPIC_API_KEY=sk-ant-..."
        )
    
    # Use provided model or fall back to config
    model_name = model or config.anthropic_model
    
    logger.info(f"Initializing Anthropic with model: {model_name}")
    
    return ChatAnthropic(
        api_key=config.anthropic_api_key,
        model=model_name,
        **kwargs
    )


def _get_google_llm(model: Optional[str] = None, **kwargs):
    """Get Google LLM instance."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError("Please install: pip install langchain-google-genai")
    
    if not config.google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY not set in environment. "
            "Add it to your .env file: GOOGLE_API_KEY=..."
        )
    
    # Use provided model or fall back to config
    model_name = model or config.google_model
    
    logger.info(f"Initializing Google with model: {model_name}")
    
    return ChatGoogleGenerativeAI(
        google_api_key=config.google_api_key,
        model=model_name,
        **kwargs
    )


def _get_azure_llm(model: Optional[str] = None, **kwargs):
    """
    Get Azure OpenAI LLM instance.
    
    Note: For Azure, the 'model' parameter is ignored as Azure uses
    deployment names instead. Use azure_openai_deployment in config.
    """
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError:
        raise ImportError("Please install: pip install langchain-openai")
    
    if not config.azure_openai_api_key:
        raise ValueError(
            "AZURE_OPENAI_API_KEY not set in environment. "
            "Add it to your .env file: AZURE_OPENAI_API_KEY=..."
        )
    if not config.azure_openai_endpoint:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT not set in environment. "
            "Add it to your .env file: AZURE_OPENAI_ENDPOINT=https://..."
        )
    if not config.azure_openai_deployment:
        raise ValueError(
            "AZURE_OPENAI_DEPLOYMENT not set in environment. "
            "Add it to your .env file: AZURE_OPENAI_DEPLOYMENT=..."
        )
    
    if model:
        logger.warning(
            "Model parameter ignored for Azure OpenAI. "
            "Azure uses deployment names from AZURE_OPENAI_DEPLOYMENT config."
        )
    
    logger.info(f"Initializing Azure OpenAI with deployment: {config.azure_openai_deployment}")
    
    return AzureChatOpenAI(
        api_key=config.azure_openai_api_key,
        azure_endpoint=config.azure_openai_endpoint,
        azure_deployment=config.azure_openai_deployment,
        api_version=config.azure_openai_api_version,
        **kwargs
    )