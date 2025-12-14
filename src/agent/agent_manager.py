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
from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)


def _get_agent_factory(name: str) -> Callable[[Optional[Dict[str, Any]]], StateGraph]:
    """Get the factory function for creating an agent by name.
    
    Args:
        name: Agent name (e.g., "example").
        
    Returns:
        Factory function that creates a StateGraph, accepting optional config.
        
    Raises:
        ValueError: If agent factory not found.
    """
    # Import agent modules dynamically
    if name == "example":
        from src.agent.example import create_agent
        return create_agent
    else:
        raise ValueError(f"Unknown agent name: {name}")


def _compute_agent_id(name: str, config: Dict[str, Any]) -> str:
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


class AgentManager:
    """Global singleton manager for agent registration and creation."""

    _instance: Optional["AgentManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, **kwargs) -> "AgentManager":
        """Create or return the singleton instance.

        Args:
            **kwargs: Additional keyword arguments (ignored after first instantiation).
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, **kwargs) -> None:
        """Initialize the agent manager.

        Args:
            **kwargs: Additional keyword arguments (ignored).
        """
        if not hasattr(self, "_initialized") or not self._initialized:
            with self._lock:
                if not hasattr(self, "_initialized") or not self._initialized:
                    # Registry: agent_id -> (name, config, factory_func)
                    self._registered_agents: Dict[str, Tuple[str, Dict[str, Any], Callable]] = {}
                    # Name index: name -> [agent_ids]
                    self._name_index: Dict[str, List[str]] = {}
                    # Agent factory registry: name -> factory function
                    self._agent_factories: Dict[str, Callable[[Optional[Dict[str, Any]]], StateGraph]] = {}
                    # Statistics
                    self._creation_count: int = 0
                    self._registration_count: int = 0
                    self._initialized = True
                    # Register known agents
                    self._register_known_agents()
    
    def _register_known_agents(self) -> None:
        """Register known agent factories."""
        try:
            from src.agent import agent_names
            # Register example agent factory
            if hasattr(agent_names, "EXAMPLE_AGENT"):
                self._agent_factories[agent_names.EXAMPLE_AGENT] = _get_agent_factory(
                    agent_names.EXAMPLE_AGENT
                )
        except Exception as e:
            logger.warning(f"Failed to register known agents: {e}")

    def register(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> str:
        """Register an agent with name and configuration.

        Args:
            name: Agent name (e.g., "example").
            config: Configuration dictionary.

        Returns:
            str: The unique agent ID.

        Raises:
            ValueError: If agent with same name and config already exists.
        """
        if config is None:
            config = {}
        
        agent_id = _compute_agent_id(name, config)
        
        with self._lock:
            if agent_id in self._registered_agents:
                raise ValueError(
                    f"Agent with name '{name}' and config already registered "
                    f"(agent_id: {agent_id})"
                )
            
            # Get factory function
            if name not in self._agent_factories:
                try:
                    factory_func = _get_agent_factory(name)
                    self._agent_factories[name] = factory_func
                except ValueError as e:
                    raise ValueError(f"Cannot register agent '{name}': {e}")
            
            factory_func = self._agent_factories[name]
            
            # Register agent
            self._registered_agents[agent_id] = (name, config, factory_func)
            
            # Update name index
            if name not in self._name_index:
                self._name_index[name] = []
            self._name_index[name].append(agent_id)
            
            self._registration_count += 1
            logger.info(f"Registered agent '{name}' with ID {agent_id}")
        
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
            
            name, config, factory_func = self._registered_agents[agent_id]
        
        try:
            # Use config from registered agent
            agent = factory_func(config)
            self._creation_count += 1
            logger.debug(f"Created agent '{name}' with ID {agent_id}")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent '{name}' with ID {agent_id}: {e}", exc_info=True)
            raise ValueError(f"Failed to create agent: {e}") from e

    def get_agent_ids_by_name(self, name: str) -> List[str]:
        """Get all agent IDs registered with the given name.

        Args:
            name: Agent name.

        Returns:
            list[str]: List of agent IDs.
        """
        with self._lock:
            return self._name_index.get(name, []).copy()

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
    ) -> StateGraph:
        """Create an agent by name and config, with automatic registration.

        If auto_register is enabled and the agent is not registered, it will be
        automatically registered before creation.

        Args:
            name: Agent name (e.g., "example").
            config: Configuration dictionary for the agent. Defaults to empty dict.

        Returns:
            StateGraph: The agent graph.

        Raises:
            ValueError: If agent creation fails.
        """
        if config is None:
            config = {}
        
        agent_id = _compute_agent_id(name, config)
        
        # Check if already registered and get factory function
        with self._lock:
            if agent_id in self._registered_agents:
                # Agent already registered, get factory function and registered config
                _, registered_config, factory_func = self._registered_agents[agent_id]
            else:
                # Need to register first
                factory_func = None
                registered_config = None
        
        # If factory function found, create agent outside the lock
        if factory_func is not None:
            try:
                # Use registered config to ensure consistency
                agent = factory_func(registered_config)
                with self._lock:
                    self._creation_count += 1
                logger.debug(f"Created agent '{name}' with ID {agent_id}")
                return agent
            except Exception as e:
                logger.error(f"Failed to create agent '{name}' with ID {agent_id}: {e}", exc_info=True)
                raise ValueError(f"Failed to create agent: {e}") from e
        
        # Auto-register if not already registered
        try:
            self.register(name, config)
        except ValueError as e:
            # If registration fails because it already exists, that's okay
            # (race condition - another thread registered it)
            if "already registered" not in str(e).lower():
                raise
        
        # Now create it
        return self.create_agent(agent_id)

    def create_compiled_agent_by_name(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        graph_name: Optional[str] = None,
    ) -> Tuple[CompiledStateGraph, Dict[str, Any]]:
        """Create a compiled agent with context config by name.

        This is a convenience method that creates an agent, compiles it, and returns
        both the compiled graph and the context config to use when invoking it.

        Args:
            name: Agent name (e.g., "example").
            config: Configuration dictionary for the agent. Defaults to empty dict.
            graph_name: Optional name for the compiled graph. Defaults to agent name.

        Returns:
            Tuple[CompiledStateGraph, Dict[str, Any]]: The compiled graph and context config.

        Raises:
            ValueError: If agent creation fails.
        """
        if config is None:
            config = {}
        
        if graph_name is None:
            graph_name = name
        
        # Create the agent graph
        agent = self.create_agent_by_name(name, config)
        
        # Compile the graph
        try:
            compiled_graph = agent.compile(name=graph_name)
            logger.debug(f"Compiled agent '{name}' as '{graph_name}'")
        except Exception as e:
            logger.error(f"Failed to compile agent '{name}': {e}", exc_info=True)
            raise ValueError(f"Failed to compile agent: {e}") from e
        
        # Build context config from the config dict
        # Extract context-related config and store in context_config
        context_config: Dict[str, Any] = {}
        if name == "example":
            # Map config to context fields
            # The context_config dict will be used to create ExampleContext when invoking
            context_config = {
                "example_context": config.get("example_context", "this is an example context from config file")
            }
            
            # Extract LLM configuration from agent config
            # Store LLM config in context (will be used to create LLM in nodes)
            llm_config = {}
            for key in ["llm_provider", "llm_model", "temperature", "max_tokens", "api_key", "base_url"]:
                if key in config:
                    llm_config[key] = config[key]
            
            # Store LLM config in context_config (empty dict means use defaults)
            context_config["llm_config"] = llm_config if llm_config else {}
        
        return compiled_graph, context_config

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the manager.

        Returns:
            Dict[str, Any]: Statistics dictionary.
        """
        with self._lock:
            return {
                "total_registered": len(self._registered_agents),
                "total_creations": self._creation_count,
                "total_registrations": self._registration_count,
                "agents_by_name": {
                    name: len(ids) for name, ids in self._name_index.items()
                },
                "registered_agents": list(self._registered_agents.keys()),
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
        _agent_manager = AgentManager()
    return _agent_manager
