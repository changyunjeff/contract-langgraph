from typing import Any, Dict, Optional

from pydantic import BaseModel


class ExampleContext(BaseModel):
    """Context parameters for the agent.
    
    This context is passed to all node functions at runtime.
    """
    example_context: str = "this is an example context from config file"
    # LLM configuration dictionary (will be used to create LLM in nodes)
    # Keys: llm_model, temperature, max_tokens, api_key, base_url
    llm_config: Optional[Dict[str, Any]] = None
