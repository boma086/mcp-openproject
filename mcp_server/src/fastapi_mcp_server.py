#!/usr/bin/env python3
"""
FastAPI-based MCP OpenProject Server

Production-ready MCP server using FastAPI as the base framework with
MCP protocol wrapper for compatibility. Replaces the original FastMCP
implementation with proper security, resource management, and error handling.
"""

import asyncio
import json
import sys
import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import structlog
from pydantic import BaseModel, Field

# Import our modules - using simple configuration
try:
    from .simple_config import load_config, ServerConfig
    from .security import get_security_middleware, SecurityError, AuthenticationError, ValidationError
    from .openproject_client import OpenProjectClient, create_openproject_client, OpenProjectClientError
except ImportError:
    from simple_config import load_config, ServerConfig
    from security import get_security_middleware, SecurityError, AuthenticationError, ValidationError
    from openproject_client import OpenProjectClient, create_openproject_client, OpenProjectClientError

logger = structlog.get_logger(__name__)


# MCP Protocol Models
class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(..., description="Input schema")


class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mimeType: Optional[str] = Field(None, description="Resource MIME type")


class MCPToolCall(BaseModel):
    """MCP tool call request."""
    tool: str = Field(..., description="Tool name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class MCPResponse(BaseModel):
    """MCP response."""
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


# API Request/Response Models
class WeeklyReportRequest(BaseModel):
    """Weekly report request."""
    project_id: int = Field(..., gt=0, description="Project ID")
    week: Optional[str] = Field(None, pattern=r"^202[0-9]-W([1-9]|[1-4][0-9]|5[0-3])$", description="Week format: YYYY-WXX")


class WeeklyReportResponse(BaseModel):
    """Weekly report response."""
    project: Dict[str, Any]
    work_packages: List[Dict[str, Any]]
    week: str
    summary: Optional[str] = None
    total_packages: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Server version")
    openproject_connected: bool = Field(..., description="OpenProject connectivity status")
    uptime_seconds: float = Field(..., description="Server uptime")


# Global state
class ServerState:
    """Server state management."""

    def __init__(self):
        self.config: Optional[ServerConfig] = None
        self.openproject_client: Optional[OpenProjectClient] = None
        self.start_time: float = 0
        self.security_middleware = None
        self.initialized: bool = False

    async def initialize(self, config: ServerConfig):
        """Initialize server state."""
        self.config = config
        self.openproject_client = await create_openproject_client(config)
        self.start_time = asyncio.get_event_loop().time()

        # Initialize security
        from .security import initialize_security
        self.security_middleware = initialize_security(config.encryption_key)

        self.initialized = True
        logger.info("Server state initialized",
                   transport_mode=config.transport_mode,
                   openproject_base_url=config.openproject_base_url)

    async def cleanup(self):
        """Cleanup server resources."""
        if self.openproject_client:
            await self.openproject_client.close()
        logger.info("Server state cleaned up")


# Global server state
server_state = ServerState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    config = load_config()
    await server_state.initialize(config)

    logger.info("MCP OpenProject Server started successfully",
               version="1.0.0",
               transport_mode=config.transport_mode,
               host=config.host,
               port=config.port)

    yield

    # Shutdown
    await server_state.cleanup()
    logger.info("MCP OpenProject Server stopped")


# Create FastAPI application
app = FastAPI(
    title="MCP OpenProject Server",
    description="Production-ready MCP server for OpenProject integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - simple configuration using environment variables
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
        allow_headers=["*"],
    )


# Exception handlers
@app.exception_handler(SecurityError)
async def security_exception_handler(request: Request, exc: SecurityError):
    """Handle security-related exceptions."""
    logger.warning("Security error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=403,
        content={"error": "security_error", "message": str(exc)}
    )


@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication exceptions."""
    logger.warning("Authentication error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=401,
        content={"error": "authentication_error", "message": str(exc)}
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation exceptions."""
    logger.warning("Validation error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": str(exc)}
    )


@app.exception_handler(OpenProjectClientError)
async def openproject_exception_handler(request: Request, exc: OpenProjectClientError):
    """Handle OpenProject client exceptions."""
    logger.error("OpenProject error", error=str(exc), path=request.url.path)

    status_code = 500
    if exc.error and exc.error.status_code:
        status_code = exc.error.status_code
    elif isinstance(exc, OpenProjectClientError):
        if "not found" in str(exc).lower():
            status_code = 404
        elif "authentication" in str(exc).lower():
            status_code = 401

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "openproject_error",
            "message": str(exc),
            "details": exc.error.__dict__ if exc.error else None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unexpected error", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Internal server error"}
    )


# Dependencies
async def get_openproject_client() -> OpenProjectClient:
    """Get OpenProject client dependency."""
    if not server_state.openproject_client:
        raise HTTPException(status_code=503, detail="OpenProject client not initialized")
    return server_state.openproject_client


async def require_read_permission():
    """Require read permission dependency."""
    if server_state.security_middleware:
        return await server_state.security_middleware.require_permission("read")()
    return {"user_id": "anonymous", "permissions": ["read"]}


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = asyncio.get_event_loop().time() - server_state.start_time

    # Check OpenProject connectivity
    openproject_connected = False
    try:
        if server_state.openproject_client:
            # Simple connectivity check - try to get projects list
            await server_state.openproject_client.get_projects_api()
            openproject_connected = True
    except Exception as e:
        logger.warning("OpenProject connectivity check failed", error=str(e))

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        openproject_connected=openproject_connected,
        uptime_seconds=uptime
    )


# MCP Protocol endpoints
@app.get("/mcp/tools", response_model=List[MCPTool])
async def list_mcp_tools(user_context: Dict = Depends(require_read_permission)):
    """List available MCP tools."""
    tools = [
        MCPTool(
            name="fetch_weekly_report",
            description="Fetch weekly report data for a specific project from OpenProject",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to fetch data for",
                        "minimum": 1
                    },
                    "week": {
                        "type": "string",
                        "description": "Optional week identifier (e.g., '2025-W41')",
                        "pattern": "^202[0-9]-W([1-9]|[1-4][0-9]|5[0-3])$"
                    }
                },
                "required": ["project_id"]
            }
        ),
        MCPTool(
            name="get_project_data",
            description="Get project data as a resource",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    }
                },
                "required": ["project_id"]
            }
        )
    ]

    logger.info("Listed MCP tools", count=len(tools), user=user_context.get("user_id"))
    return tools


@app.get("/mcp/resources", response_model=List[MCPResource])
async def list_mcp_resources(user_context: Dict = Depends(require_read_permission)):
    """List available MCP resources."""
    resources = [
        MCPResource(
            uri="openproject://projects/{project_id}",
            name="Project Data",
            description="OpenProject data for a specific project",
            mimeType="application/json"
        )
    ]

    logger.info("Listed MCP resources", count=len(resources), user=user_context.get("user_id"))
    return resources


@app.post("/mcp/tools/{tool_name}")
async def call_mcp_tool(
    tool_name: str,
    request: MCPToolCall,
    user_context: Dict = Depends(require_read_permission),
    client: OpenProjectClient = Depends(get_openproject_client)
):
    """
    Call an MCP tool.

    This is the main MCP protocol endpoint for tool execution.
    """
    logger.info("MCP tool called",
               tool=tool_name,
               params=request.params,
               user=user_context.get("user_id"))

    try:
        if tool_name == "fetch_weekly_report":
            return await handle_fetch_weekly_report(request.params, client)
        elif tool_name == "get_project_data":
            return await handle_get_project_data(request.params, client)
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    except Exception as e:
        logger.error("MCP tool execution failed",
                    tool=tool_name,
                    error=str(e),
                    user=user_context.get("user_id"))
        raise


async def handle_fetch_weekly_report(params: Dict[str, Any], client: OpenProjectClient) -> MCPResponse:
    """Handle fetch_weekly_report tool call."""
    project_id = params.get("project_id")
    week = params.get("week")

    if not project_id:
        raise ValidationError("project_id is required")

    # Get weekly report data
    report_data = await client.get_weekly_report(project_id, week)

    # Convert to dict for MCP response
    response_data = {
        "project": report_data.project.dict(),
        "work_packages": [wp.dict() for wp in report_data.work_packages],
        "week": report_data.week,
        "summary": report_data.summary,
        "total_packages": len(report_data.work_packages)
    }

    return MCPResponse(data=response_data)


async def handle_get_project_data(params: Dict[str, Any], client: OpenProjectClient) -> MCPResponse:
    """Handle get_project_data tool call."""
    project_id = params.get("project_id")

    if not project_id:
        raise ValidationError("project_id is required")

    # Get project data
    project_data = await client.get_project(project_id)

    # Get work packages for the project
    work_packages = await client.get_work_packages(project_id)

    response_data = {
        "project": project_data.dict(),
        "work_packages": [wp.dict() for wp in work_packages],
        "total_packages": len(work_packages)
    }

    return MCPResponse(data=response_data)


@app.get("/mcp/resources/openproject://projects/{project_id}")
async def get_mcp_resource(
    project_id: int,
    user_context: Dict = Depends(require_read_permission),
    client: OpenProjectClient = Depends(get_openproject_client)
):
    """Get MCP resource data."""
    logger.info("MCP resource requested",
               resource=f"openproject://projects/{project_id}",
               user=user_context.get("user_id"))

    try:
        # Get project data
        project_data = await client.get_project(project_id)

        # Get work packages for the project
        work_packages = await client.get_work_packages(project_id)

        resource_data = {
            "project": project_data.dict(),
            "work_packages": [wp.dict() for wp in work_packages],
            "total_packages": len(work_packages)
        }

        return Response(
            content=json.dumps(resource_data, indent=2),
            media_type="application/json"
        )

    except Exception as e:
        logger.error("MCP resource retrieval failed",
                    resource=f"openproject://projects/{project_id}",
                    error=str(e),
                    user=user_context.get("user_id"))
        raise


# REST API endpoints for direct HTTP access
@app.post("/api/v1/reports/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    request: WeeklyReportRequest,
    user_context: Dict = Depends(require_read_permission),
    client: OpenProjectClient = Depends(get_openproject_client)
):
    """Get weekly report via REST API."""
    logger.info("Weekly report requested via REST API",
               project_id=request.project_id,
               week=request.week,
               user=user_context.get("user_id"))

    report_data = await client.get_weekly_report(request.project_id, request.week)

    return WeeklyReportResponse(
        project=report_data.project.dict(),
        work_packages=[wp.dict() for wp in report_data.work_packages],
        week=report_data.week,
        summary=report_data.summary,
        total_packages=len(report_data.work_packages)
    )


@app.get("/api/v1/projects/{project_id}")
async def get_project(
    project_id: int,
    user_context: Dict = Depends(require_read_permission),
    client: OpenProjectClient = Depends(get_openproject_client)
):
    """Get project via REST API."""
    logger.info("Project requested via REST API",
               project_id=project_id,
               user=user_context.get("user_id"))

    project_data = await client.get_project(project_id)
    return project_data.dict()


# SSE endpoint for real-time updates
@app.get("/sse")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time updates."""
    async def event_generator():
        """Generate SSE events."""
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"message": "Connected to MCP OpenProject Server"})
            }

            # Here you could implement real-time updates
            # For now, we'll send periodic health checks
            while True:
                await asyncio.sleep(30)  # Send update every 30 seconds

                # Check if client is still connected
                if await request.is_disconnected():
                    break

                # Send health update
                uptime = asyncio.get_event_loop().time() - server_state.start_time
                yield {
                    "event": "health_update",
                    "data": json.dumps({
                        "uptime_seconds": uptime,
                        "status": "healthy"
                    })
                }

        except asyncio.CancelledError:
            logger.info("SSE connection closed by client")
        except Exception as e:
            logger.error("SSE error", error=str(e))
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


# stdio mode handler for IDE integration - MCP JSON-RPC 2.0 compliant
async def handle_stdio_mode():
    """Handle stdio communication for IDE integration using MCP JSON-RPC 2.0 protocol."""
    logger.info("Starting stdio mode for IDE integration")

    # Send ready message to stderr
    print("MCP OpenProject Server (stdio mode) - Ready", file=sys.stderr)
    sys.stderr.flush()

    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )

            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                # Parse JSON-RPC 2.0 request
                request_data = json.loads(line)
                logger.info("STDIO request received", request=request_data)

                # Validate JSON-RPC 2.0 format
                if not isinstance(request_data, dict) or request_data.get("jsonrpc") != "2.0":
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_data.get("id", None),
                        "error": {
                            "code": -32600,
                            "message": "Invalid Request: Must be JSON-RPC 2.0"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    continue

                # Handle different MCP methods
                method = request_data.get("method")
                params = request_data.get("params", {})
                request_id = request_data.get("id")

                logger.info("Processing MCP request", method=method, params=params, id=request_id)

                if method == "initialize":
                    # Handle MCP initialization
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {
                                    "listChanged": True
                                },
                                "resources": {
                                    "subscribe": False,
                                    "listChanged": False
                                }
                            },
                            "serverInfo": {
                                "name": "mcp-openproject-server",
                                "version": "1.0.0"
                            }
                        }
                    }

                elif method == "tools/list":
                    # List available tools
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": [
                                {
                                    "name": "fetch_weekly_report",
                                    "description": "Fetch weekly report data for a specific project from OpenProject",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "project_id": {
                                                "type": "integer",
                                                "description": "The ID of the project to fetch data for",
                                                "minimum": 1
                                            },
                                            "week": {
                                                "type": "string",
                                                "description": "Optional week identifier (e.g., '2025-W41')",
                                                "pattern": "^202[0-9]-W([1-9]|[1-4][0-9]|5[0-3])$"
                                            }
                                        },
                                        "required": ["project_id"]
                                    }
                                },
                                {
                                    "name": "get_project_data",
                                    "description": "Get project data as a resource",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "project_id": {
                                                "type": "integer",
                                                "description": "The ID of the project",
                                                "minimum": 1
                                            }
                                        },
                                        "required": ["project_id"]
                                    }
                                }
                            ]
                        }
                    }

                elif method == "tools/call":
                    # Handle tool calls
                    tool_name = params.get("name")
                    tool_params = params.get("arguments", {})

                    if tool_name == "fetch_weekly_report":
                        tool_result = await handle_fetch_weekly_report(
                            tool_params,
                            server_state.openproject_client
                        )
                    elif tool_name == "get_project_data":
                        tool_result = await handle_get_project_data(
                            tool_params,
                            server_state.openproject_client
                        )
                    else:
                        tool_result = {"error": f"Unknown tool: {tool_name}"}

                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": tool_result.dict(exclude_none=True) if hasattr(tool_result, 'dict') else tool_result
                    }

                elif method == "resources/list":
                    # List available resources
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "resources": [
                                {
                                    "uri": "openproject://projects/{project_id}",
                                    "name": "Project Data",
                                    "description": "OpenProject data for a specific project",
                                    "mimeType": "application/json"
                                }
                            ]
                        }
                    }

                elif method in ["initialized", "notifications/tools/list_changed", "notifications/resources/list_changed"]:
                    # Handle notifications and acks
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": None
                    }

                else:
                    # Unknown method
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }

                # Send response
                response_json = json.dumps(response, separators=(',', ':'))  # Compact JSON
                print(response_json)
                sys.stdout.flush()

                logger.info("STDIO response sent", method=method, id=request_id)

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

            except Exception as e:
                logger.error("STDIO request failed", error=str(e), exc_info=True)
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id if 'request_id' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

    except KeyboardInterrupt:
        logger.info("STDIO mode interrupted")
    except Exception as e:
        logger.error("STDIO mode error", error=str(e), exc_info=True)


# Main entry point for different transport modes
async def run_server():
    """Run the server with configured transport mode."""
    config = server_state.config

    if config.transport_mode == "stdio":
        await handle_stdio_mode()
    else:
        # Run HTTP/SSE server
        uvicorn_config = uvicorn.Config(
            app=app,
            host=config.host,
            port=config.port,
            log_level=config.log_level.lower(),
            access_log=True
        )

        server = uvicorn.Server(uvicorn_config)

        logger.info(f"Starting HTTP server on {config.host}:{config.port}")
        await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())