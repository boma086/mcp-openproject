"""
MCP OpenProject Server Package

Production-ready MCP server with multiple transport modes.
"""

__version__ = "0.1.0"
__author__ = "MCP OpenProject Team"

# Import core components
from .src.config import ServerConfig, load_config
from .src.security import SecurityManager
from .src.openproject_client import OpenProjectClient, create_openproject_client
from .src.mcp_core import MCPCore

__all__ = [
    "ServerConfig",
    "load_config",
    "SecurityManager",
    "OpenProjectClient",
    "create_openproject_client",
    "MCPCore"
]