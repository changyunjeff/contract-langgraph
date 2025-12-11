<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM 服务使用指南</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }

        header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .content {
            padding: 40px;
        }

        section {
            margin-bottom: 40px;
        }

        h2 {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        h3 {
            color: #764ba2;
            font-size: 1.4em;
            margin-top: 30px;
            margin-bottom: 15px;
        }

        .feature-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }

        .code-block {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .code-block code {
            color: #f8f8f2;
        }

        .keyword {
            color: #c678dd;
        }

        .string {
            color: #98c379;
        }

        .comment {
            color: #5c6370;
            font-style: italic;
        }

        .function {
            color: #61afef;
        }

        ul, ol {
            margin-left: 30px;
            margin-top: 10px;
        }

        li {
            margin-bottom: 8px;
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

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 8px;
        }

        .badge-primary {
            background: #667eea;
            color: white;
        }

        .badge-success {
            background: #28a745;
            color: white;
        }

        footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 LLM 服务使用指南</h1>
            <p>高效、智能的语言模型服务管理框架</p>
        </header>

        <div class="content">
            <section>
                <h2>📖 简介</h2>
                <p>
                    LLM 服务模块提供了一个高级接口，用于管理和使用语言模型（LLM）。
                    该模块采用工厂模式和单例管理器模式，实现了 LLM 对象的生命周期管理、
                    智能缓存和自动资源清理。
                </p>
                <div class="feature-box">
                    <h3>✨ 核心特性</h3>
                    <ul>
                        <li><strong>自动缓存管理</strong>：相同配置的 LLM 对象会被自动缓存和复用</li>
                        <li><strong>资源自动清理</strong>：支持 <code>with</code> 语句自动释放资源</li>
                        <li><strong>线程安全</strong>：多线程环境下安全使用</li>
                        <li><strong>生命周期管理</strong>：自动管理 LLM 对象的创建、使用和回收</li>
                        <li><strong>定期清理</strong>：后台线程定期清理过期的缓存对象</li>
                    </ul>
                </div>
            </section>

            <section>
                <h2>🔧 安装与配置</h2>
                <h3>依赖安装</h3>
                <p>确保已安装以下依赖：</p>
                <div class="code-block">
<code><span class="comment"># 项目依赖已在 pyproject.toml 中定义</span>
<span class="keyword">pip</span> install -e .
</code>
                </div>

                <h3>环境变量配置</h3>
                <div class="info">
                    <strong>💡 提示：</strong> 设置 <code>OPENAI_API_KEY</code> 环境变量，或在使用时通过配置传入 API key。
                </div>
                <div class="code-block">
<code><span class="comment"># 在 .env 文件中设置</span>
<span class="keyword">OPENAI_API_KEY</span>=<span class="string">your-api-key-here</span>
</code>
                </div>
            </section>

            <section>
                <h2>🚀 快速开始</h2>
                
                <h3>基础使用</h3>
                <div class="code-block">
<code><span class="keyword">from</span> src.llm <span class="keyword">import</span> create_service

<span class="comment"># 创建服务实例（使用默认配置）</span>
service = create_service()

<span class="comment"># 调用 LLM</span>
response = service.invoke(<span class="string">"Hello, world!"</span>)
<span class="function">print</span>(response)

<span class="comment"># 手动释放资源</span>
service.release()
</code>
                </div>

                <h3>使用 with 语句（推荐）</h3>
                <div class="success">
                    <strong>✅ 最佳实践：</strong> 使用 <code>with</code> 语句可以确保资源自动释放，无需手动调用 <code>release()</code>。
                </div>
                <div class="code-block">
<code><span class="keyword">from</span> src.llm <span class="keyword">import</span> create_service

<span class="comment"># 使用 with 语句自动管理资源</span>
<span class="keyword">with</span> create_service() <span class="keyword">as</span> service:
    response = service.invoke(<span class="string">"What is Python?"</span>)
    <span class="function">print</span>(response)
<span class="comment"># 退出 with 块时自动释放资源</span>
</code>
                </div>

                <h3>自定义配置</h3>
                <div class="code-block">
<code><span class="keyword">from</span> src.llm <span class="keyword">import</span> create_service

<span class="comment"># 创建自定义配置的服务</span>
<span class="keyword">with</span> create_service({
    <span class="string">"model_name"</span>: <span class="string">"gpt-4"</span>,
    <span class="string">"temperature"</span>: <span class="string">0.5</span>,
    <span class="string">"max_tokens"</span>: <span class="string">1000</span>
}) <span class="keyword">as</span> service:
    response = service.invoke(<span class="string">"Explain machine learning"</span>)
    <span class="function">print</span>(response)
</code>
                </div>
            </section>

            <section>
                <h2>📚 API 参考</h2>

                <h3>create_service()</h3>
                <p>创建 LLM 服务实例的便捷函数。</p>
                <table>
                    <tr>
                        <th>参数</th>
                        <th>类型</th>
                        <th>说明</th>
                        <th>默认值</th>
                    </tr>
                    <tr>
                        <td><code>config</code></td>
                        <td>Dict[str, Any] | None</td>
                        <td>配置字典</td>
                        <td>None</td>
                    </tr>
                </table>

                <h3>配置参数</h3>
                <table>
                    <tr>
                        <th>参数</th>
                        <th>类型</th>
                        <th>说明</th>
                        <th>默认值</th>
                    </tr>
                    <tr>
                        <td><code>model_name</code></td>
                        <td>str</td>
                        <td>模型名称</td>
                        <td>"gpt-3.5-turbo"</td>
                    </tr>
                    <tr>
                        <td><code>temperature</code></td>
                        <td>float</td>
                        <td>采样温度（0-2）</td>
                        <td>0.7</td>
                    </tr>
                    <tr>
                        <td><code>max_tokens</code></td>
                        <td>int | None</td>
                        <td>最大生成 token 数</td>
                        <td>None</td>
                    </tr>
                    <tr>
                        <td><code>api_key</code></td>
                        <td>str | None</td>
                        <td>OpenAI API 密钥</td>
                        <td>从环境变量读取</td>
                    </tr>
                    <tr>
                        <td><code>base_url</code></td>
                        <td>str | None</td>
                        <td>API 基础 URL</td>
                        <td>OpenAI 默认 URL</td>
                    </tr>
                </table>

                <h3>Service 方法</h3>
                
                <h4>invoke(prompt: str, **kwargs) -> str</h4>
                <p>调用 LLM 生成响应。</p>
                <div class="code-block">
<code>response = service.invoke(<span class="string">"Your prompt here"</span>)
</code>
                </div>

                <h4>batch_invoke(prompts: List[str], **kwargs) -> List[str]</h4>
                <p>批量调用 LLM。</p>
                <div class="code-block">
<code>responses = service.batch_invoke([
    <span class="string">"Prompt 1"</span>,
    <span class="string">"Prompt 2"</span>,
    <span class="string">"Prompt 3"</span>
])
</code>
                </div>

                <h4>stream(prompt: str, **kwargs) -> Generator</h4>
                <p>流式生成响应。</p>
                <div class="code-block">
<code><span class="keyword">for</span> chunk <span class="keyword">in</span> service.stream(<span class="string">"Your prompt"</span>):
    <span class="function">print</span>(chunk, end=<span class="string">""</span>)
</code>
                </div>

                <h4>release()</h4>
                <p>手动释放 LLM 资源（通常在 with 语句中自动调用）。</p>
            </section>

            <section>
                <h2>💡 使用示例</h2>

                <h3>示例 1：简单对话</h3>
                <div class="code-block">
<code><span class="keyword">from</span> src.llm <span class="keyword">import</span> create_service

<span class="keyword">with</span> create_service() <span class="keyword">as</span> service:
    question = <span class="string">"What is the capital of France?"</span>
    answer = service.invoke(question)
    <span class="function">print</span>(<span class="string">f"Q: {question}"</span>)
    <span class="function">print</span>(<span class="string">f"A: {answer}"</span>)
</code>
                </div>

                <h3>示例 2：批量处理</h3>
                <div class="code-block">
<code><span class="keyword">from</span> src.llm <span class="keyword">import</span> create_service

questions = [
    <span class="string">"What is Python?"</span>,
    <span class="string">"What is machine learning?"</span>,
    <span class="string">"What is deep learning?"</span>
]

<span class="keyword">with</span> create_service() <span class="keyword">as</span> service:
    answers = service.batch_invoke(questions)
    <span class="keyword">for</span> q, a <span class="keyword">in</span> <span class="function">zip</span>(questions, answers):
        <span class="function">print</span>(<span class="string">f"Q: {q}\nA: {a}\n"</span>)
</code>
                </div>

                <h3>示例 3：流式输出</h3>
                <div class="code-block">
<code><span class="keyword">from</span> src.llm <span class="keyword">import</span> create_service

<span class="keyword">with</span> create_service() <span class="keyword">as</span> service:
    <span class="function">print</span>(<span class="string">"Response: "</span>, end=<span class="string">""</span>)
    <span class="keyword">for</span> chunk <span class="keyword">in</span> service.stream(<span class="string">"Tell me a story"</span>):
        <span class="keyword">if</span> <span class="function">hasattr</span>(chunk, <span class="string">'content'</span>):
            <span class="function">print</span>(chunk.content, end=<span class="string">""</span>, flush=<span class="keyword">True</span>)
        <span class="keyword">else</span>:
            <span class="function">print</span>(chunk, end=<span class="string">""</span>, flush=<span class="keyword">True</span>)
    <span class="function">print</span>()  <span class="comment"># 换行</span>
</code>
                </div>

                <h3>示例 4：使用 GPT-4</h3>
                <div class="code-block">
<code><span class="keyword">from</span> src.llm <span class="keyword">import</span> create_service

<span class="keyword">with</span> create_service({
    <span class="string">"model_name"</span>: <span class="string">"gpt-4"</span>,
    <span class="string">"temperature"</span>: <span class="string">0.3</span>
}) <span class="keyword">as</span> service:
    response = service.invoke(<span class="string">"Write a Python function to calculate factorial"</span>)
    <span class="function">print</span>(response)
</code>
                </div>
            </section>

            <section>
                <h2>⚠️ 注意事项</h2>
                
                <div class="warning">
                    <strong>⚠️ 重要提示：</strong>
                    <ul>
                        <li>始终使用 <code>with</code> 语句或手动调用 <code>release()</code> 来释放资源</li>
                        <li>相同配置的 LLM 对象会被缓存和复用，提高效率</li>
                        <li>确保设置了正确的 API key，否则会抛出异常</li>
                        <li>在多线程环境中，服务是线程安全的</li>
                    </ul>
                </div>

                <div class="info">
                    <strong>ℹ️ 性能优化：</strong>
                    <ul>
                        <li>管理器会自动缓存未使用的 LLM 对象（默认 TTL: 1 小时）</li>
                        <li>后台线程会定期清理过期的缓存对象</li>
                        <li>缓存池大小限制为 100 个对象（可配置）</li>
                    </ul>
                </div>
            </section>

            <section>
                <h2>🏗️ 架构说明</h2>
                <p>
                    LLM 服务模块采用三层架构设计：
                </p>
                <ol>
                    <li><strong>Factory 层</strong>：负责创建 LLM 对象和服务实例</li>
                    <li><strong>Manager 层</strong>：全局单例管理器，负责 LLM 对象的生命周期管理、缓存和清理</li>
                    <li><strong>Service 层</strong>：对外暴露的高级接口，提供便捷的 LLM 调用方法</li>
                </ol>
                <div class="feature-box">
                    <h3>工作流程</h3>
                    <ol>
                        <li>Factory 创建 LLM 对象后，向 Manager 注册</li>
                        <li>Manager 检查缓存，如果存在相同配置的 LLM，则复用</li>
                        <li>Service 从 Manager 获取 LLM 对象（增加引用计数）</li>
                        <li>使用完毕后，Service 释放 LLM（减少引用计数）</li>
                        <li>当引用计数为 0 时，LLM 被移入缓存池</li>
                        <li>后台线程定期清理过期的缓存对象</li>
                    </ol>
                </div>
            </section>
        </div>

        <footer>
            <p>© 2024 LLM Service Module | 使用 LangChain OpenAI 构建</p>
        </footer>
    </div>
</body>
</html>

