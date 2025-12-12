"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from pydantic import BaseModel
from typing_extensions import TypedDict

from src.llm import create_service

logger = logging.getLogger(__name__)


class AgentContext(BaseModel):
    """Context parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    my_configurable_param: str = "default_value"


class AgentState(TypedDict):
    """Input state for the agent.

    Defines the initial structure of incoming data.
    See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
    """

    query: str
    history: Optional[list[AnyMessage]]
    answer: Optional[AnyMessage]


async def call_model(
    state: AgentState, runtime: Runtime[AgentContext]
) -> Dict[str, Any]:
    """Process input and return output.

    Args:
        state: The current agent state containing query and history.
        runtime: Runtime context with configurable parameters.

    Returns:
        Dictionary containing the answer message.

    Raises:
        ValueError: If LLM service cannot be created or query is empty.
    """
    if not state.get("query"):
        raise ValueError("Query cannot be empty")

    # Get configurable param from runtime context
    config_param = (
        runtime.context.my_configurable_param
        if runtime.context
        else "default_value"
    )

    # Create LLM service and get model instance
    service = create_service()
    llm: Optional[BaseLanguageModel] = service.get_llm()

    if llm is None:
        raise ValueError("Failed to get LLM instance from service")

    try:
        # LangChain's ainvoke accepts a string prompt or list of messages
        response = await llm.ainvoke(state["query"])

        # Extract content from response
        content = (
            response.content if hasattr(response, "content") else str(response)
        )
        answer_text = f"{content}\n\nConfigured with: {config_param}"

        logger.info(
            "Successfully processed query with config: %s", config_param
        )

        return {"answer": answer_text}

    except Exception as e:
        logger.error("Error processing query: %s", str(e), exc_info=True)
        raise


def create_agent() -> StateGraph:
    """Create and configure the agent graph.

    Returns:
        Compiled StateGraph instance ready for execution.
    """
    agent = StateGraph(AgentState, context_schema=AgentContext)
    agent.add_node("call_model", call_model)
    agent.add_edge("__start__", "call_model")
    agent.add_edge("call_model", "__end__")
    return agent


# Define the graph
graph_demo = create_agent().compile(name="Agent Demo Graph")
