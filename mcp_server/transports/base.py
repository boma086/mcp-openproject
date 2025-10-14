"""
Base transport class for MCP OpenProject Server.

Provides abstract interface and shared functionality for all transport modes.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncContextManager
from pathlib import Path

from mcp_server.src.config import ServerConfig
from mcp_server.src.mcp_core import MCPCore

logger = logging.getLogger(__name__)


class BaseTransport(ABC):
    """Abstract base class for transport implementations."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.mcp_core: Optional[MCPCore] = None
        self._is_running = False

    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        pass

    @abstractmethod
    async def serve(self) -> None:
        """Main serving loop."""
        pass

    async def initialize_core(self) -> MCPCore:
        """Initialize the MCP core if not already done."""
        if self.mcp_core is None:
            logger.info("Initializing MCP core...")
            self.mcp_core = MCPCore(self.config)
            await self.mcp_core.initialize()
        return self.mcp_core

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.mcp_core:
            await self.mcp_core.cleanup()
            self.mcp_core = None
        self._is_running = False

    def is_running(self) -> bool:
        """Check if transport is running."""
        return self._is_running

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "transport": self.__class__.__name__,
            "running": self.is_running(),
            "config_valid": self.config.validate(),
            "core_initialized": self.mcp_core is not None
        }