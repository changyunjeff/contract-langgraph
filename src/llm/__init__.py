"""LLM module for creating and managing language models.

This module provides a high-level service interface for working with LLMs.
The service layer handles LLM lifecycle management, caching, and resource cleanup.
"""

from typing import Any, Dict, Optional

from .factory.openai import OpenAIFactory
from .service import LLMServiceAbstract, OpenAIService

# Global factory instance for convenience
_default_factory: Optional[OpenAIFactory] = None


def create_service(config: Optional[Dict[str, Any]] = None) -> LLMServiceAbstract:
    """Create an LLM service instance with the given configuration.

    This is a convenience function that uses the default OpenAI factory.

    Args:
        config: Optional configuration dictionary. Supported keys:
            - model_name: Model name (default: "gpt-3.5-turbo")
            - temperature: Sampling temperature (default: 0.7)
            - max_tokens: Maximum tokens to generate
            - api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
            - base_url: Base URL for API (default: OpenAI default)

    Returns:
        LLMServiceAbstract: The created service instance.

    Example:
        ```python
        from src.llm import create_service

        # Create a service with default config
        service = create_service()

        # Create a service with custom config
        service = create_service({
            "model_name": "gpt-4",
            "temperature": 0.5
        })

        # Use with statement for automatic cleanup
        with create_service() as service:
            response = service.invoke("Hello, world!")
        ```
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = OpenAIFactory()
    return _default_factory.create_service(config)


__all__ = [
    "LLMServiceAbstract",
    "OpenAIService",
    "create_service",
]

