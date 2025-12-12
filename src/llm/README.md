# 🚀 LLM 服务使用指南

**高效、智能的语言模型服务管理框架**

---

## 📖 简介

LLM 服务模块提供了一个高级接口，用于管理和使用语言模型（LLM）。该模块采用工厂模式和单例管理器模式，实现了 LLM 对象的生命周期管理、智能缓存和自动资源清理。

<div class="feature-box">

### ✨ 核心特性

- **自动缓存管理**：相同配置的 LLM 对象会被自动缓存和复用
- **资源自动清理**：支持 `with` 语句自动释放资源
- **线程安全**：多线程环境下安全使用
- **生命周期管理**：自动管理 LLM 对象的创建、使用和回收
- **定期清理**：后台线程定期清理过期的缓存对象

</div>

---

## 🔧 安装与配置

### 依赖安装

确保已安装以下依赖：

```bash
# 项目依赖已在 pyproject.toml 中定义
pip install -e .
```

### 环境变量配置

<div class="info">

**💡 提示：** 设置 `OPENAI_API_KEY` 环境变量，或在使用时通过配置传入 API key。

</div>

```bash
# 在 .env 文件中设置
OPENAI_API_KEY=your-api-key-here
```

---

## 🚀 快速开始

### 基础使用

```python
from src.llm import create_service

# 创建服务实例（使用默认配置）
service = create_service()

# 调用 LLM
response = service.invoke("Hello, world!")
print(response)

# 手动释放资源
service.release()
```

### 使用 with 语句（推荐）

<div class="success">

**✅ 最佳实践：** 使用 `with` 语句可以确保资源自动释放，无需手动调用 `release()`。

</div>

```python
from src.llm import create_service

# 使用 with 语句自动管理资源
with create_service() as service:
    response = service.invoke("What is Python?")
    print(response)
# 退出 with 块时自动释放资源
```

### 自定义配置

```python
from src.llm import create_service

# 创建自定义配置的服务
with create_service({
    "model_name": "gpt-4",
    "temperature": 0.5,
    "max_tokens": 1000
}) as service:
    response = service.invoke("Explain machine learning")
    print(response)
```

---

## 📚 API 参考

### create_service()

创建 LLM 服务实例的便捷函数。

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `config` | `Dict[str, Any] \| None` | 配置字典 | `None` |

### 配置参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `model_name` | `str` | 模型名称 | `"gpt-3.5-turbo"` |
| `temperature` | `float` | 采样温度（0-2） | `0.7` |
| `max_tokens` | `int \| None` | 最大生成 token 数 | `None` |
| `api_key` | `str \| None` | OpenAI API 密钥 | 从环境变量读取 |
| `base_url` | `str \| None` | API 基础 URL | OpenAI 默认 URL |

### Service 方法

#### invoke(prompt: str, **kwargs) -> str

调用 LLM 生成响应。

```python
response = service.invoke("Your prompt here")
```

#### batch_invoke(prompts: List[str], **kwargs) -> List[str]

批量调用 LLM。

```python
responses = service.batch_invoke([
    "Prompt 1",
    "Prompt 2",
    "Prompt 3"
])
```

#### stream(prompt: str, **kwargs) -> Generator

流式生成响应。

```python
for chunk in service.stream("Your prompt"):
    print(chunk, end="")
```

#### release()

手动释放 LLM 资源（通常在 `with` 语句中自动调用）。

---

## 💡 使用示例

### 示例 1：简单对话

```python
from src.llm import create_service

with create_service() as service:
    question = "What is the capital of France?"
    answer = service.invoke(question)
    print(f"Q: {question}")
    print(f"A: {answer}")
```

### 示例 2：批量处理

```python
from src.llm import create_service

questions = [
    "What is Python?",
    "What is machine learning?",
    "What is deep learning?"
]

with create_service() as service:
    answers = service.batch_invoke(questions)
    for q, a in zip(questions, answers):
        print(f"Q: {q}\nA: {a}\n")
```

### 示例 3：流式输出

```python
from src.llm import create_service

with create_service() as service:
    print("Response: ", end="")
    for chunk in service.stream("Tell me a story"):
        if hasattr(chunk, 'content'):
            print(chunk.content, end="", flush=True)
        else:
            print(chunk, end="", flush=True)
    print()  # 换行
```

### 示例 4：使用 GPT-4

```python
from src.llm import create_service

with create_service({
    "model_name": "gpt-4",
    "temperature": 0.3
}) as service:
    response = service.invoke("Write a Python function to calculate factorial")
    print(response)
```

### 示例 5：为 LLM 绑定工具

```python
from langchain_core.tools import tool
from src.llm import create_service

# 定义工具
@tool
def add(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers together."""
    return a * b

# 创建工具列表
tools = [add, multiply]

# 创建服务并获取 LLM
with create_service() as service:
    llm = service.get_llm()
    
    # 绑定工具到 LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # 使用带工具的 LLM
    response = llm_with_tools.invoke("What is 5 + 3?")
    print(response)
```

content='' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 18, 'prompt_tokens': 52, 'total_tokens': 70, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'gpt-4.1-mini-2025-04-14', 'system_fingerprint': 'fp_3dcd5944f5', 'id': 'chatcmpl-Clk5dCkIEipVEn8soyDm3E7JWTWHp', 'finish_reason': 'tool_calls', 'logprobs': None} id='lc_run--019b0fae-0071-7973-816e-f8f39db73e2b-0' tool_calls=[{'name': 'add', 'args': {'a': 10, 'b': 10}, 'id': 'call_qsaH3LV5SUMMEsZc63xMuewE', 'type': 'tool_call'}] usage_metadata={'input_tokens': 52, 'output_tokens': 18, 'total_tokens': 70, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}


---

## 🔧 工具绑定与 Agent 集成

### 定义工具

使用 `@tool` 装饰器定义工具函数：

```python
from langchain_core.tools import tool

@tool
def add(a: int, b: int) -> int:
    """Adds two numbers together.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    return a + b

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.
    
    Args:
        city: Name of the city
    
    Returns:
        Weather information
    """
    # 实现天气查询逻辑
    return f"Weather in {city}: Sunny, 25°C"
```

### 绑定工具到 LLM

从服务获取 LLM 对象后，使用 `bind_tools()` 方法绑定工具：

```python
from src.llm import create_service
from langchain_core.tools import tool

# 定义工具
@tool
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

# 创建工具列表
tools = [add]

# 创建服务并绑定工具
with create_service() as service:
    # 获取 LLM 对象
    llm = service.get_llm()
    
    # 绑定工具
    llm_with_tools = llm.bind_tools(tools)
    
    # 现在可以使用带工具的 LLM
    response = llm_with_tools.invoke("Calculate 10 + 20")
```

### 在 Agent 中使用工具

在 LangGraph Agent 中集成带工具的 LLM：

```python
from dataclasses import dataclass
from typing import Any, Dict

from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from src.llm import create_service

# 定义工具
@tool
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers."""
    return a * b

# 创建工具列表和字典
tools = [add, multiply]
tools_by_name = {tool.name: tool for tool in tools}

# 创建 LLM 服务
llm_service = create_service()
llm = llm_service.get_llm()

# 绑定工具到 LLM
llm_with_tools = llm.bind_tools(tools)

# 定义 Agent State
@dataclass
class State:
    """Agent state."""
    messages: list = None
    # 其他状态字段...

# 定义 Agent 节点
async def agent_node(state: State, runtime: Runtime) -> Dict[str, Any]:
    """Agent node that uses LLM with tools."""
    # 使用带工具的 LLM
    response = llm_with_tools.invoke(state.messages[-1].content)
    
    # 处理工具调用
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            # 执行工具
            if tool_name in tools_by_name:
                tool_result = tools_by_name[tool_name].invoke(tool_args)
                # 将工具结果添加到消息中
                # ...
    
    return {"messages": [response]}

# 构建图
graph = (
    StateGraph(State)
    .add_node("agent", agent_node)
    .add_edge("__start__", "agent")
    .compile()
)
```

### 完整示例：带工具的 Agent

<div class="feature-box">

**完整示例：**

```python
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from src.llm import create_service

# 1. 定义工具
@tool
def calculator(expression: str) -> str:
    """Evaluates a mathematical expression.
    
    Args:
        expression: Mathematical expression as string (e.g., "2 + 2")
    
    Returns:
        Result of the expression
    """
    try:
        result = eval(expression)  # 注意：生产环境应使用更安全的方法
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# 2. 创建工具列表
tools = [calculator]

# 3. 创建服务并绑定工具
with create_service() as service:
    llm = service.get_llm()
    llm_with_tools = llm.bind_tools(tools)
    
    # 4. 使用带工具的 LLM
    messages = [HumanMessage(content="What is 15 * 8?")]
    response = llm_with_tools.invoke(messages)
    
    # 5. 处理工具调用
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            # 执行工具
            if tool_name == 'calculator':
                result = calculator.invoke(tool_args)
                print(f"Tool result: {result}")
    
    print(f"LLM response: {response.content}")
```

</div>

### 工具绑定最佳实践

<div class="info">

**💡 提示：**

1. **工具定义**：确保工具函数有清晰的文档字符串，LLM 会使用这些信息来决定何时调用工具
2. **工具命名**：使用描述性的工具名称，帮助 LLM 理解工具的功能
3. **参数类型**：明确定义参数类型，有助于 LLM 正确调用工具
4. **错误处理**：在工具函数中添加适当的错误处理
5. **资源管理**：使用 `with` 语句确保服务资源正确释放

</div>

<div class="warning">

**⚠️ 注意事项：**

- 绑定工具后，LLM 可能会返回工具调用请求，需要检查 `tool_calls` 属性
- 工具执行结果应该反馈给 LLM，以便生成最终响应
- 在生产环境中，避免使用 `eval()` 等不安全的函数执行用户输入

</div>

---

## ⚠️ 注意事项

<div class="warning">

**⚠️ 重要提示：**

- 始终使用 `with` 语句或手动调用 `release()` 来释放资源
- 相同配置的 LLM 对象会被缓存和复用，提高效率
- 确保设置了正确的 API key，否则会抛出异常
- 在多线程环境中，服务是线程安全的

</div>

<div class="info">

**ℹ️ 性能优化：**

- 管理器会自动缓存未使用的 LLM 对象（默认 TTL: 1 小时）
- 后台线程会定期清理过期的缓存对象
- 缓存池大小限制为 100 个对象（可配置）

</div>

---

## 🏗️ 架构说明

LLM 服务模块采用三层架构设计：

1. **Factory 层**：负责创建 LLM 对象和服务实例
2. **Manager 层**：全局单例管理器，负责 LLM 对象的生命周期管理、缓存和清理
3. **Service 层**：对外暴露的高级接口，提供便捷的 LLM 调用方法

<div class="feature-box">

### 工作流程

1. Factory 创建 LLM 对象后，向 Manager 注册
2. Manager 检查缓存，如果存在相同配置的 LLM，则复用
3. Service 从 Manager 获取 LLM 对象（增加引用计数）
4. 使用完毕后，Service 释放 LLM（减少引用计数）
5. 当引用计数为 0 时，LLM 被移入缓存池
6. 后台线程定期清理过期的缓存对象

</div>

---

**© 2024 LLM Service Module | 使用 LangChain OpenAI 构建**
