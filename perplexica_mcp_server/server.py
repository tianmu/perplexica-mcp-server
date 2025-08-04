"""Perplexica MCP Server implementation."""

import json
import os
import sys
import logging

from mcp.server.fastmcp import Context, FastMCP
from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections.abc import AsyncIterator

from .client import PerplexicaClient
from .models import (
    SearchRequest, 
    ChatModel, 
    EmbeddingModel, 
    PerplexicaConfig
)

# 设置日志
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# 设置特定的日志级别
logger = logging.getLogger(__name__)

# 降低MCP相关的日志级别，减少底层通信日志
logging.getLogger('mcp.server.lowlevel').setLevel(logging.WARNING)
logging.getLogger('mcp.client').setLevel(logging.WARNING)
logging.getLogger('mcp.shared').setLevel(logging.WARNING)


def load_config() -> PerplexicaConfig:
    """Load configuration from environment variables or config file."""
    # Try to load .env file if it exists
    try:
        from dotenv import load_dotenv
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
    except ImportError:
        pass  # dotenv not available, use only system environment
    
    config_data = {
        "base_url": os.getenv("PERPLEXICA_BASE_URL", "http://localhost:3000"),
        "timeout": int(os.getenv("PERPLEXICA_TIMEOUT", "30")),
        "default_optimization_mode": os.getenv("PERPLEXICA_OPTIMIZATION_MODE", "balanced"),
        "default_output_format": os.getenv("PERPLEXICA_DEFAULT_OUTPUT_FORMAT", "json"),
    }
    
    # Load default chat model if provided
    chat_provider = os.getenv("PERPLEXICA_DEFAULT_CHAT_PROVIDER")
    chat_model = os.getenv("PERPLEXICA_DEFAULT_CHAT_MODEL")
    if chat_provider and chat_model:
        chat_model_config = {
            "provider": chat_provider,
            "name": chat_model
        }
        
        # Add custom OpenAI configuration if using custom_openai provider
        if chat_provider == "custom_openai":
            custom_base_url = os.getenv("PERPLEXICA_CUSTOM_OPENAI_BASE_URL")
            custom_key = os.getenv("PERPLEXICA_CUSTOM_OPENAI_KEY")
            if custom_base_url:
                chat_model_config["customOpenAIBaseURL"] = custom_base_url
            if custom_key:
                chat_model_config["customOpenAIKey"] = custom_key
        
        config_data["default_chat_model"] = ChatModel(**chat_model_config)
        logger.info(f"Using default chat model: {chat_provider}/{chat_model}")
        if chat_provider == "custom_openai":
            logger.info(f"Custom OpenAI Base URL: {chat_model_config.get('customOpenAIBaseURL', 'Not set')}")
    
    # Load default embedding model if provided
    embedding_provider = os.getenv("PERPLEXICA_DEFAULT_EMBEDDING_PROVIDER")
    embedding_model = os.getenv("PERPLEXICA_DEFAULT_EMBEDDING_MODEL")
    if embedding_provider and embedding_model:
        config_data["default_embedding_model"] = EmbeddingModel(
            provider=embedding_provider, 
            name=embedding_model
        )
        logger.info(f"Using default embedding model: {embedding_provider}/{embedding_model}")
    
    logger.info(f"Configuration loaded: base_url={config_data['base_url']}, timeout={config_data['timeout']}")
    return PerplexicaConfig(**config_data)


@dataclass
class AppContext:
    """Application context with typed dependencies."""
    config: PerplexicaConfig


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    logger.info("Initializing application lifespan")
    config = load_config()
    try:
        yield AppContext(config=config)
    finally:
        logger.info("Application shutdown complete")


# Initialize FastMCP server with lifespan
mcp = FastMCP("Perplexica MCP Server", lifespan=app_lifespan)


def format_search_response(message: str, sources: list, search_type: str = "搜索", output_format: str = "formatted") -> str:
    """Format search response for better readability."""
    if output_format == "json":
        result = {"message": message, "sources": sources}
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    # Format as human-readable text
    emoji_map = {
        "网页搜索": "🔍",
        "学术搜索": "🎓", 
        "YouTube搜索": "📺",
        "Reddit搜索": "💬",
        "写作助手": "✍️"
    }
    
    emoji = emoji_map.get(search_type, "🔍")
    formatted_text = f"{emoji} **{search_type}结果**\n\n{message}"
    
    if sources:
        formatted_text += "\n\n📚 **参考来源**\n"
        for i, source in enumerate(sources, 1):
            title = source.get("title", "无标题")
            url = source.get("url", "")
            formatted_text += f"\n{i}. **{title}**"
            if url:
                formatted_text += f"\n   🔗 {url}"
            
            # 添加内容预览（限制长度）
            content = source.get("content", "")
            if content:
                preview = content[:150] + "..." if len(content) > 150 else content
                formatted_text += f"\n   📄 {preview}"
            formatted_text += "\n"
    
    return formatted_text

@mcp.tool()
async def search_web(
    ctx: Context,
    query: str,
    chat_provider: str = None,
    chat_model: str = None,
    embedding_provider: str = None,
    embedding_model: str = None,
    optimization_mode: str = None,
    output_format: str = None
) -> str:
    """
    Search the web using Perplexica's AI-powered search engine.
    
    Args:
        query: The search query or question
        chat_provider: Chat model provider (optional, uses env config if not provided)
        chat_model: Specific chat model to use (optional, uses env config if not provided)
        embedding_provider: Embedding model provider (optional, uses env config if not provided)
        embedding_model: Specific embedding model to use (optional, uses env config if not provided)
        optimization_mode: Speed vs quality tradeoff (optional, uses env config if not provided)
        output_format: Output format - "formatted" for human-readable text or "json" for raw JSON
    
    Returns:
        Formatted text with AI response and sources, or JSON if output_format="json"
    """
    await ctx.info(f"Web search request: {query}")

    client = PerplexicaClient(ctx.request_context.lifespan_context.config)
    async with client:
        try:
            # Use default output format from config if not provided
            if output_format is None:
                output_format = client.config.default_output_format
            
            # Build request using provided params or env defaults
            chat_model_config = None
            embedding_model_config = None
            
            if chat_provider and chat_model:
                chat_model_config = ChatModel(provider=chat_provider, name=chat_model)
            elif client.config.default_chat_model:
                chat_model_config = client.config.default_chat_model
                
            if embedding_provider and embedding_model:
                embedding_model_config = EmbeddingModel(provider=embedding_provider, name=embedding_model)
            elif client.config.default_embedding_model:
                embedding_model_config = client.config.default_embedding_model
            
            request = SearchRequest(
                chatModel=chat_model_config,
                embeddingModel=embedding_model_config,
                optimizationMode=optimization_mode or client.config.default_optimization_mode,
                focusMode="webSearch",
                query=query
            )
            
            response = await client.search(request)
            logger.info("Web search completed successfully")
            
            # Extract message and sources
            message = getattr(response, 'message', str(response))
            sources = []
            
            if hasattr(response, 'sources') and response.sources:
                sources = [
                    {
                        "content": source.pageContent,
                        "title": source.metadata.get("title", ""),
                        "url": source.metadata.get("url", "")
                    }
                    for source in response.sources
                ]
            
            # Return formatted output
            return format_search_response(message, sources, "网页搜索", output_format)
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def search_academic(
    ctx: Context,
    query: str,
    chat_provider: str = None,
    chat_model: str = None,
    embedding_provider: str = None,
    embedding_model: str = None,
    optimization_mode: str = None,
    output_format: str = None
) -> str:
    """
    Search academic sources using Perplexica's academic search mode.
    
    Args:
        query: The academic search query
        chat_provider: Chat model provider (optional, uses env config if not provided)
        chat_model: Specific chat model to use (optional, uses env config if not provided)
        embedding_provider: Embedding model provider (optional, uses env config if not provided)
        embedding_model: Specific embedding model to use (optional, uses env config if not provided)
        optimization_mode: Speed vs quality tradeoff (optional, uses env config if not provided)
        output_format: Output format - "formatted" for human-readable text or "json" for raw JSON
    
    Returns:
        Formatted text with AI response and sources, or JSON if output_format="json"
    """
    logger.info(f"Academic search request: {query}")
    client = PerplexicaClient(ctx.request_context.lifespan_context.config)
    async with client:
        try:
            # Use default output format from config if not provided
            if output_format is None:
                output_format = client.config.default_output_format
            
            # Build request using provided params or env defaults
            chat_model_config = None
            embedding_model_config = None
            
            if chat_provider and chat_model:
                chat_model_config = ChatModel(provider=chat_provider, name=chat_model)
            elif client.config.default_chat_model:
                chat_model_config = client.config.default_chat_model
                
            if embedding_provider and embedding_model:
                embedding_model_config = EmbeddingModel(provider=embedding_provider, name=embedding_model)
            elif client.config.default_embedding_model:
                embedding_model_config = client.config.default_embedding_model
            
            request = SearchRequest(
                chatModel=chat_model_config,
                embeddingModel=embedding_model_config,
                optimizationMode=optimization_mode or client.config.default_optimization_mode,
                focusMode="academicSearch",
                query=query
            )
            
            response = await client.search(request)
            logger.info("Academic search completed successfully")
            
            # Extract message and sources
            message = getattr(response, 'message', str(response))
            sources = []
            
            if hasattr(response, 'sources') and response.sources:
                sources = [
                    {
                        "content": source.pageContent,
                        "title": source.metadata.get("title", ""),
                        "url": source.metadata.get("url", "")
                    }
                    for source in response.sources
                ]
            
            # Return formatted output
            return format_search_response(message, sources, "学术搜索", output_format)
            
        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def search_youtube(
    ctx: Context,
    query: str,
    chat_provider: str = None,
    chat_model: str = None,
    optimization_mode: str = None,
    output_format: str = None
) -> str:
    """
    Search YouTube videos using Perplexica.
    
    Args:
        query: The YouTube search query
        chat_provider: Chat model provider (optional, uses env config if not provided)
        chat_model: Specific chat model to use (optional, uses env config if not provided)
        optimization_mode: Speed vs quality tradeoff (optional, uses env config if not provided)
        output_format: Output format - "formatted" for human-readable text or "json" for raw JSON
    
    Returns:
        Formatted text with AI response and sources, or JSON if output_format="json"
    """
    logger.info(f"YouTube search request: {query}")
    client = PerplexicaClient(ctx.request_context.lifespan_context.config)
    async with client:
        try:
            # Use default output format from config if not provided
            if output_format is None:
                output_format = client.config.default_output_format
            
            # Build request using provided params or env defaults
            chat_model_config = None
            
            if chat_provider and chat_model:
                chat_model_config = ChatModel(provider=chat_provider, name=chat_model)
            elif client.config.default_chat_model:
                chat_model_config = client.config.default_chat_model
            
            request = SearchRequest(
                chatModel=chat_model_config,
                optimizationMode=optimization_mode or client.config.default_optimization_mode,
                focusMode="youtubeSearch",
                query=query
            )
            
            response = await client.search(request)
            logger.info("YouTube search completed successfully")
            
            # Extract message and sources
            message = getattr(response, 'message', str(response))
            sources = []
            
            if hasattr(response, 'sources') and response.sources:
                sources = [
                    {
                        "content": source.pageContent,
                        "title": source.metadata.get("title", ""),
                        "url": source.metadata.get("url", "")
                    }
                    for source in response.sources
                ]
            
            # Return formatted output
            return format_search_response(message, sources, "YouTube搜索", output_format)
            
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def search_reddit(
    ctx: Context,
    query: str,
    chat_provider: str = None,
    chat_model: str = None,
    optimization_mode: str = None,
    output_format: str = None
) -> str:
    """
    Search Reddit discussions using Perplexica.
    
    Args:
        query: The Reddit search query
        chat_provider: Chat model provider (optional, uses env config if not provided)
        chat_model: Specific chat model to use (optional, uses env config if not provided)
        optimization_mode: Speed vs quality tradeoff (optional, uses env config if not provided)
        output_format: Output format - "formatted" for human-readable text or "json" for raw JSON
    
    Returns:
        Formatted text with AI response and sources, or JSON if output_format="json"
    """
    logger.info(f"Reddit search request: {query}")
    client = PerplexicaClient(ctx.request_context.lifespan_context.config)
    async with client:
        try:
            # Use default output format from config if not provided
            if output_format is None:
                output_format = client.config.default_output_format
            
            # Build request using provided params or env defaults
            chat_model_config = None
            
            if chat_provider and chat_model:
                chat_model_config = ChatModel(provider=chat_provider, name=chat_model)
            elif client.config.default_chat_model:
                chat_model_config = client.config.default_chat_model
            
            request = SearchRequest(
                chatModel=chat_model_config,
                optimizationMode=optimization_mode or client.config.default_optimization_mode,
                focusMode="redditSearch",
                query=query
            )
            
            response = await client.search(request)
            logger.info("Reddit search completed successfully")
            
            # Extract message and sources
            message = getattr(response, 'message', str(response))
            sources = []
            
            if hasattr(response, 'sources') and response.sources:
                sources = [
                    {
                        "content": source.pageContent,
                        "title": source.metadata.get("title", ""),
                        "url": source.metadata.get("url", "")
                    }
                    for source in response.sources
                ]
            
            # Return formatted output
            return format_search_response(message, sources, "Reddit搜索", output_format)
            
        except Exception as e:
            logger.error(f"Reddit search failed: {e}")
            return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def writing_assistant(
    ctx: Context,
    query: str,
    chat_provider: str = None,
    chat_model: str = None,
    optimization_mode: str = None,
    output_format: str = None
) -> str:
    """
    Use Perplexica's writing assistant mode for writing help and research.
    
    Args:
        query: The writing-related query or request
        chat_provider: Chat model provider (optional, uses env config if not provided)
        chat_model: Specific chat model to use (optional, uses env config if not provided)
        optimization_mode: Speed vs quality tradeoff (optional, uses env config if not provided)
        output_format: Output format - "formatted" for human-readable text or "json" for raw JSON
    
    Returns:
        Formatted text with AI response and sources, or JSON if output_format="json"
    """
    logger.info(f"Writing assistant request: {query}")
    client = PerplexicaClient(ctx.request_context.lifespan_context.config)
    async with client:
        try:
            # Use default output format from config if not provided
            if output_format is None:
                output_format = client.config.default_output_format
            
            # Build request using provided params or env defaults
            chat_model_config = None
            
            if chat_provider and chat_model:
                chat_model_config = ChatModel(provider=chat_provider, name=chat_model)
            elif client.config.default_chat_model:
                chat_model_config = client.config.default_chat_model
            
            request = SearchRequest(
                chatModel=chat_model_config,
                optimizationMode=optimization_mode or client.config.default_optimization_mode,
                focusMode="writingAssistant",
                query=query
            )
            
            response = await client.search(request)
            logger.info("Writing assistant completed successfully")
            
            # Extract message and sources
            message = getattr(response, 'message', str(response))
            sources = []
            
            if hasattr(response, 'sources') and response.sources:
                sources = [
                    {
                        "content": source.pageContent,
                        "title": source.metadata.get("title", ""),
                        "url": source.metadata.get("url", "")
                    }
                    for source in response.sources
                ]
            
            # Return formatted output
            return format_search_response(message, sources, "写作助手", output_format)
            
        except Exception as e:
            logger.error(f"Writing assistant failed: {e}")
            return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def get_available_models(ctx: Context) -> str:
    """
    Get available chat and embedding models from Perplexica.
    
    Returns:
        JSON string containing available models
    """
    logger.info("Getting available models")
    client = PerplexicaClient(ctx.request_context.lifespan_context.config)
    async with client:
        try:
            models = await client.get_models()
            logger.info("Got available models successfully")
            return json.dumps(models, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)


@mcp.tool()
async def health_check(ctx: Context) -> str:
    """
    Check if Perplexica API is healthy and accessible.
    
    Returns:
        JSON string with health status
    """
    logger.info("Performing health check")
    client = PerplexicaClient(ctx.request_context.lifespan_context.config)
    async with client:
        try:
            is_healthy = await client.health_check()
            logger.info(f"Health check result: {'healthy' if is_healthy else 'unhealthy'}")
            return json.dumps({
                "healthy": is_healthy,
                "message": "Perplexica API is accessible" if is_healthy else "Perplexica API is not accessible"
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return json.dumps({"healthy": False, "error": str(e)}, indent=2, ensure_ascii=False)


@mcp.resource(uri="perplexica://config")
async def get_config() -> str:
    """Get current Perplexica configuration."""
    logger.info("Getting configuration")
    config = load_config()
    return json.dumps(config.model_dump(), indent=2, ensure_ascii=False)


@mcp.resource(uri="perplexica://status")
async def get_status() -> str:
    """Get Perplexica service status."""
    logger.info("Getting service status")
    config = load_config()
    client = PerplexicaClient(config)
    async with client:
        try:
            is_healthy = await client.health_check()
            models = await client.get_models() if is_healthy else {}
            logger.info(f"Service status: {'healthy' if is_healthy else 'unhealthy'}")
            
            return json.dumps({
                "status": "healthy" if is_healthy else "unhealthy",
                "base_url": client.config.base_url,
                "available_models": models
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2, ensure_ascii=False)


def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Perplexica MCP Server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
