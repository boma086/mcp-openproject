"""
HTTP transport implementation for MCP OpenProject Server.

Provides RESTful HTTP endpoints for web service integration.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from mcp_server.transports.base import BaseTransport
from mcp_server.src.config import ServerConfig

logger = logging.getLogger(__name__)


class HttpTransport(BaseTransport):
    """HTTP transport implementation for MCP server."""

    def __init__(self, config: ServerConfig, host: str = "localhost", port: int = 8000):
        super().__init__(config)
        self.host = host
        self.port = port
        self._server: Optional[asyncio.Server] = None

    async def start(self) -> None:
        """Start HTTP transport."""
        logger.info(f"Starting HTTP transport on {self.host}:{self.port}...")
        self._is_running = True

        # Initialize MCP core
        await self.initialize_core()

        print(f"MCP OpenProject HTTP Server - Ready")
        print(f"Listening on: http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop HTTP transport."""
        logger.info("Stopping HTTP transport...")

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        await self.cleanup()
        logger.info("HTTP transport stopped")

    async def serve(self) -> None:
        """Main serving loop for HTTP transport."""
        try:
            # Create HTTP server
            self._server = await asyncio.start_server(
                self._handle_connection,
                self.host,
                self.port
            )

            logger.info(f"HTTP server listening on {self.host}:{self.port}")

            # Keep server running
            async with self._server:
                await self._server.serve_forever()

        except Exception as e:
            logger.error(f"HTTP server error: {e}")
            raise
        finally:
            await self.cleanup()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle incoming HTTP connection."""
        try:
            # Basic HTTP response for now
            response = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            response += json.dumps({
                "status": "ok",
                "transport": "http",
                "message": "MCP OpenProject HTTP Server"
            }).encode()

            writer.write(response)
            await writer.drain()

        except Exception as e:
            logger.error(f"HTTP connection error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check specific to HTTP transport."""
        base_health = await super().health_check()
        base_health.update({
            "transport_mode": "http",
            "host": self.host,
            "port": self.port,
            "server_running": self._server is not None
        })
        return base_health