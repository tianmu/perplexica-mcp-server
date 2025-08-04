# Perplexica MCP 服务器

**语言版本**: [English](README.md) | [中文](README_zh.md)

一个模型上下文协议 (MCP) 服务器，提供对 Perplexica AI 搜索引擎功能的访问。

## 功能特性

- **网页搜索**: 使用 AI 进行通用网页搜索
- **学术搜索**: 搜索学术资源和论文  
- **YouTube 搜索**: 查找和总结 YouTube 视频
- **Reddit 搜索**: 搜索 Reddit 讨论
- **写作助手**: 获得写作和研究帮助
- **多模型支持**: 使用不同的聊天和嵌入模型
- **健康监控**: 检查服务状态和可用性

## 前置要求

- Python 3.10+
- 运行中的 Perplexica 实例（默认: http://localhost:3000）
- 可选: OpenAI API 密钥以增强搜索功能

## 安装

1. 克隆此仓库
2. 安装依赖:
   ```bash
   pip install -r requirements.txt
   pip install .
   ```
or
   ```bash
   uv tool install .
   ```
## 配置
### cline
配置服务器到 cline:
```json
{
  "mcpServers": {
    "perplexica": {
      "command": "python",
      "args": [
        "-m", "perplexica_mcp_server.server"
      ],
      "env": {
        "PERPLEXICA_DEFAULT_CHAT_PROVIDER":"custom_openai",
        "PERPLEXICA_DEFAULT_CHAT_MODEL":"gpt-4.1",
        "PERPLEXICA_CUSTOM_OPENAI_BASE_URL":"https://api.poe.com/v1",
        "PERPLEXICA_CUSTOM_OPENAI_KEY":"your_api_key",
        "PERPLEXICA_DEFAULT_EMBEDDING_PROVIDER":"transformers",
        "PERPLEXICA_DEFAULT_EMBEDDING_MODEL":"xenova-bge-small-en-v1.5",
        "PERPLEXICA_OPTIMIZATION_MODE":"balanced",
        "PERPLEXICA_BASE_URL":"http://localhost:3000"
      },
      "timeout": 60,
      "transport": "stdio"
    }
  }
}
```
or
```json
{
  "mcpServers": {
    "perplexica": {
      "command": "uvx",
      "args": [
        "perplexica-mcp-server"
      ],
      "env": {
        "PERPLEXICA_DEFAULT_CHAT_PROVIDER":"custom_openai",
        "PERPLEXICA_DEFAULT_CHAT_MODEL":"gpt-4.1",
        "PERPLEXICA_CUSTOM_OPENAI_BASE_URL":"https://api.poe.com/v1",
        "PERPLEXICA_CUSTOM_OPENAI_KEY":"your_api_key",
        "PERPLEXICA_DEFAULT_EMBEDDING_PROVIDER":"transformers",
        "PERPLEXICA_DEFAULT_EMBEDDING_MODEL":"xenova-bge-small-en-v1.5",
        "PERPLEXICA_OPTIMIZATION_MODE":"balanced",
        "PERPLEXICA_BASE_URL":"http://localhost:3000"
      },
      "timeout": 60,
      "transport": "stdio"
    }
  }
}

```
## 开发

复制 `env.example` 到 `.env` 并根据需要修改:

```bash
cp env.example .env
# 编辑 .env 文件设置您的配置
```

### 启动服务器

使用 stdio 传输运行 MCP 服务器:

```bash
python -m perplexica_mcp_server.server
```

### 测试

测试服务器功能:

```bash
python test/test_client.py
```

测试您的 perplexica:

```bash
python test/test_official_api.py
```

### 输出格式

支持两种输出格式:
- `json`: 原始 JSON 数据（默认）
- `formatted`: 人类可读的格式化文本

## 许可证

MIT 许可证