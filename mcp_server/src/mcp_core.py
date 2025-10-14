"""
MCP Core functionality for OpenProject Server.

Provides shared MCP server logic that can be used by all transport modes.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult

from .config import ServerConfig
from .openproject_client import OpenProjectClient, OpenProjectClientError
from .security import SecurityError, AuthenticationError

logger = logging.getLogger(__name__)


class MCPCore:
    """Core MCP functionality shared across all transport modes."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.server = Server(
            name="openproject-mcp-server",
            version="1.0.0",
            instructions="OpenProject MCP Server providing access to project data and work packages"
        )
        self.client: Optional[OpenProjectClient] = None

    async def initialize(self) -> None:
        """Initialize the MCP core."""
        logger.info("Initializing MCP core...")

        # Validate configuration
        if not self.config.validate():
            raise ValueError("Invalid configuration")

        # Set up server tools
        await self._setup_tools()

        logger.info("MCP core initialized successfully")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.cleanup()
            self.client = None
        logger.info("MCP core cleaned up")

    async def _setup_tools(self) -> None:
        """Set up MCP server tools."""
        logger.info("Setting up MCP tools...")

        # Register tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)

    async def _list_tools(self) -> List[Tool]:
        """List available tools."""
        tools = [
            Tool(
                name="get_project",
                description="Get project information by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "integer",
                            "description": "Project ID to retrieve"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="get_work_packages",
                description="Get work packages for a project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "integer",
                            "description": "Project ID to get work packages for"
                        },
                        "filters": {
                            "type": "array",
                            "description": "Optional filters to apply",
                            "items": {
                                "type": "object"
                            }
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="get_weekly_report",
                description="Get weekly report data for a project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "integer",
                            "description": "Project ID to generate weekly report for"
                        },
                        "week": {
                            "type": "string",
                            "description": "Week identifier (e.g., '2024-W42')"
                        }
                    },
                    "required": ["project_id"]
                }
            )
        ]

        logger.info(f"Available tools: {[tool.name for tool in tools]}")
        return tools

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle tool calls."""
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        try:
            # Initialize OpenProject client if not already done
            if self.client is None:
                logger.info("Initializing OpenProject client")
                self.client = await self._create_client()

            # Handle different tools
            if name == "get_project":
                return await self._handle_get_project(arguments)
            elif name == "get_work_packages":
                return await self._handle_get_work_packages(arguments)
            elif name == "get_weekly_report":
                return await self._handle_get_weekly_report(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        except (ValueError, KeyError) as e:
            logger.error(f"Invalid arguments for tool {name}: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({"error": f"Invalid arguments: {str(e)}"})
                )]
            )

        except (OpenProjectClientError, AuthenticationError, SecurityError) as e:
            logger.error(f"OpenProject API error for tool {name}: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({"error": f"OpenProject API error: {str(e)}"})
                )]
            )

        except Exception as e:
            logger.error(f"Unexpected error for tool {name}: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unexpected error: {str(e)}"})
                )]
            )

    async def _create_client(self) -> OpenProjectClient:
        """Create OpenProject client."""
        from .openproject_client import create_openproject_client
        return await create_openproject_client(self.config)

    async def _handle_get_project(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_project tool call."""
        project_id = arguments.get("project_id")
        if not project_id:
            raise ValueError("project_id is required")

        logger.info(f"Getting project {project_id}")
        project = await self.client.get_project(project_id)

        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "id": project.id,
                    "name": project.name,
                    "identifier": project.identifier,
                    "description": project.description,
                    "created_at": project.created_at,
                    "updated_at": project.updated_at
                }, indent=2, default=str)
            )]
        )

    async def _handle_get_work_packages(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_work_packages tool call."""
        project_id = arguments.get("project_id")
        filters = arguments.get("filters")

        if not project_id:
            raise ValueError("project_id is required")

        logger.info(f"Getting work packages for project {project_id}")
        work_packages = await self.client.get_work_packages(project_id, filters)

        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "project_id": project_id,
                    "work_packages": [
                        {
                            "id": wp.id,
                            "subject": wp.subject,
                            "status": wp.status,
                            "priority": wp.priority,
                            "assignee": wp.assignee,
                            "due_date": wp.due_date,
                            "created_at": wp.created_at,
                            "updated_at": wp.updated_at
                        }
                        for wp in work_packages
                    ],
                    "total_count": len(work_packages)
                }, indent=2, default=str)
            )]
        )

    async def _handle_get_weekly_report(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_weekly_report tool call."""
        project_id = arguments.get("project_id")
        week = arguments.get("week")

        if not project_id:
            raise ValueError("project_id is required")

        logger.info(f"Getting weekly report for project {project_id}, week {week or 'current'}")
        report = await self.client.get_weekly_report(project_id, week)

        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "project": {
                        "id": report.project.id,
                        "name": report.project.name,
                        "identifier": report.project.identifier
                    },
                    "week": report.week,
                    "work_packages": [
                        {
                            "id": wp.id,
                            "subject": wp.subject,
                            "status": wp.status,
                            "priority": wp.priority,
                            "assignee": wp.assignee,
                            "due_date": wp.due_date
                        }
                        for wp in report.work_packages
                    ],
                    "summary": report.summary,
                    "total_packages": len(report.work_packages)
                }, indent=2, default=str)
            )]
        )

    async def setup_server_tools(self, server: Server) -> None:
        """Set up tools on an external server instance."""
        server.list_tools()(self._list_tools)
        server.call_tool()(self._call_tool)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of MCP core."""
        return {
            "core_initialized": self.client is not None,
            "config_valid": self.config.validate(),
            "tools_available": len(await self._list_tools()) > 0
        }