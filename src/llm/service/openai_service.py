"""OpenAI LLM service implementation."""

from typing import Any, List, Optional

from langchain_core.language_models import BaseLanguageModel

from ..manager import get_llm_manager
from .service_abc import LLMServiceAbstract


class OpenAIService(LLMServiceAbstract):
    """OpenAI LLM service implementation."""

    def __init__(
        self,
        config_hash: str,
        llm: Optional[BaseLanguageModel] = None,
    ) -> None:
        """Initialize OpenAI service.

        Args:
            config_hash: Configuration hash for retrieving LLM from manager.
            llm: Optional LLM instance. If provided, will be used as initial reference.
                The service will always get LLM from manager to ensure proper reference counting.
        """
        self._config_hash = config_hash
        self._manager = get_llm_manager()
        self._released = False
        # If llm is provided, it's already registered in manager, so we get it from manager
        # to ensure proper reference counting
        if llm is not None:
            # The llm is already in manager, get it to increment reference count
            self._llm = self._manager.get_llm(config_hash)
        else:
            self._llm = None

    def get_llm(self) -> Optional[BaseLanguageModel]:
        """Get the LLM instance from the manager.

        Returns:
            Optional[BaseLanguageModel]: The LLM instance, or None if not found or released.
        """
        if self._released:
            return None

        # Always get from manager to ensure proper reference counting
        if self._llm is None:
            self._llm = self._manager.get_llm(self._config_hash)

        return self._llm

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        """Invoke the LLM with a prompt.

        Args:
            prompt: The input prompt string.
            **kwargs: Additional arguments for the LLM invocation.

        Returns:
            str: The generated response from the LLM.

        Raises:
            ValueError: If the LLM is not available (released or not found).
        """
        llm = self.get_llm()
        if llm is None:
            raise ValueError("LLM is not available. It may have been released.")

        response = llm.invoke(prompt, **kwargs)
        if hasattr(response, "content"):
            return response.content
        return str(response)

    def batch_invoke(self, prompts: List[str], **kwargs: Any) -> List[str]:
        """Invoke the LLM with multiple prompts in batch.

        Args:
            prompts: List of input prompt strings.
            **kwargs: Additional arguments for the LLM invocation.

        Returns:
            List[str]: List of generated responses from the LLM.

        Raises:
            ValueError: If the LLM is not available (released or not found).
        """
        llm = self.get_llm()
        if llm is None:
            raise ValueError("LLM is not available. It may have been released.")

        responses = llm.batch(prompts, **kwargs)
        return [
            response.content if hasattr(response, "content") else str(response)
            for response in responses
        ]

    def stream(self, prompt: str, **kwargs: Any) -> Any:
        """Stream the LLM response.

        Args:
            prompt: The input prompt string.
            **kwargs: Additional arguments for the LLM invocation.

        Returns:
            Generator: Stream of response chunks.

        Raises:
            ValueError: If the LLM is not available (released or not found).
        """
        llm = self.get_llm()
        if llm is None:
            raise ValueError("LLM is not available. It may have been released.")

        return llm.stream(prompt, **kwargs)

    def release(self) -> None:
        """Release the LLM back to the manager's cache pool."""
        if not self._released and self._llm is not None:
            self._manager.release_llm(self._config_hash)
            self._released = True
            self._llm = None

    def __del__(self) -> None:
        """Cleanup: release LLM when service is destroyed."""
        try:
            self.release()
        except Exception:
            # Ignore errors during cleanup
            pass

