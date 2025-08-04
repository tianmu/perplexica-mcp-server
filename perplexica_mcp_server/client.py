"""Perplexica API client."""

import json
import asyncio
from typing import AsyncGenerator, Optional
import httpx

from .models import SearchRequest, SearchResponse, StreamMessage, Source, PerplexicaConfig


class PerplexicaClient:
    """Client for interacting with Perplexica API."""
    
    def __init__(self, config: PerplexicaConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout)
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform a search and return the complete response."""
        
        # Apply defaults from config
        if request.chatModel is None and self.config.default_chat_model:
            request.chatModel = self.config.default_chat_model
        
        if request.embeddingModel is None and self.config.default_embedding_model:
            request.embeddingModel = self.config.default_embedding_model
        
        if request.optimizationMode is None:
            request.optimizationMode = self.config.default_optimization_mode
        
        try:
            # Convert model names to use the 'model' field for the actual API call
            request_data = request.model_dump(exclude_none=True)
            
            # Ensure chat model uses 'model' field for API compatibility
            if "chatModel" in request_data and request_data["chatModel"]:
                chat_model = request_data["chatModel"]
                if "name" in chat_model and not chat_model.get("model"):
                    chat_model["model"] = chat_model["name"]
            
            # Ensure embedding model uses 'model' field for API compatibility  
            if "embeddingModel" in request_data and request_data["embeddingModel"]:
                embedding_model = request_data["embeddingModel"]
                if "name" in embedding_model and not embedding_model.get("model"):
                    embedding_model["model"] = embedding_model["name"]
            
            response = await self.client.post(
                "/api/search",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            return SearchResponse(**data)
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"Perplexica API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Network error connecting to Perplexica: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from Perplexica: {str(e)}")
    
    async def search_stream(self, request: SearchRequest) -> AsyncGenerator[StreamMessage, None]:
        """Perform a streaming search."""
        
        # Apply defaults from config
        if request.chatModel is None and self.config.default_chat_model:
            request.chatModel = self.config.default_chat_model
        
        if request.embeddingModel is None and self.config.default_embedding_model:
            request.embeddingModel = self.config.default_embedding_model
        
        if request.optimizationMode is None:
            request.optimizationMode = self.config.default_optimization_mode
        
        try:
            async with self.client.stream(
                "POST",
                "/api/search",
                json={**request.model_dump(exclude_none=True), "stream": True},
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield StreamMessage(**data)
                        except json.JSONDecodeError:
                            continue  # Skip invalid JSON lines
                            
        except httpx.HTTPStatusError as e:
            raise Exception(f"Perplexica API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Network error connecting to Perplexica: {str(e)}")
    
    async def get_models(self) -> dict:
        """Get available models from Perplexica."""
        try:
            response = await self.client.get("/api/models")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Perplexica API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Network error connecting to Perplexica: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Perplexica API is healthy."""
        try:
            response = await self.client.get("/api/models", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False