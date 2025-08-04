"""Perplexica MCP Server package."""

from .server import main
from .client import PerplexicaClient
from .models import PerplexicaConfig, SearchRequest, SearchResponse

__version__ = "0.1.0"
__all__ = ["main", "PerplexicaClient", "PerplexicaConfig", "SearchRequest", "SearchResponse"]