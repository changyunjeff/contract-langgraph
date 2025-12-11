"""Abstract base class for LLM services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseLanguageModel


class LLMServiceAbstract(ABC):
    """Abstract base class for LLM service implementations."""

    @abstractmethod
    def get_llm(self) -> Optional[BaseLanguageModel]:
        """Get the LLM instance from the manager.

        Returns:
            Optional[BaseLanguageModel]: The language model instance, or None if not found.
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """Release the LLM back to the manager's cache pool."""
        pass

    @abstractmethod
    def invoke(self, prompt: str, **kwargs: Any) -> str:
        """Invoke the LLM with a prompt.

        Args:
            prompt: The input prompt string.
            **kwargs: Additional arguments for the LLM invocation.

        Returns:
            str: The generated response from the LLM.
        """
        pass

    @abstractmethod
    def batch_invoke(self, prompts: List[str], **kwargs: Any) -> List[str]:
        """Invoke the LLM with multiple prompts in batch.

        Args:
            prompts: List of input prompt strings.
            **kwargs: Additional arguments for the LLM invocation.

        Returns:
            List[str]: List of generated responses from the LLM.
        """
        pass

    @abstractmethod
    def stream(self, prompt: str, **kwargs: Any) -> Any:
        """Stream the LLM response.

        Args:
            prompt: The input prompt string.
            **kwargs: Additional arguments for the LLM invocation.

        Returns:
            Generator or AsyncGenerator: Stream of response chunks.
        """
        pass

    def __enter__(self) -> "LLMServiceAbstract":
        """Context manager entry.

        Returns:
            LLMServiceAbstract: The service instance itself.
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit. Automatically releases the LLM.

        Args:
            exc_type: Exception type if any.
            exc_val: Exception value if any.
            exc_tb: Exception traceback if any.
        """
        self.release()

