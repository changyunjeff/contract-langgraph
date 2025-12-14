"""Agent graph definitions.

This module defines the compiled agent graphs that has been registered with LangGraph.
Each agent is created with its context configuration from config files.
"""

from src.agent.agent_manager import get_agent_manager
from src.agent import agent_names

manager = get_agent_manager()

# Create compiled agent with context config from config file
agent_example, _ = manager.create_compiled_agent_by_name(
    name=agent_names.EXAMPLE_AGENT,
    config={},
    graph_name=agent_names.EXAMPLE_AGENT,
)
