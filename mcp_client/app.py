"""
MCP Client for AI Website Integration

FastAPI backend with langchain-mcp-adapters integration for MCP tool execution.
Supports both development (JSON) and production (database) configurations.
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader, Template
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy import Column, String, Integer, JSON, Text
from watchfiles import awatch
import httpx

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/mcp_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

# Database setup
Base = declarative_base()

class MCPService(Base):
    __tablename__ = "mcp_services"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), index=True)
    desc = Column(String(255), nullable=False)
    interaction_mode = Column(String(50))
    url = Column(String(255))
    endpoint = Column(String(255))
    api_key = Column(String(255))
    params = Column(JSON)
    auth = Column(JSON)

# Database engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Global configuration storage
mcp_configs: Dict[str, List[Dict[str, Any]]] = {}
mcp_clients: Dict[str, Optional[MultiServerMCPClient]] = {}

# Jinja2 environment
template_env = Environment(loader=FileSystemLoader("templates"))
weekly_report_template = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_database()
    await load_templates()
    await load_configurations()

    # Start config file watcher for development
    if os.path.exists("mcp_config.json"):
        asyncio.create_task(watch_config_file())

    yield

    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="MCP Client Service",
    description="AI Website MCP Integration with langchain-mcp-adapters",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models
class MCPRequest(BaseModel):
    desc: str = Field(..., description="MCP tool description")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    user_id: str = Field(default="global", description="User ID for isolation")

class MCPConfigRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    config: Dict[str, Any] = Field(..., description="MCP configuration")

class MCPConfigResponse(BaseModel):
    desc: str
    interaction_mode: str
    url: Optional[str]
    endpoint: Optional[str]
    params: Dict[str, Any]
    auth: Dict[str, Any]

class TemplateRequest(BaseModel):
    content: str = Field(..., description="Template content")
    user_id: str = Field(default="admin", description="User ID for authorization")

# Database operations
async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_config_from_db(user_id: str, desc: str) -> Optional[Dict[str, Any]]:
    """Get MCP configuration from database"""
    async with async_session() as session:
        result = await session.execute(
            "SELECT * FROM mcp_services WHERE user_id = :user_id AND desc = :desc",
            {"user_id": user_id, "desc": desc}
        )
        row = result.fetchone()
        if row:
            return {
                "desc": row.desc,
                "interaction_mode": row.interaction_mode,
                "url": row.url,
                "endpoint": row.endpoint,
                "api_key": row.api_key,
                "params": row.params or {},
                "auth": row.auth or {}
            }
    return None

async def save_config_to_db(user_id: str, config: Dict[str, Any]):
    """Save MCP configuration to database"""
    async with async_session() as session:
        await session.execute(
            """
            INSERT INTO mcp_services
            (user_id, desc, interaction_mode, url, endpoint, api_key, params, auth)
            VALUES (:user_id, :desc, :mode, :url, :endpoint, :api_key, :params, :auth)
            ON CONFLICT (user_id, desc)
            DO UPDATE SET
                interaction_mode = EXCLUDED.interaction_mode,
                url = EXCLUDED.url,
                endpoint = EXCLUDED.endpoint,
                api_key = EXCLUDED.api_key,
                params = EXCLUDED.params,
                auth = EXCLUDED.auth
            """,
            {
                "user_id": user_id,
                "desc": config["desc"],
                "mode": config["interaction_mode"],
                "url": config.get("url"),
                "endpoint": config.get("endpoint"),
                "api_key": config.get("api_key"),
                "params": json.dumps(config.get("params", {})),
                "auth": json.dumps(config.get("auth", {}))
            }
        )
        await session.commit()

# Configuration management
async def load_configurations():
    """Load configurations from database"""
    async with async_session() as session:
        result = await session.execute("SELECT * FROM mcp_services")
        for row in result.fetchall():
            user_id = row.user_id
            if user_id not in mcp_configs:
                mcp_configs[user_id] = []

            mcp_configs[user_id].append({
                "desc": row.desc,
                "interaction_mode": row.interaction_mode,
                "url": row.url,
                "endpoint": row.endpoint,
                "api_key": row.api_key,
                "params": row.params or {},
                "auth": row.auth or {}
            })

async def watch_config_file():
    """Watch mcp_config.json for changes (development mode)"""
    if os.path.exists("mcp_config.json"):
        async for changes in awatch("mcp_config.json"):
            try:
                with open("mcp_config.json", "r") as f:
                    mcp_configs["global"] = json.load(f)
                print("Configuration reloaded from file")
            except Exception as e:
                print(f"Error reloading configuration: {e}")

async def load_templates():
    """Load Jinja2 templates"""
    global weekly_report_template
    try:
        weekly_report_template = template_env.get_template("weekly_report.j2")
    except:
        # Create default template
        default_template = """
# Project Weekly Report
**Project**: {{ project.name }}
**Week**: {{ week }}
**Tasks**:
{% for task in work_packages %}
- {{ task.subject }} (Status: {{ task.status }})
{% endfor %}
"""
        weekly_report_template = Template(default_template)

# MCP Client management
async def get_mcp_client(user_id: str, config: Dict[str, Any]) -> MultiServerMCPClient:
    """Get or create MCP client for configuration"""
    cache_key = f"{user_id}_{config['desc']}"

    if cache_key not in mcp_clients:
        if config["interaction_mode"] == "stdio":
            # stdio mode - subprocess communication
            client_config = {
                config["desc"]: {
                    "command": [
                        "python", "mcp_openproject.py",
                        "--endpoint", config["endpoint"],
                        "--api-key", config["api_key"],
                        "--mode", "stdio"
                    ],
                    "transport": "stdio"
                }
            }
        else:
            # HTTP/SSE mode
            client_config = {
                config["desc"]: {
                    "url": config["url"],
                    "transport": config["interaction_mode"].replace("streamful_http", "streamable_http"),
                    "headers": {"Authorization": f"Bearer {config['api_key']}"}
                }
            }

        mcp_clients[cache_key] = MultiServerMCPClient(client_config)

    return mcp_clients[cache_key]

def validate_auth(auth_config: Dict[str, Any], provided_token: str) -> bool:
    """Validate authentication configuration"""
    if auth_config.get("type") == "api_key":
        return provided_token == auth_config.get("value")
    return False  # OAuth/JWT placeholder

def render_weekly_report(data: Dict[str, Any], week: str = "2025-W41") -> str:
    """Render weekly report using Jinja2 template"""
    if weekly_report_template:
        return weekly_report_template.render(
            project=data.get("project", {}),
            week=week,
            work_packages=data.get("work_packages", [])
        )
    return json.dumps(data, indent=2)

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}

@app.post("/mcp/{desc}")
async def execute_mcp_tool(
    desc: str,
    request: MCPRequest,
    background_tasks: BackgroundTasks
):
    """Execute MCP tool with given description"""
    try:
        # Get configuration (try database first, then JSON)
        config = await get_config_from_db(request.user_id, desc)
        if not config and request.user_id in mcp_configs:
            config = next(
                (c for c in mcp_configs[request.user_id] if c["desc"] == desc),
                None
            )

        if not config:
            raise HTTPException(status_code=404, detail=f"MCP configuration '{desc}' not found")

        # Validate authentication
        if not validate_auth(config.get("auth", {}), config.get("api_key", "")):
            raise HTTPException(status_code=401, detail="Authentication failed")

        # Get MCP client
        client = await get_mcp_client(request.user_id, config)

        # Execute tool
        tools = await client.get_tools()
        tool = next((t for t in tools if t.name == "fetch_weekly_report"), None)

        if not tool:
            raise HTTPException(status_code=404, detail="Tool 'fetch_weekly_report' not found")

        # Merge parameters
        params = {**config.get("params", {}), **request.params}

        # Execute tool
        result = await tool.ainvoke(params)

        # Render report
        week = params.get("week", "2025-W41")
        report = render_weekly_report(result, week)

        # Optional: Refine with LLM
        if OPENAI_API_KEY != "your-openai-api-key":
            try:
                llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
                prompt = PromptTemplate.from_template(
                    "Please refine and improve this weekly report for clarity and readability:\n\n{report}"
                )
                refined = await llm.ainvoke(prompt.format(report=report))
                report = refined.content
            except Exception as e:
                print(f"LLM refinement failed: {e}")

        return {
            "result": report,
            "raw_data": result,
            "tool": desc,
            "params": params
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp-config", response_model=MCPConfigResponse)
async def add_mcp_config(request: MCPConfigRequest):
    """Add or update MCP configuration"""
    try:
        # Save to database
        await save_config_to_db(request.user_id, request.config)

        # Update in-memory config
        if request.user_id not in mcp_configs:
            mcp_configs[request.user_id] = []

        # Remove existing config with same description
        mcp_configs[request.user_id] = [
            c for c in mcp_configs[request.user_id]
            if c["desc"] != request.config["desc"]
        ]

        # Add new config
        mcp_configs[request.user_id].append(request.config)

        return MCPConfigResponse(**request.config)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp-config", response_model=List[MCPConfigResponse])
async def list_mcp_configs(user_id: str = "global"):
    """List MCP configurations for user"""
    configs = mcp_configs.get(user_id, [])
    return [MCPConfigResponse(**config) for config in configs]

@app.delete("/mcp-config/{desc}")
async def delete_mcp_config(desc: str, user_id: str = "global"):
    """Delete MCP configuration"""
    try:
        # Remove from database
        async with async_session() as session:
            await session.execute(
                "DELETE FROM mcp_services WHERE user_id = :user_id AND desc = :desc",
                {"user_id": user_id, "desc": desc}
            )
            await session.commit()

        # Remove from in-memory config
        if user_id in mcp_configs:
            mcp_configs[user_id] = [
                c for c in mcp_configs[user_id]
                if c["desc"] != desc
            ]

        return {"status": "deleted", "desc": desc}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/templates/{template_name}")
async def update_template(template_name: str, request: TemplateRequest):
    """Update Jinja2 template"""
    try:
        # Simple authorization check
        if request.user_id != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        # Save template
        template_path = f"templates/{template_name}.j2"
        os.makedirs("templates", exist_ok=True)

        with open(template_path, "w") as f:
            f.write(request.content)

        # Reload templates
        await load_templates()

        return {"status": "updated", "template": template_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/{template_name}")
async def get_template(template_name: str):
    """Get Jinja2 template content"""
    try:
        template_path = f"templates/{template_name}.j2"
        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail="Template not found")

        with open(template_path, "r") as f:
            content = f.read()

        return {"template": template_name, "content": content}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)