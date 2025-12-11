<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        line-height: 1.8;
        color: #333;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    h1 {
        color: #667eea;
        border-bottom: 3px solid #667eea;
        padding-bottom: 10px;
    }
    h2 {
        color: #667eea;
        margin-top: 40px;
        border-bottom: 2px solid #667eea;
        padding-bottom: 8px;
    }
    h3 {
        color: #764ba2;
        margin-top: 30px;
    }
    .feature-box {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 20px;
        margin: 20px 0;
        border-radius: 4px;
    }
    .warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 20px 0;
        border-radius: 4px;
    }
    .info {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 15px;
        margin: 20px 0;
        border-radius: 4px;
    }
    .success {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 15px;
        margin: 20px 0;
        border-radius: 4px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    th {
        background: #667eea;
        color: white;
        font-weight: bold;
    }
    tr:hover {
        background: #f5f5f5;
    }
    code {
        background: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
    }
    pre {
        background: #2d2d2d;
        color: #f8f8f2;
        padding: 20px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 20px 0;
    }
    pre code {
        background: transparent;
        color: #f8f8f2;
        padding: 0;
    }
</style>

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
