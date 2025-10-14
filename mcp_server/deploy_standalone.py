#!/usr/bin/env python3
"""
Standalone deployment script for MCP OpenProject stdio server
Creates a self-contained script that can be run with uvx or pipx
"""
import sys
import json
import os
from pathlib import Path

# Create standalone script content
STANDALONE_SCRIPT = '''#!/usr/bin/env python3
"""
Standalone MCP OpenProject stdio server for uvx/pipx deployment
Auto-generated script that includes all necessary dependencies
"""

import asyncio
import json
import sys
import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

# Check required dependencies
try:
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
    import httpx
    import backoff
    from pydantic import BaseModel, Field
except ImportError as e:
    print(f"Missing required dependency: {e}", file=sys.stderr)
    print("Please install with: pip install mcp httpx backoff pydantic", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_openproject_standalone.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
@dataclass
class ServerConfig:
    openproject_base_url: str
    openproject_api_key: str
    encryption_key: str

    def __post_init__(self):
        if not self.openproject_base_url:
            raise ValueError("OPENPROJECT_BASE_URL is required")
        if not self.openproject_api_key:
            raise ValueError("OPENPROJECT_API_KEY is required")
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY is required")

def load_config() -> ServerConfig:
    """Load configuration from environment variables"""
    return ServerConfig(
        openproject_base_url=os.getenv('OPENPROJECT_BASE_URL', ''),
        openproject_api_key=os.getenv('OPENPROJECT_API_KEY', ''),
        encryption_key=os.getenv('ENCRYPTION_KEY', '')
    )

# Pydantic models
class WorkPackageInfo(BaseModel):
    id: Optional[int] = None
    subject: str = Field(..., description="Work package subject")
    status: Optional[str] = Field(None, description="Work package status")
    priority: Optional[str] = Field(None, description="Work package priority")
    assignee: Optional[str] = Field(None, description="Assignee name")
    due_date: Optional[str] = Field(None, description="Due date")
    created_at: Optional[str] = Field(None, description="Creation date")
    updated_at: Optional[str] = Field(None, description="Last update date")

class ProjectInfo(BaseModel):
    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    identifier: str = Field(..., description="Project identifier")
    created_at: Optional[str] = Field(None, description="Creation date")
    updated_at: Optional[str] = Field(None, description="Last update date")

class WeeklyReportData(BaseModel):
    project: ProjectInfo
    work_packages: List[WorkPackageInfo]
    week: str
    summary: Optional[str] = None

# HTTP client for OpenProject API
class OpenProjectHTTPClient:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.openproject_base_url,
            timeout=httpx.Timeout(30),
            headers={
                "User-Agent": "MCP-OpenProject-Standalone/1.0",
                "Accept": "application/hal+json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.openproject_api_key}"
            }
        )

    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get project information"""
        response = await self.client.get(f"/api/v3/projects/{project_id}")
        response.raise_for_status()
        return response.json()

    async def get_work_packages(self, project_id: int, filters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Get work packages for a project"""
        params = {}
        if filters:
            params['filters'] = json.dumps(filters)

        response = await self.client.get("/api/v3/work_packages", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('_embedded', {}).get('elements', [])

    async def close(self):
        await self.client.aclose()

# Error classes
class OpenProjectClientError(Exception):
    pass

# Main client
class OpenProjectClient:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.http_client = OpenProjectHTTPClient(config)

    async def get_project(self, project_id: int) -> ProjectInfo:
        try:
            data = await self.http_client.get_project(project_id)
            return ProjectInfo(
                id=data['id'],
                name=data['name'],
                identifier=data['identifier'],
                created_at=data.get('createdAt'),
                updated_at=data.get('updatedAt')
            )
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            raise OpenProjectClientError(f"Failed to get project {project_id}: {e}")

    async def get_work_packages(self, project_id: int, filters: Optional[List[Dict[str, Any]]] = None) -> List[WorkPackageInfo]:
        try:
            data = await self.http_client.get_work_packages(project_id, filters)
            work_packages = []
            for wp in data:
                work_packages.append(WorkPackageInfo(
                    id=wp.get('id'),
                    subject=wp.get('subject', ''),
                    status=wp.get('status', {}).get('name') if wp.get('status') else None,
                    priority=wp.get('priority', {}).get('name') if wp.get('priority') else None,
                    assignee=wp.get('assignee', {}).get('name') if wp.get('assignee') else None,
                    due_date=wp.get('dueDate'),
                    created_at=wp.get('createdAt'),
                    updated_at=wp.get('updatedAt')
                ))
            return work_packages
        except Exception as e:
            logger.error(f"Failed to get work packages for project {project_id}: {e}")
            raise OpenProjectClientError(f"Failed to get work packages for project {project_id}: {e}")

    async def get_weekly_report(self, project_id: int, week: Optional[str] = None) -> WeeklyReportData:
        try:
            project, work_packages = await asyncio.gather(
                self.get_project(project_id),
                self.get_work_packages(project_id)
            )
            return WeeklyReportData(
                project=project,
                work_packages=work_packages,
                week=week or "current",
                summary=f"Found {len(work_packages)} work packages"
            )
        except Exception as e:
            logger.error(f"Failed to generate weekly report for project {project_id}: {e}")
            raise

    async def close(self):
        await self.http_client.close()

# Global client
openproject_client: Optional[OpenProjectClient] = None

# Create MCP server
server = Server(
    name="openproject-mcp-server",
    version="1.0.0",
    instructions="OpenProject MCP Server providing access to project data and work packages"
)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
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
    """Handle tool calls"""
    global openproject_client

    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        # Initialize client if not already done
        if openproject_client is None:
            logger.info("Initializing OpenProject client")
            config = load_config()
            openproject_client = OpenProjectClient(config)

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

    except Exception as e:
        logger.error(f"Error for tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({"error": f"Error: {str(e)}"})
            )]
        )

async def main():
    """Main entry point"""
    logger.info("Starting MCP OpenProject Standalone Server (stdio mode)")

    try:
        # Validate configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        logger.info(f"OpenProject URL: {config.openproject_base_url}")

        # Send ready message
        print("MCP OpenProject Standalone Server (stdio mode) - Ready", file=sys.stderr)
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
'''

def create_standalone_script():
    """Create the standalone script"""
    script_path = Path(__file__).parent / "mcp_openproject_standalone.py"

    print("📦 Creating standalone MCP OpenProject server...")

    with open(script_path, 'w') as f:
        f.write(STANDALONE_SCRIPT)

    # Make script executable
    script_path.chmod(0o755)

    print(f"✅ Standalone script created: {script_path}")
    print(f"   Size: {len(STANDALONE_SCRIPT)} characters")

    return script_path

def create_requirements_file():
    """Create requirements file for standalone deployment"""
    requirements = [
        "mcp>=1.17.0",
        "httpx>=0.28.0",
        "backoff>=2.2.1",
        "pydantic>=2.11.0"
    ]

    req_path = Path(__file__).parent / "requirements_standalone.txt"

    with open(req_path, 'w') as f:
        f.write("# Standalone MCP OpenProject Server Requirements\n")
        f.write("# For use with uvx or pipx\n\n")
        for req in requirements:
            f.write(f"{req}\n")

    print(f"✅ Requirements file created: {req_path}")
    return req_path

def create_deployment_configs():
    """Create deployment configuration examples"""
    configs = {
        "uvx": {
            "command": "uvx",
            "args": ["run", "/path/to/mcp-openproject_standalone.py"],
            "description": "Run with uvx (recommended)"
        },
        "pipx": {
            "command": "pipx",
            "args": ["run", "/path/to/mcp-openproject_standalone.py"],
            "description": "Run with pipx"
        },
        "direct": {
            "command": "python3",
            "args": ["/path/to/mcp-openproject_standalone.py"],
            "description": "Run directly with Python"
        }
    }

    config_path = Path(__file__).parent / "deployment_configs.json"

    with open(config_path, 'w') as f:
        json.dump(configs, f, indent=2)

    print(f"✅ Deployment configs created: {config_path}")
    return config_path

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 MCP OpenProject Standalone Deployment Generator")
    print("=" * 60)

    try:
        # Create standalone script
        script_path = create_standalone_script()

        # Create requirements file
        req_path = create_requirements_file()

        # Create deployment configs
        config_path = create_deployment_configs()

        print("\n" + "=" * 60)
        print("📋 Deployment Instructions")
        print("=" * 60)

        print("\n🔧 Installation:")
        print("```bash")
        print("# For uvx (recommended)")
        print("uvx install -r requirements_standalone.txt")
        print("")
        print("# For pipx")
        print("pipx install -r requirements_standalone.txt")
        print("")
        print("# Or run directly")
        print("python3 mcp_openproject_standalone.py")
        print("```")

        print("\n🌐 WindSurf Configuration:")
        print("```json")
        print("{")
        print('  "mcpServers": {')
        print('    "openproject": {')
        print('      "command": "uvx",')
        print('      "args": ["run", "' + str(script_path) + '"],')
        print('      "env": {')
        print('        "OPENPROJECT_BASE_URL": "https://your.openproject.instance",')
        print('        "OPENPROJECT_API_KEY": "your-api-key",')
        print('        "ENCRYPTION_KEY": "your-encryption-key"')
        print('      }')
        print("    }")
        print("  }")
        print("}")
        print("```")

        print("\n📊 Benefits:")
        print("✅ No virtual environment setup required")
        print("✅ Self-contained with all dependencies")
        print("✅ Works with uvx/pipx for easy deployment")
        print("✅ Enhanced logging to /tmp/mcp_openproject_standalone.log")
        print("✅ Direct HTTP client implementation (no external dependencies)")

        print("\n🎯 Next Steps:")
        print("1. Copy the standalone script to your deployment location")
        print("2. Set environment variables in your WindSurf config")
        print("3. Test the connection")
        print("4. Monitor logs at /tmp/mcp_openproject_standalone.log")

        return 0

    except Exception as e:
        print(f"❌ Error creating deployment: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())