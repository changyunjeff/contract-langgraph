"""Abstract base class for LLM factories."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseLanguageModel

from ..service.service_abc import LLMServiceAbstract


class LLMFactoryAbstract(ABC):
    """Abstract base class for LLM factory implementations."""

    @abstractmethod
    def create_llm(self, config: Optional[Dict[str, Any]] = None) -> BaseLanguageModel:
        """Create an LLM instance.

        Args:
            config: Optional configuration dictionary for the LLM.

        Returns:
            BaseLanguageModel: The created language model instance.
        """
        pass

    @abstractmethod
    def create_service(
        self, config: Optional[Dict[str, Any]] = None
    ) -> LLMServiceAbstract:
        """Create an LLM service instance.

        Args:
            config: Optional configuration dictionary for the service.

        Returns:
            LLMServiceAbstract: The created LLM service instance.
        """
        pass
