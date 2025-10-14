"""
SSE (Server-Sent Events) transport implementation for MCP OpenProject Server.

Provides real-time streaming for web applications.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

from mcp_server.transports.base import BaseTransport
from mcp_server.src.config import ServerConfig

logger = logging.getLogger(__name__)


class SseTransport(BaseTransport):
    """SSE transport implementation for MCP server."""

    def __init__(self, config: ServerConfig, host: str = "localhost", port: int = 8001):
        super().__init__(config)
        self.host = host
        self.port = port
        self._server: Optional[asyncio.Server] = None
        self._clients: set[asyncio.StreamWriter] = set()

    async def start(self) -> None:
        """Start SSE transport."""
        logger.info(f"Starting SSE transport on {self.host}:{self.port}...")
        self._is_running = True

        # Initialize MCP core
        await self.initialize_core()

        print(f"MCP OpenProject SSE Server - Ready")
        print(f"Listening on: http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop SSE transport."""
        logger.info("Stopping SSE transport...")

        # Close all client connections
        for client in self._clients.copy():
            try:
                client.close()
                await client.wait_closed()
            except Exception:
                pass
        self._clients.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        await self.cleanup()
        logger.info("SSE transport stopped")

    async def serve(self) -> None:
        """Main serving loop for SSE transport."""
        try:
            # Create SSE server
            self._server = await asyncio.start_server(
                self._handle_sse_connection,
                self.host,
                self.port
            )

            logger.info(f"SSE server listening on {self.host}:{self.port}")

            # Keep server running
            async with self._server:
                await self._server.serve_forever()

        except Exception as e:
            logger.error(f"SSE server error: {e}")
            raise
        finally:
            await self.cleanup()

    async def _handle_sse_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle incoming SSE connection."""
        try:
            # Add to clients set
            self._clients.add(writer)

            # Send SSE headers
            headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/event-stream\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: keep-alive\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "\r\n"
            )
            writer.write(headers.encode())
            await writer.drain()

            # Send initial event
            await self._send_sse_event(writer, "connected", {
                "transport": "sse",
                "message": "Connected to MCP OpenProject SSE Server"
            })

            # Keep connection alive
            while self._is_running:
                await self._send_sse_event(writer, "heartbeat", {"timestamp": asyncio.get_event_loop().time()})
                await asyncio.sleep(30)  # Heartbeat every 30 seconds

        except Exception as e:
            logger.error(f"SSE connection error: {e}")
        finally:
            # Remove from clients set
            self._clients.discard(writer)
            writer.close()
            await writer.wait_closed()

    async def _send_sse_event(self, writer: asyncio.StreamWriter, event: str, data: Dict[str, Any]) -> None:
        """Send SSE event to client."""
        try:
            message = f"event: {event}\ndata: {json.dumps(data)}\n\n"
            writer.write(message.encode())
            await writer.drain()
        except Exception as e:
            logger.error(f"Failed to send SSE event: {e}")
            # Remove failed client
            self._clients.discard(writer)

    async def broadcast_event(self, event: str, data: Dict[str, Any]) -> None:
        """Broadcast event to all connected clients."""
        if not self._clients:
            return

        # Send to all clients concurrently
        tasks = []
        for client in self._clients.copy():
            tasks.append(self._send_sse_event(client, event, data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check specific to SSE transport."""
        base_health = await super().health_check()
        base_health.update({
            "transport_mode": "sse",
            "host": self.host,
            "port": self.port,
            "server_running": self._server is not None,
            "connected_clients": len(self._clients)
        })
        return base_health