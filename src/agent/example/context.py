from pydantic import BaseModel


class ExampleContext(BaseModel):
    """Context parameters for the agent.
    
    These parameters are configurable and can be set via:
    1. JSON config file (config.example.json)
    2. config parameter when creating agent
    3. context_config when invoking the graph
    
    The system_prompt will be used to control the agent's behavior.
    """
    example_context: str = "this is an example context from config file"
    system_prompt: str = "你是一个{role}，你只能回答数学相关的问题，如果用户提问数学以外的问题，请拒绝回答。"
    role: str = "数学专家"
