"""Data models for Perplexica API requests and responses."""

from typing import List, Optional, Tuple, Literal, Any, Dict
from pydantic import BaseModel, Field


class ChatModel(BaseModel):
    """Chat model configuration."""
    provider: str = Field(description="The provider for the chat model (e.g., 'openai', 'anthropic')")
    model: Optional[str] = Field(None, description="The specific chat model (e.g., 'gpt-4o-mini', 'claude-3-sonnet')")
    name: Optional[str] = Field(None, description="Alternative field name for the model (official API compatibility)")
    customOpenAIBaseURL: Optional[str] = Field(None, description="Custom OpenAI base URL")
    customOpenAIKey: Optional[str] = Field(None, description="Custom OpenAI API key")
    
    def get_model_name(self) -> str:
        """Get the model name, preferring 'name' field for official API compatibility."""
        return self.name or self.model or ""


class EmbeddingModel(BaseModel):
    """Embedding model configuration."""
    provider: str = Field(description="The provider for the embedding model (e.g., 'openai')")
    model: Optional[str] = Field(None, description="The specific embedding model (e.g., 'text-embedding-3-large')")
    name: Optional[str] = Field(None, description="Alternative field name for the model (official API compatibility)")
    
    def get_model_name(self) -> str:
        """Get the model name, preferring 'name' field for official API compatibility."""
        return self.name or self.model or ""


class SearchRequest(BaseModel):
    """Request model for Perplexica search API."""
    chatModel: Optional[ChatModel] = Field(None, description="Chat model configuration")
    embeddingModel: Optional[EmbeddingModel] = Field(None, description="Embedding model configuration")
    optimizationMode: Optional[Literal["speed", "balanced", "quality"]] = Field(
        "balanced", 
        description="Optimization mode for search performance"
    )
    focusMode: Literal[
        "webSearch", 
        "academicSearch", 
        "writingAssistant", 
        "wolframAlphaSearch", 
        "youtubeSearch", 
        "redditSearch"
    ] = Field(description="Focus mode for the search")
    query: str = Field(description="The search query or question")
    history: Optional[List[Tuple[str, str]]] = Field(
        None, 
        description="Chat history as list of [role, message] tuples"
    )
    systemInstructions: Optional[str] = Field(None, description="System instructions for the AI")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")


class Source(BaseModel):
    """Source information for search results."""
    pageContent: str = Field(description="Content snippet from the source")
    metadata: Dict[str, Any] = Field(description="Metadata including title and URL")


class SearchResponse(BaseModel):
    """Response model for Perplexica search API."""
    message: str = Field(description="The AI-generated response message")
    sources: List[Source] = Field(description="List of sources used to generate the response")


class StreamMessage(BaseModel):
    """Streaming message from Perplexica API."""
    type: Literal["init", "sources", "response", "done", "error"]
    data: Any


class PerplexicaConfig(BaseModel):
    """Configuration for Perplexica MCP server."""
    base_url: str = Field(default="http://localhost:3000", description="Perplexica API base URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    default_chat_model: Optional[ChatModel] = Field(None, description="Default chat model")
    default_embedding_model: Optional[EmbeddingModel] = Field(None, description="Default embedding model")
    default_optimization_mode: Literal["speed", "balanced", "quality"] = Field(
        "balanced", 
        description="Default optimization mode"
    )
    default_output_format: Literal["json", "formatted"] = Field(
        "json",
        description="Default output format for search results"
    )