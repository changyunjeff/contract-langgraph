"""Example agent implementation.

This module defines an example agent graph based on the agent_demo template.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from src.llm import create_service

from .context import ExampleContext
from .state import ExampleState

logger = logging.getLogger(__name__)


async def call_model(
    state: ExampleState, runtime: Runtime[ExampleContext]
) -> Dict[str, Any]:
    """Process input and return output.

    This function uses the system_prompt from the runtime context to control
    the agent's behavior. The system_prompt should be passed via context_config
    when invoking the graph.

    Args:
        state: The current agent state containing query.
        runtime: Runtime context with configurable parameters.

    Returns:
        Dictionary containing the answer message.

    Raises:
        ValueError: If LLM service cannot be created or query is empty.
    """
    if not state.get("query"):
        raise ValueError("Query cannot be empty")

    # Get configurable params from runtime context
    # If context is None, use default values (should not happen if context_config is passed)
    if runtime.context is None:
        logger.warning(
            "Runtime context is None, using default ExampleContext. "
            "Make sure to pass context_config when invoking the graph."
        )
        context = ExampleContext()
    else:
        context = runtime.context

    example_context = context.example_context
    system_prompt = context.system_prompt
    role = context.role

    # Validate that system_prompt is not empty
    if not system_prompt or not system_prompt.strip():
        raise ValueError(
            "system_prompt cannot be empty. "
            "Please provide system_prompt in config file or context_config."
        )

    # 替换系统提示词中的 {role} 占位符
    try:
        formatted_system_prompt = system_prompt.format(role=role)
    except KeyError as e:
        logger.error(
            "Failed to format system_prompt: missing placeholder %s", e
        )
        formatted_system_prompt = system_prompt.replace("{role}", role)

    # Create LLM service and get model instance
    service = create_service()
    llm: Optional[BaseLanguageModel] = service.get_llm()

    if llm is None:
        raise ValueError("Failed to get LLM instance from service")

    try:
        # Get query from state
        query = state.get("query", "")
        
        # Build messages with system prompt
        # The system prompt is critical for controlling agent behavior
        messages = [
            SystemMessage(content=formatted_system_prompt),
            HumanMessage(content=query),
        ]

        logger.debug(
            "Invoking LLM with system_prompt: %s, role: %s, query: %s",
            formatted_system_prompt[:100] + "..." if len(formatted_system_prompt) > 100 else formatted_system_prompt,
            role,
            query[:100] + "..." if len(query) > 100 else query,
        )

        # 调用 LLM
        response = await llm.ainvoke(messages)

        # Extract content from response
        content = (
            response.content if hasattr(response, "content") else str(response)
        )

        logger.info(
            "Successfully processed query with system_prompt (role: %s) and context: %s",
            role,
            example_context,
        )

        return {"query": content}

    except Exception as e:
        logger.error("Error processing query: %s", str(e), exc_info=True)
        raise


def create_agent() -> StateGraph:
    """Create and configure the example agent graph.

    Returns:
        StateGraph instance ready for compilation.
    """
    agent = StateGraph(ExampleState, context_schema=ExampleContext)
    agent.add_node("call_model", call_model)
    agent.add_edge("__start__", "call_model")
    agent.add_edge("call_model", "__end__")
    return agent

