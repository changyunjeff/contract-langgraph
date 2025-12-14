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
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def call_model(
    state: ExampleState, runtime: Runtime[ExampleContext]
) -> Dict[str, Any]:
    """Process input and return output.

    This function uses the system_prompt from the runtime context to control
    the agent's behavior.

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

    example_context = ""
    if runtime.context is not None:
        example_context = runtime.context.example_context

    # Create LLM service from config in context
    # Convert agent config format to LLM service config format
    service_config = None
    if runtime.context is not None and runtime.context.llm_config:
        llm_config = runtime.context.llm_config
        if llm_config:  # Only process if config is not empty
            service_config = {}
            
            # Pass through LLM-related config
            for key in ["model_name", "temperature", "max_tokens", "api_key", "base_url"]:
                if key in llm_config:
                    service_config[key] = llm_config[key]
    
    # Create LLM service and get model instance
    # If service_config is None or empty, create_service will use defaults
    service = create_service(service_config)
    llm = service.get_llm()
    
    if llm is None:
        logger.error("Failed to create LLM from service")
        raise ValueError("Failed to create LLM from service")

    try:
        # Get query from state
        query = state.get("query", "")

        if query == "":
            raise ValueError("Query cannot be empty")
        
        # Build messages with system prompt
        # The system prompt is critical for controlling agent behavior
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]

        logger.debug(
            "Invoking LLM with system_prompt: %s, context: %s, query: %s",
            SYSTEM_PROMPT[:100] + "..." if len(SYSTEM_PROMPT) > 100 else SYSTEM_PROMPT,
            example_context,
            query[:100] + "..." if len(query) > 100 else query,
        )

        # 调用 LLM
        response = await llm.ainvoke(messages)

        # Extract content from response
        content = (
            response.content if hasattr(response, "content") else str(response)
        )

        logger.info(
            "Successfully processed query with system_prompt and context: %s",
            example_context,
        )

        return {"query": content}

    except ValueError as e:
        logger.error("ValueError in call_model: %s", str(e))
        raise e
    except Exception as e:
        logger.error("Error processing query: %s", str(e), exc_info=True)
        raise
    finally:
        # Always release LLM service to return it to the cache pool
        service.release()
        logger.debug("Released LLM service")

async def load_context(
    state: ExampleState, runtime: Runtime[ExampleContext]
) -> Dict[str, Any]:
    """Load context from runtime to state.
    
    This function loads context parameters from the runtime context
    into the agent state for use in subsequent nodes.
    
    Args:
        state: The current agent state.
        runtime: Runtime context with configurable parameters.
    
    Returns:
        Dictionary containing updated state with context information.
    """
    context_list = []
    
    # Extract context from runtime if available
    if runtime.context is not None:
        example_context = runtime.context.example_context
        if example_context:
            # Convert context string to list if needed
            # You can customize this logic based on your needs
            context_list = [example_context] if isinstance(example_context, str) else example_context
    
    logger.debug(f"Loaded context: {context_list}")
    
    return {"context": context_list}

def create_agent(config: Optional[Dict[str, Any]] = None) -> StateGraph:
    """Create and configure the example agent graph.

    Args:
        config: Optional configuration dictionary. Supported keys:
            - llm_provider: LLM provider name (e.g., "openai")
            - llm_model: Model name (e.g., "gpt-sonnet-3-5")
            - temperature: Sampling temperature
            - max_tokens: Maximum tokens to generate
            - api_key: API key for LLM service
            - base_url: Base URL for LLM API
            - example_context: Example context string

    Returns:
        StateGraph instance ready for compilation.
    """
    agent = StateGraph(ExampleState, context_schema=ExampleContext)
    agent.add_node("load_context", load_context)
    agent.add_node("call_model", call_model)
    agent.add_edge("__start__", "load_context")
    agent.add_edge("load_context", "call_model")
    agent.add_edge("call_model", "__end__")
    return agent

