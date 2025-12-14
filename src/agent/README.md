# Agent 开发指南

本文档详细说明如何添加新的 agent 到系统中。

## 目录结构

每个 agent 应该在自己的目录下，目录结构如下：

```
src/agent/
├── example/              # 示例 agent
│   ├── __init__.py      # 模块导出
│   ├── agent.py         # Agent 图定义和节点函数
│   ├── context.py       # Context 模型定义
│   ├── state.py         # State 模型定义
│   └── prompts.py       # Prompt 模板（可选）
├── agent_manager.py     # Agent 管理器
├── agent_names.py       # Agent 名称常量
└── agents.py            # 预编译的 agent 实例（可选）
```

## 步骤 1: 创建 Agent 目录和文件

### 1.1 创建目录

在 `src/agent/` 下创建新的 agent 目录，例如 `my_agent/`。

### 1.2 创建 `state.py` - 定义 State 模型

State 定义了 agent 在处理过程中使用的数据结构。

```python
from typing import Optional
from typing_extensions import TypedDict


class MyAgentState(TypedDict):
    """Agent state definition.
    
    定义 agent 在处理过程中使用的数据结构。
    所有节点函数都会接收和返回这个 state。
    """
    query: str  # 必需字段
    context: Optional[list[str]]  # 可选字段
    # 添加其他需要的字段...
```

### 1.3 创建 `context.py` - 定义 Context 模型

Context 定义了运行时传递给所有节点函数的配置参数。**重要：Context 必须是可序列化的（只包含基本类型和字典）**。

```python
from typing import Any, Dict, Optional
from pydantic import BaseModel


class MyAgentContext(BaseModel):
    """Context parameters for the agent.
    
    Context 在运行时传递给所有节点函数。
    所有字段必须是可序列化的（基本类型、字典、列表等）。
    """
    # Agent 特定的配置
    my_config_param: str = "default_value"
    
    # LLM 配置（可选，如果 agent 需要使用 LLM）
    # 这个配置会被传递到节点函数中，用于创建 LLM 服务
    llm_config: Optional[Dict[str, Any]] = None
```

**注意：**
- Context 中的 `llm_config` 是可选的，如果 agent 不需要 LLM，可以省略
- `llm_config` 支持的键：`llm_provider`, `llm_model`, `temperature`, `max_tokens`, `api_key`, `base_url`
- 在节点函数中，`llm_model` 会被映射为 `model_name` 传递给 LLM 服务

### 1.4 创建 `prompts.py` - 定义 Prompt 模板（可选）

如果 agent 需要使用系统提示词，可以在这里定义。

```python
SYSTEM_PROMPT = "You are a helpful assistant. ..."
```

### 1.5 创建 `agent.py` - 实现 Agent 逻辑

这是核心文件，包含节点函数和 agent 图定义。

```python
"""My agent implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from src.llm import create_service  # 如果使用 LLM

from .context import MyAgentContext
from .state import MyAgentState
from .prompts import SYSTEM_PROMPT  # 如果定义了 prompts

logger = logging.getLogger(__name__)


async def my_node_function(
    state: MyAgentState, runtime: Runtime[MyAgentContext]
) -> Dict[str, Any]:
    """节点函数示例。
    
    所有节点函数必须遵循这个签名：
    - 第一个参数：state (TypedDict)
    - 第二个参数：runtime (Runtime[Context])
    - 返回值：Dict[str, Any]，用于更新 state
    
    Args:
        state: 当前 agent 状态
        runtime: 运行时上下文，包含配置参数
        
    Returns:
        包含要更新的 state 字段的字典
    """
    # 从 state 读取数据
    query = state.get("query", "")
    
    # 从 runtime.context 读取配置
    if runtime.context is not None:
        my_config = runtime.context.my_config_param
    
    # 如果需要使用 LLM，从 context 创建 LLM 服务
    if runtime.context is not None and runtime.context.llm_config:
        llm_config = runtime.context.llm_config
        if llm_config:
            service_config = {}
            
            # 传递 LLM 配置
            for key in ["model_name", "temperature", "max_tokens", "api_key", "base_url"]:
                if key in llm_config:
                    service_config[key] = llm_config[key]
            
            service = create_service(service_config)
            llm: Optional[BaseLanguageModel] = service.get_llm()
            
            if llm is not None:
                try:
                    # 使用 LLM
                    messages = [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=query),
                    ]
                    response = await llm.ainvoke(messages)
                    content = response.content if hasattr(response, "content") else str(response)
                    
                    return {"query": content}
                finally:
                    # 确保释放 LLM 服务，将其返回到缓存池
                    service.release()
    
    # 返回更新后的 state
    return {"query": "processed: " + query}


def create_agent(config: Optional[Dict[str, Any]] = None) -> StateGraph:
    """创建并配置 agent 图。
    
    Args:
        config: 可选的配置字典。支持的键：
            - llm_provider: LLM 提供商名称
            - llm_model: 模型名称
            - temperature: 采样温度
            - max_tokens: 最大 token 数
            - api_key: API 密钥
            - base_url: API 基础 URL
            - 其他 agent 特定的配置键
            
    Returns:
        准备好编译的 StateGraph 实例
    """
    # 创建 StateGraph，指定 state 和 context schema
    agent = StateGraph(MyAgentState, context_schema=MyAgentContext)
    
    # 添加节点
    agent.add_node("my_node", my_node_function)
    # agent.add_node("another_node", another_node_function)
    
    # 添加边（定义节点之间的流程）
    agent.add_edge("__start__", "my_node")
    # agent.add_edge("my_node", "another_node")
    agent.add_edge("my_node", "__end__")
    
    return agent
```

**关键点：**
- 节点函数必须是 `async` 函数
- 节点函数签名：`async def node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- 返回值是字典，用于更新 state
- 如果需要使用 LLM，从 `runtime.context.llm_config` 读取配置并创建服务

### 1.6 创建 `__init__.py` - 模块导出

```python
"""My agent module.

This module provides the my agent implementation.
"""

from .agent import create_agent
from .context import MyAgentContext
from .state import MyAgentState

__all__ = ["create_agent", "MyAgentContext", "MyAgentState"]
```

## 步骤 2: 注册 Agent

### 2.1 在 `agent_names.py` 中添加 Agent 名称常量

```python
EXAMPLE_AGENT = "example"
MY_AGENT = "my_agent"  # 添加新行
```

### 2.2 在 `agent_manager.py` 中注册 Agent 工厂

#### 2.2.1 更新 `_get_agent_factory` 函数

在 `_get_agent_factory` 函数中添加新的 agent：

```python
def _get_agent_factory(name: str) -> Callable[[Optional[Dict[str, Any]]], StateGraph]:
    """Get the factory function for creating an agent by name."""
    # Import agent modules dynamically
    if name == "example":
        from src.agent.example import create_agent
        return create_agent
    elif name == "my_agent":  # 添加新分支
        from src.agent.my_agent import create_agent
        return create_agent
    else:
        raise ValueError(f"Unknown agent name: {name}")
```

#### 2.2.2 更新 `_register_known_agents` 方法（可选）

如果希望在初始化时自动注册，可以在 `_register_known_agents` 中添加：

```python
def _register_known_agents(self) -> None:
    """Register known agent factories."""
    try:
        from src.agent import agent_names
        # Register example agent factory
        if hasattr(agent_names, "EXAMPLE_AGENT"):
            self._agent_factories[agent_names.EXAMPLE_AGENT] = _get_agent_factory(
                agent_names.EXAMPLE_AGENT
            )
        # 添加新 agent 注册
        if hasattr(agent_names, "MY_AGENT"):
            self._agent_factories[agent_names.MY_AGENT] = _get_agent_factory(
                agent_names.MY_AGENT
            )
    except Exception as e:
        logger.warning(f"Failed to register known agents: {e}")
```

#### 2.2.3 更新 `create_compiled_agent_by_name` 方法

在 `create_compiled_agent_by_name` 方法中添加 context config 构建逻辑：

```python
# Build context config from the config dict
context_config: Dict[str, Any] = {}
if name == "example":
    # ... existing code ...
elif name == "my_agent":  # 添加新分支
    # Map config to context fields
    context_config = {
        "my_config_param": config.get("my_config_param", "default_value")
    }
    
    # Extract LLM configuration from agent config
    llm_config = {}
    for key in ["llm_provider", "llm_model", "temperature", "max_tokens", "api_key", "base_url"]:
        if key in config:
            llm_config[key] = config[key]
    
    # Store LLM config in context_config
    context_config["llm_config"] = llm_config if llm_config else {}
```

## 步骤 3: 创建 Agent 实例（可选）

在 `src/agents.py` 中创建预编译的 agent 实例：

```python
from src.agent.agent_manager import get_agent_manager
from src.agent import agent_names

manager = get_agent_manager()

# Example agent
agent_example, _ = manager.create_compiled_agent_by_name(
    name=agent_names.EXAMPLE_AGENT,
    config={},
    graph_name=agent_names.EXAMPLE_AGENT,
)

# My agent
agent_my, _ = manager.create_compiled_agent_by_name(
    name=agent_names.MY_AGENT,
    config={
        "llm_model": "gpt-4",
        "temperature": 0.7,
        "my_config_param": "custom_value"
    },
    graph_name=agent_names.MY_AGENT,
)
```

## 完整示例

以下是一个完整的示例，展示如何创建一个简单的问答 agent：

### `my_agent/state.py`
```python
from typing import Optional
from typing_extensions import TypedDict


class QAAgentState(TypedDict):
    question: str
    answer: Optional[str]
```

### `my_agent/context.py`
```python
from typing import Any, Dict, Optional
from pydantic import BaseModel


class QAAgentContext(BaseModel):
    """Context for QA agent."""
    llm_config: Optional[Dict[str, Any]] = None
```

### `my_agent/agent.py`
```python
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from src.llm import create_service

from .context import QAAgentContext
from .state import QAAgentState

logger = logging.getLogger(__name__)


async def answer_question(
    state: QAAgentState, runtime: Runtime[QAAgentContext]
) -> Dict[str, Any]:
    """Answer the question using LLM."""
    question = state.get("question", "")
    
    # Get LLM config from context
    service_config = None
    if runtime.context and runtime.context.llm_config:
        llm_config = runtime.context.llm_config
        if llm_config:
            service_config = {}
            if "llm_model" in llm_config:
                service_config["model_name"] = llm_config["llm_model"]
            for key in ["temperature", "max_tokens", "api_key", "base_url"]:
                if key in llm_config:
                    service_config[key] = llm_config[key]
    
    # Create LLM service
    service = create_service(service_config)
    llm = service.get_llm()
    
    if llm is None:
        raise ValueError("Failed to create LLM")
    
    try:
        # Invoke LLM
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=question),
        ]
        response = await llm.ainvoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)
        
        return {"answer": answer}
    finally:
        # Always release LLM service to return it to the cache pool
        service.release()


def create_agent(config: Dict[str, Any] | None = None) -> StateGraph:
    """Create QA agent graph."""
    agent = StateGraph(QAAgentState, context_schema=QAAgentContext)
    agent.add_node("answer_question", answer_question)
    agent.add_edge("__start__", "answer_question")
    agent.add_edge("answer_question", "__end__")
    return agent
```

## 最佳实践

1. **保持 Context 可序列化**：Context 中的所有字段必须是可序列化的（基本类型、字典、列表等），不要存储对象引用。

2. **使用 LLM 配置**：如果 agent 需要使用 LLM，在 context 中存储 `llm_config` 字典，在节点函数中根据配置创建 LLM 服务。

3. **释放 LLM 资源**：**重要**：在节点函数中使用完 LLM 后，必须调用 `service.release()` 释放资源。使用 `try/finally` 确保即使发生异常也能释放：

```python
service = create_service(service_config)
llm = service.get_llm()
try:
    # 使用 LLM
    response = await llm.ainvoke(messages)
    return {"result": response.content}
finally:
    service.release()  # 确保释放
```

4. **错误处理**：在节点函数中添加适当的错误处理和日志记录。

4. **类型提示**：使用完整的类型提示，提高代码可读性和可维护性。

5. **文档字符串**：为所有函数和类添加清晰的文档字符串。

6. **测试**：为新的 agent 编写测试用例。

## 常见问题

### Q: 如何在节点函数之间传递数据？
A: 通过 state。每个节点函数接收 state，返回包含更新字段的字典。

### Q: 如何访问配置参数？
A: 通过 `runtime.context`。Context 在运行时传递给所有节点函数。

### Q: 如何创建 LLM 服务？
A: 从 `runtime.context.llm_config` 读取配置，转换为 LLM 服务配置格式，然后调用 `create_service(service_config)`。

### Q: 如何确保 LLM 服务被正确释放？
A: **重要**：在节点函数中使用 LLM 服务后，必须调用 `service.release()` 将其返回到缓存池。推荐使用 `try/finally` 确保即使发生异常也能释放：

```python
service = create_service(service_config)
llm = service.get_llm()
try:
    # 使用 LLM
    response = await llm.ainvoke(messages)
    return {"result": response.content}
finally:
    # 确保释放 LLM 服务
    service.release()
```

这样可以确保 LLM 对象被正确返回到管理器，避免资源泄漏。

### Q: Context 和 State 的区别是什么？
A: 
- **State**: 在节点之间传递的数据，会随着处理流程变化
- **Context**: 运行时配置参数，在整个执行过程中保持不变

### Q: 如何调试 agent？
A: 使用日志记录。所有节点函数都应该记录关键操作和错误。

## 参考

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- 示例 agent: `src/agent/example/`

