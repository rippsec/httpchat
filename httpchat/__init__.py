"""httpchat: chat HTTP para red local, sin dependencias."""
from .server import ChatRoom, serve, main

__all__ = ["ChatRoom", "serve", "main"]
__version__ = "0.1.0"
