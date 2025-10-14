#!/usr/bin/env python3
"""
MCP OpenProject Server using standard MCP library

Production-ready MCP server using the standard MCP library for stdio transport.
Maintains our existing OpenProject client and configuration management.
"""

import asyncio
import json
import sys
import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import MCP library components
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    InitializeResult,
    ServerCapabilities,
    ToolsCapability
)

# Import our existing modules
try:
    from .simple_config import load_config, ServerConfig
    from .openproject_client import OpenProjectClient, create_openproject_client, OpenProjectClientError
    from .security import SecurityError, AuthenticationError
except ImportError:
    # Fallback for running directly
    from simple_config import load_config, ServerConfig
    from openproject_client import OpenProjectClient, create_openproject_client, OpenProjectClientError
    from security import SecurityError, AuthenticationError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_openproject.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server(
    name="openproject-mcp-server",
    version="1.0.0",
    instructions="OpenProject MCP Server providing access to project data and work packages"
)

# Global state for OpenProject client
openproject_client: Optional[OpenProjectClient] = None


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    logger.info("Listing available tools")

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


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    global openproject_client

    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        # Initialize OpenProject client if not already done
        if openproject_client is None:
            logger.info("Initializing OpenProject client")
            config = load_config()
            openproject_client = await create_openproject_client(config)

        # Handle different tools
        if name == "get_project":
            project_id = arguments.get("project_id")
            if not project_id:
                raise ValueError("project_id is required")

            logger.info(f"Getting project {project_id}")
            project = await openproject_client.get_project(project_id)

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

        elif name == "get_work_packages":
            project_id = arguments.get("project_id")
            filters = arguments.get("filters")

            if not project_id:
                raise ValueError("project_id is required")

            logger.info(f"Getting work packages for project {project_id}")
            work_packages = await openproject_client.get_work_packages(project_id, filters)

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

        elif name == "get_weekly_report":
            project_id = arguments.get("project_id")
            week = arguments.get("week")

            if not project_id:
                raise ValueError("project_id is required")

            logger.info(f"Getting weekly report for project {project_id}, week {week or 'current'}")
            report = await openproject_client.get_weekly_report(project_id, week)

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


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting MCP OpenProject Server (stdio mode)")

    try:
        # Validate configuration
        config = load_config()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"OpenProject URL: {config.openproject_base_url}")
        logger.info(f"Environment: {'production' if not config.debug else 'development'}")

        # Send ready message to stderr
        print("MCP OpenProject Server (stdio mode) - Ready", file=sys.stderr)
        sys.stderr.flush()

        # Start stdio server
        logger.info("Starting stdio server transport")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)

    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        print(f"Failed to start MCP server: {e}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())