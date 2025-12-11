"""LLM Manager for managing LLM object lifecycle and caching."""

import hashlib
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from weakref import WeakSet

from langchain_core.language_models import BaseLanguageModel


@dataclass
class LLMEntry:
    """Entry for LLM object in the manager."""

    llm: BaseLanguageModel
    config_hash: str
    config: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    reference_count: int = 0
    is_in_use: bool = False


class LLMManager:
    """Global singleton manager for LLM objects with caching and lifecycle management."""

    _instance: Optional["LLMManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "LLMManager":
        """Create or return the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        cache_ttl: float = 3600.0,
        cleanup_interval: float = 300.0,
        max_cache_size: int = 100,
    ) -> None:
        """Initialize the LLM manager.

        Args:
            cache_ttl: Time to live for cached LLM objects in seconds (default: 1 hour).
            cleanup_interval: Interval for periodic cleanup in seconds (default: 5 minutes).
            max_cache_size: Maximum number of cached LLM objects (default: 100).
        """
        if self._initialized:
            return

        self._cache_ttl = cache_ttl
        self._cleanup_interval = cleanup_interval
        self._max_cache_size = max_cache_size

        # Active LLM entries: config_hash -> LLMEntry
        self._active_entries: Dict[str, LLMEntry] = {}

        # Cache pool: config_hash -> LLMEntry (unused LLMs)
        self._cache_pool: Dict[str, LLMEntry] = {}

        # Track service references to LLMs
        self._service_refs: WeakSet[Any] = WeakSet()

        self._lock = threading.RLock()
        self._initialized = True

        # Start cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self) -> None:
        """Start the background cleanup thread."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._stop_cleanup.clear()
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop, daemon=True
            )
            self._cleanup_thread.start()

    def _cleanup_loop(self) -> None:
        """Background thread for periodic cleanup."""
        while not self._stop_cleanup.wait(self._cleanup_interval):
            self.cleanup_unused()

    def compute_config_hash(self, config: Dict[str, Any]) -> str:
        """Compute a hash for the configuration.

        Args:
            config: Configuration dictionary.

        Returns:
            str: Hash string of the configuration.
        """
        # Sort keys for consistent hashing
        sorted_config = sorted(config.items())
        config_str = str(sorted_config)
        return hashlib.md5(config_str.encode()).hexdigest()

    def register_llm(
        self, llm: BaseLanguageModel, config: Dict[str, Any]
    ) -> Tuple[str, BaseLanguageModel]:
        """Register a newly created LLM with the manager.

        Args:
            llm: The LLM instance to register.
            config: Configuration dictionary used to create the LLM.

        Returns:
            Tuple[str, BaseLanguageModel]: (config_hash, llm) for reference.
        """
        config_hash = self.compute_config_hash(config)

        with self._lock:
            # Check if we have a cached LLM with the same config
            if config_hash in self._cache_pool:
                # Reuse cached LLM
                entry = self._cache_pool.pop(config_hash)
                entry.is_in_use = True
                entry.reference_count = 1
                entry.last_used_at = time.time()
                self._active_entries[config_hash] = entry
                return config_hash, entry.llm

            # Create new entry
            entry = LLMEntry(
                llm=llm,
                config_hash=config_hash,
                config=config,
                is_in_use=True,
                reference_count=1,
            )
            self._active_entries[config_hash] = entry

        return config_hash, llm

    def get_llm(self, config_hash: str) -> Optional[BaseLanguageModel]:
        """Get an LLM by its config hash.

        Args:
            config_hash: The configuration hash.

        Returns:
            Optional[BaseLanguageModel]: The LLM instance if found, None otherwise.
        """
        with self._lock:
            # Check active entries first
            if config_hash in self._active_entries:
                entry = self._active_entries[config_hash]
                entry.last_used_at = time.time()
                entry.reference_count += 1
                return entry.llm

            # Check cache pool
            if config_hash in self._cache_pool:
                entry = self._cache_pool.pop(config_hash)
                entry.is_in_use = True
                entry.reference_count = 1
                entry.last_used_at = time.time()
                self._active_entries[config_hash] = entry
                return entry.llm

        return None

    def release_llm(self, config_hash: str) -> None:
        """Release an LLM back to the cache pool when no longer in use.

        Args:
            config_hash: The configuration hash of the LLM to release.
        """
        with self._lock:
            if config_hash not in self._active_entries:
                return

            entry = self._active_entries[config_hash]
            entry.reference_count -= 1

            if entry.reference_count <= 0:
                entry.is_in_use = False
                entry.reference_count = 0
                # Move to cache pool
                del self._active_entries[config_hash]
                self._cache_pool[config_hash] = entry

    def cleanup_unused(self) -> None:
        """Clean up unused LLM objects from the cache pool."""
        current_time = time.time()
        to_remove = []

        with self._lock:
            # Remove expired entries from cache pool
            for config_hash, entry in list(self._cache_pool.items()):
                age = current_time - entry.last_used_at
                if age > self._cache_ttl:
                    to_remove.append(config_hash)

            for config_hash in to_remove:
                del self._cache_pool[config_hash]

            # Limit cache pool size
            if len(self._cache_pool) > self._max_cache_size:
                # Remove oldest entries
                sorted_entries = sorted(
                    self._cache_pool.items(),
                    key=lambda x: x[1].last_used_at,
                )
                excess = len(self._cache_pool) - self._max_cache_size
                for config_hash, _ in sorted_entries[:excess]:
                    del self._cache_pool[config_hash]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the manager.

        Returns:
            Dict[str, Any]: Statistics dictionary.
        """
        with self._lock:
            return {
                "active_entries": len(self._active_entries),
                "cached_entries": len(self._cache_pool),
                "total_entries": len(self._active_entries) + len(self._cache_pool),
                "cache_ttl": self._cache_ttl,
                "max_cache_size": self._max_cache_size,
            }

    def shutdown(self) -> None:
        """Shutdown the manager and stop cleanup thread."""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)


# Global singleton instance
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """Get the global LLM manager singleton instance.

    Returns:
        LLMManager: The singleton manager instance.
    """
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

