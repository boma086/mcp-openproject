"""
Stdio transport implementation for MCP OpenProject Server.

Provides JSON message protocol over stdin/stdout for IDE integration.
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, Optional

from mcp_server.transports.base import BaseTransport
from mcp_server.src.config import ServerConfig

logger = logging.getLogger(__name__)


class StdioTransport(BaseTransport):
    """Stdio transport implementation using MCP library."""

    def __init__(self, config: ServerConfig):
        super().__init__(config)
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Start stdio transport."""
        logger.info("Starting stdio transport...")
        self._is_running = True

        # Initialize MCP core
        await self.initialize_core()

        # Send ready message to stderr (not stdout to avoid protocol interference)
        print("MCP OpenProject Server (stdio mode) - Ready", file=sys.stderr)
        sys.stderr.flush()

    async def stop(self) -> None:
        """Stop stdio transport."""
        logger.info("Stopping stdio transport...")
        self._stop_event.set()
        await self.cleanup()
        logger.info("Stdio transport stopped")

    async def serve(self) -> None:
        """Main serving loop for stdio transport."""
        try:
            # Import here to avoid import issues
            from mcp.server.stdio import stdio_server
            from mcp.server import Server

            # Create MCP server instance
            server = Server(
                name="openproject-mcp-server",
                version="1.0.0",
                instructions="OpenProject MCP Server providing access to project data and work packages"
            )

            # Set up tools and handlers
            await self.mcp_core.setup_server_tools(server)

            logger.info("Starting stdio server transport")

            # Start stdio server
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, {})

        except Exception as e:
            logger.error(f"Stdio server error: {e}")
            raise
        finally:
            await self.cleanup()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check specific to stdio transport."""
        base_health = await super().health_check()
        base_health.update({
            "transport_mode": "stdio",
            "stdio_available": True
        })
        return base_health