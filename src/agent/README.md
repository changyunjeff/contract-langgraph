# 🤖 Agent 服务使用指南

**灵活、可扩展的 LangGraph Agent 管理框架**

---

## 📖 简介

Agent 服务模块提供了一个统一的接口，用于管理和使用 LangGraph Agent。该模块采用单例管理器模式，实现了 Agent 的注册、创建和生命周期管理。每个 Agent 都有唯一的 ID（基于名称和配置的哈希值），确保相同配置的 Agent 不会重复注册。

<div class="feature-box">

### ✨ 核心特性

- **统一管理**：全局单例管理器统一管理所有 Agent
- **唯一标识**：基于名称和配置自动生成唯一 Agent ID
- **配置管理**：支持 JSON 配置文件或字典配置
- **自动去重**：相同配置的 Agent 自动复用，避免重复注册
- **线程安全**：多线程环境下安全使用
- **灵活扩展**：轻松添加新的 Agent 类型

</div>

---

## 🚀 快速开始

### 基础使用（自动注册，推荐）

<div class="success">

**✅ 推荐方式：** 使用自动注册功能，直接通过名称和配置创建 Agent，无需手动注册。

</div>

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

# 获取单例管理器（默认启用自动注册）
manager = get_agent_manager()

# 直接创建 Agent（如果未注册会自动注册）
agent_graph = manager.create_agent_by_name(
    name=EXAMPLE_AGENT,
    config={"example_context": "custom context"}
)
compiled_graph = agent_graph.compile(name="Example Agent")

# 使用 Agent
result = await compiled_graph.ainvoke({"query": "Hello, world!"})
print(result)
```

### 使用配置文件（自动注册，推荐）

<div class="success">

**✅ 推荐方式：** 使用 `create_compiled_agent_by_name()` 方法，自动加载配置文件并获取 context config。

</div>

<div class="warning">

**⚠️ 重要提示：** 使用配置文件时，**必须**传递 `context_config` 给 `ainvoke()` 或 `invoke()`，否则配置文件中的 `system_prompt`、`role` 等参数**不会生效**！

</div>

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

manager = get_agent_manager()

# 使用配置文件创建已编译的 Agent 并获取 context config（推荐）
compiled_graph, context_config = manager.create_compiled_agent_by_name(
    name=EXAMPLE_AGENT,
    config_path="src/agent/example/config.example.json",
    graph_name="Example Agent"
)

# 使用 Agent（必须传递 context_config 以使用配置文件中的系统提示词等）
# 如果不传递 context_config，system_prompt 将不会生效！
result = await compiled_graph.ainvoke(
    {"query": "Hello, world!"},
    config=context_config  # <-- 这是必需的！
)
print(result)
```

### 使用配置文件（手动方式）

如果需要手动控制编译过程：

<div class="warning">

**⚠️ 重要提示：** 必须获取并传递 `context_config`，否则 `system_prompt` 不会生效！

</div>

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

manager = get_agent_manager()

# 使用 JSON 配置文件直接创建（自动注册）
agent_graph = manager.create_agent_by_name(
    name=EXAMPLE_AGENT,
    config={},  # 可以覆盖配置文件中的值
    config_path="src/agent/example/config.example.json"
)
compiled_graph = agent_graph.compile(name="Example Agent")

# 获取 context config（包含配置文件中的系统提示词等）
# 需要先计算 agent_id（基于合并后的配置）
merged_config = {}  # 如果提供了 config，需要合并
# 实际使用中，应该从配置文件加载并合并
import json
from pathlib import Path
config_path = Path("src/agent/example/config.example.json")
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        merged_config = json.load(f)
        merged_config.update({})  # 合并提供的 config

agent_id = manager._compute_agent_id(EXAMPLE_AGENT, merged_config)
context_config = manager.get_context_config(agent_id)

# 使用 Agent（必须传递 context_config，否则 system_prompt 不会生效）
result = await compiled_graph.ainvoke(
    {"query": "Hello, world!"},
    config=context_config  # <-- 这是必需的！
)
```

### 手动注册方式（传统方式）

如果需要更精细的控制，可以手动注册：

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

# 获取单例管理器
manager = get_agent_manager()

# 手动注册 Agent
agent_id = manager.register(
    name=EXAMPLE_AGENT,
    config={"example_context": "custom context"}
)

# 创建 Agent
agent_graph = manager.create_agent(agent_id)
compiled_graph = agent_graph.compile(name="Example Agent")

# 使用 Agent
result = await compiled_graph.ainvoke({"query": "Hello, world!"})
print(result)
```

---

## 📚 API 参考

### get_agent_manager()

获取全局 Agent 管理器单例实例。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `auto_register` | `bool` | 是否启用自动注册 | `True` |

**返回值：** `AgentManager` - 管理器实例

**示例：**

```python
from src.agent.agent_manager import get_agent_manager

# 启用自动注册（默认）
manager = get_agent_manager()

# 禁用自动注册
manager = get_agent_manager(auto_register=False)
```

### AgentManager.register()

注册一个 Agent。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `name` | `str` | Agent 名称（如 "example"） | 必填 |
| `config` | `Dict[str, Any]` | Agent 配置字典 | 必填 |
| `config_path` | `str \| None` | JSON 配置文件路径 | `None` |
| `create_func` | `Callable[[], StateGraph] \| None` | 自定义创建函数 | `None` |
| `skip_file_load` | `bool` | 是否跳过文件加载（内部使用） | `False` |

**返回值：** `str` - Agent 的唯一 ID

**示例：**

```python
agent_id = manager.register(
    name="example",
    config={"example_context": "my context"},
    config_path="path/to/config.json"
)
```

### AgentManager.create_agent_by_name()

根据名称和配置直接创建 Agent 实例（推荐方式）。

如果启用了自动注册且 Agent 未注册，会自动注册后再创建。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `name` | `str` | Agent 名称（如 "example"） | 必填 |
| `config` | `Dict[str, Any] \| None` | Agent 配置字典 | `{}` |
| `config_path` | `str \| None` | JSON 配置文件路径 | `None` |

**返回值：** `StateGraph` - 未编译的 Agent 图

**示例：**

```python
# 直接创建 Agent（自动注册）
agent_graph = manager.create_agent_by_name(
    name="example",
    config={"example_context": "my context"}
)
compiled_graph = agent_graph.compile(name="My Agent")

# 使用配置文件
agent_graph = manager.create_agent_by_name(
    name="example",
    config_path="path/to/config.json"
)
compiled_graph = agent_graph.compile(name="My Agent")
```

### AgentManager.create_compiled_agent_by_name()

创建已编译的 Agent 并获取 context config（推荐方式）。

这是一个便捷方法，它会创建 Agent、编译它，并返回编译后的图和 context config。

<div class="warning">

**⚠️ 重要：** 返回的 `context_config` **必须**传递给 `ainvoke()` 或 `invoke()`，否则配置文件中的 `system_prompt` 等参数不会生效！

</div>

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `name` | `str` | Agent 名称（如 "example"） | 必填 |
| `config` | `Dict[str, Any] \| None` | Agent 配置字典 | `{}` |
| `config_path` | `str \| None` | JSON 配置文件路径 | `None` |
| `graph_name` | `str \| None` | 编译后的图名称 | `name` |

**返回值：** `Tuple[CompiledGraph, Dict[str, Any]]` - (编译后的图, context config)

**示例：**

```python
# 使用配置文件创建并获取 context config
compiled_graph, context_config = manager.create_compiled_agent_by_name(
    name="example",
    config_path="src/agent/example/config.example.json",
    graph_name="Example Agent"
)

# 使用 Agent（必须传递 context_config，否则 system_prompt 不会生效）
result = await compiled_graph.ainvoke(
    {"query": "Hello, world!"},
    config=context_config  # <-- 这是必需的！
)
```

### AgentManager.create_agent()

根据 Agent ID 创建 Agent 实例（需要先注册）。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `agent_id` | `str` | Agent 的唯一 ID | 必填 |

**返回值：** `StateGraph` - 未编译的 Agent 图

**示例：**

```python
agent_graph = manager.create_agent(agent_id)
compiled_graph = agent_graph.compile(name="My Agent")
```

### AgentManager.get_agent_ids_by_name()

根据名称获取所有相关的 Agent ID。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `name` | `str` | Agent 名称 | 必填 |

**返回值：** `List[str]` - Agent ID 列表

### AgentManager.get_agent_entry()

获取 Agent 的详细信息。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `agent_id` | `str` | Agent 的唯一 ID | 必填 |

**返回值：** `Optional[AgentEntry]` - Agent 条目信息

### AgentManager.is_registered()

检查 Agent 是否已注册。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `agent_id` | `str` | Agent 的唯一 ID | 必填 |

**返回值：** `bool` - 是否已注册

### AgentManager.enable_auto_register()

启用自动注册功能。

**示例：**

```python
manager.enable_auto_register()
```

### AgentManager.disable_auto_register()

禁用自动注册功能。

**示例：**

```python
manager.disable_auto_register()
```

### AgentManager.is_auto_register_enabled()

检查自动注册是否启用。

**返回值：** `bool` - 是否启用自动注册

**示例：**

```python
if manager.is_auto_register_enabled():
    print("Auto-register is enabled")
```

### AgentManager.get_stats()

获取管理器统计信息。

**返回值：** `Dict[str, Any]` - 统计信息字典，包含：
- `registered_agents`: 已注册的 Agent 数量
- `agents_by_name`: 按名称分组的 Agent 数量
- `auto_register`: 自动注册是否启用

---

## 🛠️ 添加新的 Agent

本节详细说明如何添加一个新的 Agent 类型。

### 步骤 1：创建 Agent 目录结构

在 `src/agent/` 目录下创建新的 Agent 目录，例如 `my_agent/`：

```
src/agent/
└── my_agent/
    ├── __init__.py
    ├── agent.py
    ├── state.py
    ├── context.py
    └── config.example.json  # 可选
```

### 步骤 2：定义 State

在 `state.py` 中定义 Agent 的状态结构：

```python
# src/agent/my_agent/state.py
from typing_extensions import TypedDict
from typing import Optional
from langchain_core.messages import AnyMessage


class MyAgentState(TypedDict):
    """Input state for the agent.
    
    Defines the initial structure of incoming data.
    """
    query: str
    history: Optional[list[AnyMessage]]
    answer: Optional[str]
```

### 步骤 3：定义 Context

在 `context.py` 中定义 Agent 的上下文参数：

```python
# src/agent/my_agent/context.py
from pydantic import BaseModel


class MyAgentContext(BaseModel):
    """Context parameters for the agent.
    
    Set these when creating assistants OR when invoking the graph.
    """
    my_param: str = "default_value"
    temperature: float = 0.7
```

### 步骤 4：实现 Agent 逻辑

在 `agent.py` 中实现 Agent 的核心逻辑：

```python
# src/agent/my_agent/agent.py
"""My agent implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from src.llm import create_service

from .context import MyAgentContext
from .state import MyAgentState

logger = logging.getLogger(__name__)


async def my_node(
    state: MyAgentState, runtime: Runtime[MyAgentContext]
) -> Dict[str, Any]:
    """Process input and return output.
    
    Args:
        state: The current agent state.
        runtime: Runtime context with configurable parameters.
    
    Returns:
        Dictionary containing the updated state.
    """
    if not state.get("query"):
        raise ValueError("Query cannot be empty")
    
    # 从 runtime context 获取配置参数
    my_param = (
        runtime.context.my_param
        if runtime.context
        else "default_value"
    )
    
    # 创建 LLM 服务
    service = create_service()
    llm: Optional[BaseLanguageModel] = service.get_llm()
    
    if llm is None:
        raise ValueError("Failed to get LLM instance from service")
    
    try:
        # 调用 LLM
        response = await llm.ainvoke(state["query"])
        
        # 提取内容
        content = (
            response.content if hasattr(response, "content") else str(response)
        )
        
        logger.info("Successfully processed query with param: %s", my_param)
        
        return {"answer": content}
    
    except Exception as e:
        logger.error("Error processing query: %s", str(e), exc_info=True)
        raise


def create_agent() -> StateGraph:
    """Create and configure the agent graph.
    
    Returns:
        StateGraph instance ready for compilation.
    """
    agent = StateGraph(MyAgentState, context_schema=MyAgentContext)
    agent.add_node("my_node", my_node)
    agent.add_edge("__start__", "my_node")
    agent.add_edge("my_node", "__end__")
    return agent
```

### 步骤 5：导出模块

在 `__init__.py` 中导出必要的组件：

```python
# src/agent/my_agent/__init__.py
"""My agent module."""

from .agent import create_agent
from .context import MyAgentContext
from .state import MyAgentState

__all__ = ["create_agent", "MyAgentContext", "MyAgentState"]
```

### 步骤 6：添加 Agent 名称常量

在 `agent_names.py` 中添加新的 Agent 名称常量：

```python
# src/agent/agent_names.py
EXAMPLE_AGENT = "example"
MY_AGENT = "my_agent"  # 新增
```

### 步骤 7：创建配置文件（可选）

创建 `config.example.json` 作为配置模板：

```json
{
  "my_param": "custom value",
  "temperature": 0.7,
  "model_name": "gpt-3.5-turbo"
}
```

### 步骤 8：使用新 Agent

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import MY_AGENT

manager = get_agent_manager()

# 注册新 Agent
agent_id = manager.register(
    name=MY_AGENT,
    config={"my_param": "custom value"},
    config_path="src/agent/my_agent/config.example.json"
)

# 创建并使用
agent_graph = manager.create_agent(agent_id)
compiled_graph = agent_graph.compile(name="My Agent")

result = await compiled_graph.ainvoke({
    "query": "Hello from my agent!"
})
```

---

## 💡 使用示例

### 示例 1：基础 Agent 使用（自动注册）

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

# 获取管理器（默认启用自动注册）
manager = get_agent_manager()

# 直接创建 Agent（自动注册）
agent_graph = manager.create_agent_by_name(
    name=EXAMPLE_AGENT,
    config={"example_context": "Hello, Agent!"}
)
compiled_graph = agent_graph.compile(name="Example Agent")

# 获取 context config（如果使用了配置文件，必须传递以使用系统提示词等）
agent_id = manager._compute_agent_id(EXAMPLE_AGENT, {"example_context": "Hello, Agent!"})
context_config = manager.get_context_config(agent_id)

# 调用 Agent（传递 context_config 以使用配置）
result = await compiled_graph.ainvoke(
    {"query": "What is LangGraph?"},
    config=context_config
)

print(result)
```

### 示例 2：使用配置文件（自动注册，推荐）

<div class="warning">

**⚠️ 重要：** 必须传递 `context_config`，否则 `system_prompt` 不会生效！

</div>

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

manager = get_agent_manager()

# 从配置文件直接创建并获取 context config（推荐方式）
compiled_graph, context_config = manager.create_compiled_agent_by_name(
    name=EXAMPLE_AGENT,
    config_path="src/agent/example/config.example.json",
    graph_name="Example Agent"
)

# 使用 Agent（必须传递 context_config 以使用配置文件中的系统提示词等）
# 配置文件中的 system_prompt 会控制 Agent 行为（例如：只回答数学问题）
result = await compiled_graph.ainvoke(
    {"query": "What is 2+2?"},
    config=context_config  # <-- 必须传递，否则 system_prompt 不会生效
)
print(result)

# 测试非数学问题（应该被拒绝）
result = await compiled_graph.ainvoke(
    {"query": "What is the capital of France?"},
    config=context_config  # <-- 必须传递
)
# 根据 system_prompt，Agent 应该拒绝回答非数学问题

# 或者覆盖部分配置
compiled_graph, context_config = manager.create_compiled_agent_by_name(
    name=EXAMPLE_AGENT,
    config={"role": "物理专家"},  # 覆盖文件中的 role 值
    config_path="src/agent/example/config.example.json",
    graph_name="Example Agent"
)

result = await compiled_graph.ainvoke(
    {"query": "What is 2+2?"},
    config=context_config  # <-- 必须传递
)
```

### 示例 2b：控制自动注册

```python
from src.agent.agent_manager import get_agent_manager

# 禁用自动注册
manager = get_agent_manager(auto_register=False)

# 或者运行时控制
manager.disable_auto_register()  # 禁用
manager.enable_auto_register()   # 启用

# 检查状态
if manager.is_auto_register_enabled():
    # 可以直接创建，会自动注册
    agent_graph = manager.create_agent_by_name(
        name="example",
        config={"example_context": "test"}
    )
else:
    # 需要先手动注册
    agent_id = manager.register(
        name="example",
        config={"example_context": "test"}
    )
    agent_graph = manager.create_agent(agent_id)
```

### 示例 3：多个相同名称的 Agent

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

manager = get_agent_manager()

# 注册多个不同配置的 Agent（相同名称）
agent_id_1 = manager.register(
    name=EXAMPLE_AGENT,
    config={"example_context": "config 1"}
)

agent_id_2 = manager.register(
    name=EXAMPLE_AGENT,
    config={"example_context": "config 2"}
)

# 获取所有同名 Agent 的 ID
all_ids = manager.get_agent_ids_by_name(EXAMPLE_AGENT)
print(f"Found {len(all_ids)} agents with name '{EXAMPLE_AGENT}'")

# 使用不同的 Agent
for agent_id in all_ids:
    agent_graph = manager.create_agent(agent_id)
    compiled_graph = agent_graph.compile(name=f"Agent {agent_id}")
    # 使用 compiled_graph...
```

### 示例 4：检查 Agent 状态

```python
from src.agent.agent_manager import get_agent_manager

manager = get_agent_manager()

agent_id = manager.register(
    name="example",
    config={"example_context": "test"}
)

# 检查是否已注册
if manager.is_registered(agent_id):
    print(f"Agent {agent_id} is registered")

# 获取 Agent 详细信息
entry = manager.get_agent_entry(agent_id)
if entry:
    print(f"Agent name: {entry.name}")
    print(f"Agent config: {entry.config}")
    print(f"Created at: {entry.created_at}")

# 获取统计信息
stats = manager.get_stats()
print(f"Total registered agents: {stats['registered_agents']}")
print(f"Agents by name: {stats['agents_by_name']}")
```

### 示例 5：自定义创建函数

```python
from src.agent.agent_manager import get_agent_manager
from langgraph.graph import StateGraph
from typing_extensions import TypedDict

# 定义简单的 State
class SimpleState(TypedDict):
    message: str

# 定义自定义创建函数
def create_custom_agent() -> StateGraph:
    def simple_node(state: SimpleState):
        return {"message": f"Processed: {state['message']}"}
    
    agent = StateGraph(SimpleState)
    agent.add_node("process", simple_node)
    agent.add_edge("__start__", "process")
    agent.add_edge("process", "__end__")
    return agent

# 使用自定义创建函数注册
manager = get_agent_manager()
agent_id = manager.register(
    name="custom",
    config={"custom_param": "value"},
    create_func=create_custom_agent
)

# 创建 Agent
agent_graph = manager.create_agent(agent_id)
compiled_graph = agent_graph.compile(name="Custom Agent")
```

### 示例 6：在 Agent 中使用工具

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT
from langchain_core.tools import tool

# 定义工具
@tool
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

# 在 Agent 的节点函数中使用工具
# (需要在 agent.py 的节点函数中实现工具调用逻辑)
# 参考 src/llm/README.md 中的工具绑定示例

manager = get_agent_manager()
agent_id = manager.register(
    name=EXAMPLE_AGENT,
    config={"example_context": "with tools"}
)

agent_graph = manager.create_agent(agent_id)
compiled_graph = agent_graph.compile(name="Agent with Tools")
```

---

## 🔑 理解 Context Config 和 System Prompt

### 为什么必须传递 context_config？

LangGraph 使用 **configurable context** 机制来传递运行时参数。这些参数（如 `system_prompt`、`role` 等）必须通过 `config` 参数传递给 `ainvoke()` 或 `invoke()`。

**关键点：**
1. **配置文件中的参数不会自动生效**：即使你在配置文件中定义了 `system_prompt`，如果不通过 `context_config` 传递，Agent 将使用 `context.py` 中的默认值。
2. **system_prompt 控制 Agent 行为**：`system_prompt` 是控制 Agent 行为的关键参数。例如，在 `config.example.json` 中定义的 `system_prompt` 要求 Agent 只回答数学问题，拒绝其他问题。
3. **context_config 的格式**：`context_config` 是一个字典，格式为 `{"configurable": {...}}`，其中包含所有需要在运行时传递给 Agent 的参数。

### 正确使用示例

```python
from src.agent.agent_manager import get_agent_manager
from src.agent.agent_names import EXAMPLE_AGENT

manager = get_agent_manager()

# 创建 Agent 并获取 context_config
compiled_graph, context_config = manager.create_compiled_agent_by_name(
    name=EXAMPLE_AGENT,
    config_path="src/agent/example/config.example.json",
    graph_name="Example Agent"
)

# ✅ 正确：传递 context_config
result = await compiled_graph.ainvoke(
    {"query": "What is 2+2?"},
    config=context_config  # system_prompt 会生效
)

# ❌ 错误：不传递 context_config
result = await compiled_graph.ainvoke(
    {"query": "What is 2+2?"}
    # 没有传递 config，system_prompt 不会生效，使用默认值
)
```

### context_config 的内容

`context_config` 包含从配置文件中提取的、在 `context.py` 中定义的所有字段：

```python
# config.example.json
{
  "example_context": "this is an example context from config file",
  "system_prompt": "你是一个{role}，你只能回答数学相关的问题...",
  "role": "数学专家"
}

# context_config 的内容（由 get_context_config 生成）
{
  "configurable": {
    "example_context": "this is an example context from config file",
    "system_prompt": "你是一个{role}，你只能回答数学相关的问题...",
    "role": "数学专家"
  }
}
```

### system_prompt 中的占位符

`system_prompt` 可以包含占位符（如 `{role}`），这些占位符会在运行时被替换为 `context` 中对应的值：

```python
# config.example.json
{
  "system_prompt": "你是一个{role}，你只能回答数学相关的问题。",
  "role": "数学专家"
}

# 在 agent.py 中，system_prompt 会被格式化为：
# "你是一个数学专家，你只能回答数学相关的问题。"
```

---

## ⚠️ 注意事项

<div class="warning">

**⚠️ 重要提示：**

- Agent ID 是基于名称和配置的哈希值生成的，相同配置会生成相同的 ID
- 相同配置的 Agent 不会重复注册，会返回已存在的 Agent ID
- 自动注册功能默认启用，可以通过 `get_agent_manager(auto_register=False)` 或 `disable_auto_register()` 关闭
- 使用 `create_agent_by_name()` 时，如果启用了自动注册且 Agent 未注册，会自动注册
- **🔴 关键：使用配置文件时，必须传递 context_config 给 `ainvoke()` 或 `invoke()`，否则配置文件中的 `system_prompt`、`role` 等配置不会生效！**
  - 如果不传递 `context_config`，Agent 将使用 `context.py` 中的默认值，而不是配置文件中的值
  - 这会导致 `system_prompt` 无法控制 Agent 的行为（例如，无法拒绝非数学问题）
- 推荐使用 `create_compiled_agent_by_name()` 方法，它会自动返回编译后的图和 context config
- 确保 Agent 模块路径正确：`src.agent.{name}.agent`
- 确保 Agent 模块中有 `create_agent()` 函数
- 配置文件路径使用相对路径或绝对路径均可
- `system_prompt` 中的 `{role}` 占位符会被自动替换为 `role` 配置的值

</div>

<div class="info">

**ℹ️ 最佳实践：**

1. **使用自动注册**：推荐使用 `create_agent_by_name()` 方法，简化使用流程
2. **命名规范**：使用小写字母和下划线命名 Agent（如 `my_agent`）
3. **配置管理**：优先使用 JSON 配置文件，便于管理和版本控制
4. **状态设计**：State 应该包含 Agent 所需的所有输入和输出字段
5. **上下文设计**：Context 应该包含可配置的参数，而不是固定的业务逻辑
6. **错误处理**：在节点函数中添加适当的错误处理和日志记录
7. **资源管理**：使用 LLM 服务时，注意资源释放（LLM 服务会自动管理）

</div>

---

## 🏗️ 架构说明

Agent 服务模块采用单例管理器模式：

1. **Manager 层**：全局单例 `AgentManager`，负责 Agent 的注册、创建和生命周期管理
2. **Agent 层**：各个 Agent 模块实现具体的业务逻辑
3. **State/Context 层**：定义 Agent 的状态结构和上下文参数

<div class="feature-box">

### 工作流程

1. **注册阶段**（手动或自动）：
   - 手动：调用 `register()` 注册 Agent
   - 自动：调用 `create_agent_by_name()` 时，如果启用了自动注册且 Agent 未注册，会自动注册
   - 管理器计算 Agent ID（name + config 的哈希值）
   - 如果已存在相同 ID，直接返回现有 ID
   - 否则创建新的 `AgentEntry` 并存储

2. **创建阶段**：
   - 方式一：调用 `create_agent_by_name(name, config)` - 推荐，支持自动注册
   - 方式二：调用 `create_agent(agent_id)` - 需要先注册
   - 管理器查找对应的 `AgentEntry`（如果未注册且启用了自动注册，会先自动注册）
   - 如果提供了 `create_func`，使用自定义函数
   - 否则从模块 `src.agent.{name}.agent` 导入 `create_agent` 函数
   - 返回未编译的 `StateGraph`

3. **使用阶段**：
   - 调用 `compile()` 编译 Agent 图
   - 使用 `ainvoke()` 或 `invoke()` 调用 Agent

</div>

### Agent ID 生成规则

Agent ID 是通过以下方式生成的：

```python
# 伪代码
sorted_config = sort(config.items())
config_str = json.dumps(sorted_config, sort_keys=True)
combined = f"{name}:{config_str}"
agent_id = md5(combined.encode()).hexdigest()
```

这意味着：
- 相同名称 + 相同配置 = 相同 ID
- 相同名称 + 不同配置 = 不同 ID
- 不同名称 + 相同配置 = 不同 ID

---

## 📁 目录结构

```
src/agent/
├── __init__.py              # Agent 模块初始化
├── agent_manager.py         # Agent 管理器实现
├── agent_names.py           # Agent 名称常量定义
├── agent_demo.py            # Agent 演示示例
├── graph.py                 # 通用图定义
├── README.md                # 本文档
└── example/                 # Example Agent 实现
    ├── __init__.py
    ├── agent.py             # Agent 核心逻辑
    ├── state.py             # State 定义
    ├── context.py           # Context 定义
    └── config.example.json  # 配置示例文件
```

---

## 🔗 相关文档

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LLM 服务使用指南](../llm/README.md)
- [LangChain 文档](https://python.langchain.com/)

---

**© 2024 Agent Service Module | 使用 LangGraph 构建**

