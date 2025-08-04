"""Test client for Perplexica MCP server."""

import asyncio
import json
import logging
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# 设置日志
logging.basicConfig(
    level=logging.INFO,  # 改为INFO级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# 设置特定的日志级别，减少MCP底层通信噪音
logger = logging.getLogger(__name__)
logging.getLogger('mcp.client.lowlevel').setLevel(logging.WARNING)
logging.getLogger('mcp.shared').setLevel(logging.WARNING)


async def main():
    """Test the Perplexica MCP server."""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "perplexica_mcp_server.server"],
        timeout=60  # 增加超时时间到 60 秒
    )
    
    logger.info("Starting test client...")
    logger.info("Connecting to server...")
    
    async with stdio_client(server_params) as (read, write):
        logger.info("Connected to server, creating session...")
        async with ClientSession(read, write) as session:
            try:
                # 初始化连接
                logger.info("Initializing session...")
                await session.initialize()
                logger.info("Session initialized successfully!")
                
                # 列出可用工具
                logger.info("Listing available tools...")
                tools_result = await session.list_tools()
                logger.info("Available tools:")
                for tool in tools_result.tools:
                    logger.info(f"  - {tool.name}: {tool.description}")
                
                # 测试健康检查
                logger.info("Testing health check...")
                result = await session.call_tool("health_check", arguments={})
                if result.content:
                    health_data = json.loads(result.content[0].text)
                    logger.info(f"Health Status: {health_data}")
                
                # 测试获取可用模型
                logger.info("Testing get_available_models...")
                result = await session.call_tool("get_available_models", arguments={})
                if result.content:
                    models_data = json.loads(result.content[0].text)
                    logger.info(f"Available Models: {json.dumps(models_data, indent=2, ensure_ascii=False)}")
                
                # 测试简单的网页搜索
                logger.info("Testing web search...")
                result = await session.call_tool(
                    "search_web",
                    arguments={
                        "query": "今天天气如何",
                        "optimization_mode": "balanced"
                    }
                )
                logger.info(result)
                if result.content:
                    response_data = json.loads(result.content[0].text)
                    logger.info(f"Raw response data: {response_data}")
                    
                    # Safe access to message field
                    message = response_data.get('message', 'No message field')
                    if isinstance(message, str) and len(message) > 200:
                        logger.info(f"Search Response: {message[:200]}...")
                    else:
                        logger.info(f"Search Response: {message}")
                    logger.info(f"Sources found: {len(response_data.get('sources', []))}")
                
            except Exception as e:
                logger.error(f"Error during testing: {e}")
                raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
        logger.info("All tests completed successfully!")
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user.")
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        sys.exit(1)