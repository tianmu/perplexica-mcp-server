# Perplexica MCP Server

**Language**: [English](README.md) | [中文](README_zh.md)

A Model Context Protocol (MCP) server that provides access to Perplexica's AI-powered search engine capabilities.

## Features

- **Web Search**: General web search using AI
- **Academic Search**: Search academic sources and papers  
- **YouTube Search**: Find and summarize YouTube videos
- **Reddit Search**: Search Reddit discussions
- **Writing Assistant**: Get help with writing and research
- **Multi-model Support**: Use different chat and embedding models
- **Health Monitoring**: Check service status and availability

## Prerequisites

- Python 3.10+
- A running Perplexica instance (default: http://localhost:3000)
- Optional: OpenAI API key for enhanced search capabilities

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install .
   ```

## Configuration
### cline
Configure the server to cline:
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


## Development

Copy `env.example` to `.env` and modify as needed:

```bash
cp env.example .env
# Edit .env file to set your configuration
```


### Starting the Server

Run the MCP server with stdio transport:

```bash
python -m perplexica_mcp_server.server
```

### Testing

Test the server functionality:

```bash
python test/test_client.py
```

Run test for you perplexica:

```bash
python test/test_official_api.py
```


### Output Formats

Supports two output formats:
- `json`: Raw JSON data (default)
- `formatted`: Human-readable formatted text


## License

MIT License