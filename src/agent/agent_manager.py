"""Agent Manager for managing agent registration and creation."""

import hashlib
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from langgraph.graph import StateGraph

logger = logging.getLogger(__name__)


@dataclass
class AgentEntry:
    """Entry for agent in the manager."""

    name: str
    agent_id: str
    config: Dict[str, Any]
    config_path: Optional[str] = None
    create_func: Optional[Callable[[], StateGraph]] = None
    created_at: float = field(default_factory=time.time)


class AgentManager:
    """Global singleton manager for agent registration and creation."""

    _instance: Optional["AgentManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, auto_register: bool = True, **kwargs) -> "AgentManager":
        """Create or return the singleton instance.

        Args:
            auto_register: If True, automatically register agents when creating by name.
                         Default is True. Only used on first instantiation.
            **kwargs: Additional keyword arguments (ignored after first instantiation).
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._pending_auto_register = auto_register
        return cls._instance

    def __init__(self, auto_register: bool = True, **kwargs) -> None:
        """Initialize the agent manager.

        Args:
            auto_register: If True, automatically register agents when creating by name.
                         Default is True.
            **kwargs: Additional keyword arguments (ignored).
        """
        if self._initialized:
            return

        # Registered agents: agent_id -> AgentEntry
        self._registered_agents: Dict[str, AgentEntry] = {}

        # Name to agent_id mapping: name -> set of agent_ids
        self._name_to_ids: Dict[str, set] = {}

        # Auto-register flag (use pending value from __new__ if available)
        self._auto_register = getattr(self, "_pending_auto_register", auto_register)
        if hasattr(self, "_pending_auto_register"):
            delattr(self, "_pending_auto_register")

        self._lock = threading.RLock()
        self._initialized = True

    def _compute_agent_id(self, name: str, config: Dict[str, Any]) -> str:
        """Compute a unique agent ID from name and config.

        Args:
            name: Agent name.
            config: Configuration dictionary.

        Returns:
            str: Unique agent ID (hash of name + config).
        """
        # Sort config keys for consistent hashing
        sorted_config = sorted(config.items())
        config_str = json.dumps(sorted_config, sort_keys=True, ensure_ascii=False)
        combined = f"{name}:{config_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def register(
        self,
        name: str,
        config: Dict[str, Any],
        config_path: Optional[str] = None,
        create_func: Optional[Callable[[], StateGraph]] = None,
        skip_file_load: bool = False,
    ) -> str:
        """Register an agent with name and configuration.

        Args:
            name: Agent name (e.g., "example").
            config: Configuration dictionary for the agent.
            config_path: Optional path to the JSON config file.
            create_func: Optional function to create the agent graph.
                         If None, will try to import from agent module.
            skip_file_load: If True, skip loading config from file (config is already merged).
                           Default is False.

        Returns:
            str: The unique agent ID.

        Raises:
            ValueError: If agent with same name and config already exists.
        """
        # Load config from file if config_path is provided and not skipped
        if config_path and not skip_file_load:
            config_path_obj = Path(config_path)
            if config_path_obj.exists():
                with open(config_path_obj, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    # Merge file config with provided config (provided config takes precedence)
                    config = {**file_config, **config}
            else:
                logger.warning(
                    "Config file not found at %s, using provided config", config_path
                )

        agent_id = self._compute_agent_id(name, config)

        with self._lock:
            # Check if already registered
            if agent_id in self._registered_agents:
                logger.info(
                    "Agent with name '%s' and config already registered with ID: %s",
                    name,
                    agent_id,
                )
                return agent_id

            # Create entry
            entry = AgentEntry(
                name=name,
                agent_id=agent_id,
                config=config,
                config_path=config_path,
                create_func=create_func,
            )

            self._registered_agents[agent_id] = entry

            # Update name mapping
            if name not in self._name_to_ids:
                self._name_to_ids[name] = set()
            self._name_to_ids[name].add(agent_id)

            logger.info(
                "Registered agent '%s' with ID: %s, config: %s",
                name,
                agent_id,
                config,
            )

        return agent_id

    def create_agent(self, agent_id: str) -> Optional[StateGraph]:
        """Create an agent by its unique ID.

        Args:
            agent_id: The unique agent ID.

        Returns:
            Optional[StateGraph]: The agent graph if found, None otherwise.

        Raises:
            ValueError: If agent is not registered or creation fails.
        """
        with self._lock:
            if agent_id not in self._registered_agents:
                raise ValueError(f"Agent with ID '{agent_id}' is not registered")

            entry = self._registered_agents[agent_id]

            # Use provided create_func if available
            if entry.create_func:
                try:
                    return entry.create_func()
                except Exception as e:
                    logger.error(
                        "Failed to create agent '%s' using create_func: %s",
                        entry.name,
                        str(e),
                        exc_info=True,
                    )
                    raise ValueError(
                        f"Failed to create agent '{entry.name}': {str(e)}"
                    ) from e

            # Try to import and create from agent module
            try:
                # Import agent module based on name
                module_path = f"src.agent.{entry.name}.agent"
                module = __import__(module_path, fromlist=["create_agent"])
                create_agent_func = getattr(module, "create_agent", None)

                if create_agent_func is None:
                    raise ValueError(
                        f"Module '{module_path}' does not have 'create_agent' function"
                    )

                return create_agent_func()
            except ImportError as e:
                logger.error(
                    "Failed to import agent module for '%s': %s",
                    entry.name,
                    str(e),
                    exc_info=True,
                )
                raise ValueError(
                    f"Failed to import agent module for '{entry.name}': {str(e)}"
                ) from e
            except Exception as e:
                logger.error(
                    "Failed to create agent '%s': %s",
                    entry.name,
                    str(e),
                    exc_info=True,
                )
                raise ValueError(
                    f"Failed to create agent '{entry.name}': {str(e)}"
                ) from e

    def get_agent_ids_by_name(self, name: str) -> List[str]:
        """Get all agent IDs registered with the given name.

        Args:
            name: Agent name.

        Returns:
            list[str]: List of agent IDs.
        """
        with self._lock:
            return list(self._name_to_ids.get(name, set()))

    def get_agent_entry(self, agent_id: str) -> Optional[AgentEntry]:
        """Get agent entry by ID.

        Args:
            agent_id: The unique agent ID.

        Returns:
            Optional[AgentEntry]: The agent entry if found, None otherwise.
        """
        with self._lock:
            return self._registered_agents.get(agent_id)

    def is_registered(self, agent_id: str) -> bool:
        """Check if an agent is registered.

        Args:
            agent_id: The unique agent ID.

        Returns:
            bool: True if registered, False otherwise.
        """
        with self._lock:
            return agent_id in self._registered_agents

    def create_agent_by_name(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
    ) -> StateGraph:
        """Create an agent by name and config, with automatic registration.

        If auto_register is enabled and the agent is not registered, it will be
        automatically registered before creation.

        Args:
            name: Agent name (e.g., "example").
            config: Configuration dictionary for the agent. Defaults to empty dict.
            config_path: Optional path to the JSON config file.

        Returns:
            StateGraph: The agent graph.

        Raises:
            ValueError: If agent creation fails.
        """
        if config is None:
            config = {}

        # Load config from file first if config_path is provided
        # This ensures agent_id is computed based on the merged config
        merged_config = config.copy()
        if config_path:
            config_path_obj = Path(config_path)
            if config_path_obj.exists():
                with open(config_path_obj, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    # Merge file config with provided config (provided config takes precedence)
                    merged_config = {**file_config, **merged_config}
            else:
                logger.warning(
                    "Config file not found at %s, using provided config", config_path
                )

        # Compute agent ID based on merged config
        agent_id = self._compute_agent_id(name, merged_config)

        with self._lock:
            # Check if already registered
            if agent_id not in self._registered_agents:
                if self._auto_register:
                    # Auto-register the agent
                    logger.info(
                        "Auto-registering agent '%s' with config: %s", name, merged_config
                    )
                    self.register(
                        name=name,
                        config=merged_config,  # Pass merged config to ensure consistent agent_id
                        config_path=config_path,
                        skip_file_load=True,  # Skip file load since config is already merged
                    )
                else:
                    raise ValueError(
                        f"Agent with name '{name}' and given config is not registered. "
                        "Enable auto_register or register the agent first."
                    )

        # Create agent using the registered ID
        return self.create_agent(agent_id)

    def enable_auto_register(self) -> None:
        """Enable automatic agent registration."""
        with self._lock:
            self._auto_register = True
            logger.info("Auto-register enabled")

    def disable_auto_register(self) -> None:
        """Disable automatic agent registration."""
        with self._lock:
            self._auto_register = False
            logger.info("Auto-register disabled")

    def is_auto_register_enabled(self) -> bool:
        """Check if auto-register is enabled.

        Returns:
            bool: True if auto-register is enabled, False otherwise.
        """
        with self._lock:
            return self._auto_register

    def get_context_config(self, agent_id: str) -> Dict[str, Any]:
        """Get context configuration for invoking an agent.

        This method extracts context-related fields from the agent's config
        and formats them for LangGraph's configurable context.

        Args:
            agent_id: The unique agent ID.

        Returns:
            Dict[str, Any]: Configuration dictionary for LangGraph's configurable context.
                           Format: {"configurable": {...}}

        Raises:
            ValueError: If agent is not registered.
        """
        with self._lock:
            if agent_id not in self._registered_agents:
                raise ValueError(f"Agent with ID '{agent_id}' is not registered")

            entry = self._registered_agents[agent_id]

            # Try to import context schema to filter config fields
            try:
                module_path = f"src.agent.{entry.name}.context"
                module = __import__(module_path, fromlist=[None])
                # Try to find context class (usually named {Name}Context)
                context_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and hasattr(attr, "model_fields")  # Pydantic model
                        and "Context" in attr_name
                    ):
                        context_class = attr
                        break

                if context_class:
                    # Filter config to only include context fields
                    context_fields = set(context_class.model_fields.keys())
                    context_config = {
                        k: v
                        for k, v in entry.config.items()
                        if k in context_fields
                    }
                    return {"configurable": context_config}
            except (ImportError, AttributeError):
                # If context class not found, return all config as context
                # This is a fallback for agents without explicit context schema
                logger.warning(
                    "Could not find context schema for agent '%s', "
                    "using all config as context",
                    entry.name,
                )

            # Fallback: return all config as context
            return {"configurable": entry.config}

    def create_compiled_agent_by_name(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        graph_name: Optional[str] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """Create a compiled agent with context config by name.

        This is a convenience method that creates an agent, compiles it, and returns
        both the compiled graph and the context config to use when invoking it.

        Args:
            name: Agent name (e.g., "example").
            config: Configuration dictionary for the agent. Defaults to empty dict.
            config_path: Optional path to the JSON config file.
            graph_name: Optional name for the compiled graph. Defaults to agent name.

        Returns:
            tuple: (compiled_graph, context_config) where:
                - compiled_graph: The compiled StateGraph ready to use
                - context_config: The context configuration dict to pass to ainvoke/invoke

        Raises:
            ValueError: If agent creation fails.
        """
        if graph_name is None:
            graph_name = name

        # Create agent graph
        agent_graph = self.create_agent_by_name(
            name=name,
            config=config,
            config_path=config_path,
        )

        # Compile the graph
        compiled_graph = agent_graph.compile(name=graph_name)

        # Get the agent ID to retrieve context config
        # We need to compute it the same way as create_agent_by_name does
        if config is None:
            config = {}
        merged_config = config.copy()
        if config_path:
            config_path_obj = Path(config_path)
            if config_path_obj.exists():
                with open(config_path_obj, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    merged_config = {**file_config, **merged_config}
        agent_id = self._compute_agent_id(name, merged_config)

        # Ensure agent is registered (it should be from create_agent_by_name)
        with self._lock:
            if agent_id not in self._registered_agents:
                # This shouldn't happen, but register it just in case
                logger.warning(
                    "Agent %s not registered, registering now", agent_id
                )
                self.register(
                    name=name,
                    config=merged_config,  # Pass merged config to ensure consistent agent_id
                    config_path=config_path,
                    skip_file_load=True,  # Skip file load since config is already merged
                )

        # Get context config
        context_config = self.get_context_config(agent_id)

        return compiled_graph, context_config

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the manager.

        Returns:
            Dict[str, Any]: Statistics dictionary.
        """
        with self._lock:
            return {
                "registered_agents": len(self._registered_agents),
                "agents_by_name": {
                    name: len(ids) for name, ids in self._name_to_ids.items()
                },
                "auto_register": self._auto_register,
            }


# Global singleton instance
_agent_manager: Optional[AgentManager] = None


def get_agent_manager(auto_register: bool = True) -> AgentManager:
    """Get the global agent manager singleton instance.

    Args:
        auto_register: If True, automatically register agents when creating by name.
                      Default is True. Only takes effect on first call.

    Returns:
        AgentManager: The singleton manager instance.
    """
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager(auto_register=auto_register)
    return _agent_manager
