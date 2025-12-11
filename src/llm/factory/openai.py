"""OpenAI LLM factory implementation."""

import os
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

from ..manager import get_llm_manager
from ..service.openai_service import OpenAIService
from ..service.service_abc import LLMServiceAbstract
from .factory_abc import LLMFactoryAbstract


class OpenAIFactory(LLMFactoryAbstract):
    """Factory for creating OpenAI LLM instances and services."""

    def __init__(self, default_config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize OpenAI factory.

        Args:
            default_config: Default configuration dictionary for LLM creation.
                If None, uses environment variables or defaults.
        """
        self.default_config = default_config or {}

    def create_llm(self, config: Optional[Dict[str, Any]] = None) -> BaseLanguageModel:
        """Create an OpenAI LLM instance and register it with the manager.

        The manager will reuse cached LLM if available with the same config.

        Args:
            config: Optional configuration dictionary. Merged with default_config.
                Supported keys:
                - model_name: Model name (default: "gpt-3.5-turbo")
                - temperature: Sampling temperature (default: 0.7)
                - max_tokens: Maximum tokens to generate
                - api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
                - base_url: Base URL for API (default: OpenAI default)

        Returns:
            BaseLanguageModel: The created or cached ChatOpenAI instance (registered with manager).
        """
        merged_config = {**self.default_config, **(config or {})}
        manager = get_llm_manager()
        config_hash = manager.compute_config_hash(merged_config)

        # Check if manager already has this LLM (active or cached)
        existing_llm = manager.get_llm(config_hash)
        if existing_llm is not None:
            return existing_llm

        # Create new LLM instance
        model_name = merged_config.get("model_name", "gpt-3.5-turbo")
        temperature = merged_config.get("temperature", 0.7)
        max_tokens = merged_config.get("max_tokens")
        api_key = merged_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        base_url = merged_config.get("base_url")

        # Extract additional kwargs
        kwargs = {
            k: v
            for k, v in merged_config.items()
            if k
            not in ["model_name", "temperature", "max_tokens", "api_key", "base_url"]
        }

        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

        # Register with manager
        _, registered_llm = manager.register_llm(llm, merged_config)

        return registered_llm

    def create_service(
        self, config: Optional[Dict[str, Any]] = None
    ) -> LLMServiceAbstract:
        """Create an OpenAI service instance.

        The service will get LLM from the manager using the config hash.

        Args:
            config: Optional configuration dictionary. Merged with default_config.
                See create_llm for supported keys.

        Returns:
            LLMServiceAbstract: The created OpenAIService instance.
        """
        merged_config = {**self.default_config, **(config or {})}

        # Create or get LLM from manager
        llm = self.create_llm(config)

        # Create service with config hash for manager reference
        manager = get_llm_manager()
        config_hash = manager.compute_config_hash(merged_config)

        return OpenAIService(config_hash=config_hash, llm=llm)
