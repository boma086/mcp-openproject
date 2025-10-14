#!/usr/bin/env python3
"""
优化的FastAPI MCP服务器

这个示例展示了如何使用mcp_toolkit来简化MCP服务器的开发，
同时保持企业级的特性和灵活性。
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import structlog

from mcp_toolkit import (
    mcp_tool, MCPToolType, tool_registry, setup_default_middlewares
)
from openproject_client import OpenProjectClient
from simple_config import load_config, ServerConfig

logger = structlog.get_logger(__name__)


# MCP协议模型
class MCPToolCall(BaseModel):
    """MCP工具调用请求"""
    tool: str = Field(..., description="工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class MCPResponse(BaseModel):
    """MCP响应"""
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="响应元数据")


# 全局状态
class OptimizedServerState:
    """优化的服务器状态管理"""

    def __init__(self):
        self.config: Optional[ServerConfig] = None
        self.openproject_client: Optional[OpenProjectClient] = None
        self.initialized: bool = False

    async def initialize(self, config: ServerConfig):
        """初始化服务器状态"""
        self.config = config
        # 这里会初始化OpenProject客户端
        # self.openproject_client = await create_openproject_client(config)
        self.initialized = True

    async def cleanup(self):
        """清理服务器资源"""
        if self.openproject_client:
            await self.openproject_client.close()


server_state = OptimizedServerState()


# 创建FastAPI应用
def create_app() -> FastAPI:
    """创建优化的FastAPI应用"""
    app = FastAPI(
        title="优化的MCP OpenProject服务器",
        description="使用mcp_toolkit优化的企业级MCP服务器",
        version="2.1.0"
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 设置默认中间件
    setup_default_middlewares()

    return app


app = create_app()


# 异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error("Unexpected error", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# 依赖函数
async def get_openproject_client() -> OpenProjectClient:
    """获取OpenProject客户端依赖"""
    if not server_state.openproject_client:
        raise HTTPException(status_code=503, detail="OpenProject客户端未初始化")
    return server_state.openproject_client


async def require_authentication() -> Dict[str, Any]:
    """认证依赖"""
    # 这里实现具体的认证逻辑
    # 返回用户上下文
    return {
        "user_id": "demo_user",
        "authenticated": True,
        "permissions": ["read", "write"]
    }


# MCP工具定义
@mcp_tool(
    name="get_project",
    description="获取OpenProject项目信息",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "项目ID",
                "minimum": 1
            }
        },
        "required": ["project_id"]
    },
    tool_type=MCPToolType.READ,
    timeout=30
)
async def get_project(
    project_id: int,
    client: OpenProjectClient = Depends(get_openproject_client)
) -> Dict[str, Any]:
    """获取项目信息的MCP工具"""
    # 模拟API调用
    await asyncio.sleep(0.1)

    return {
        "id": project_id,
        "name": f"项目 {project_id}",
        "identifier": f"project-{project_id}",
        "status": "active",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-15T00:00:00Z"
    }


@mcp_tool(
    name="get_work_packages",
    description="获取项目的工作包列表",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "项目ID",
                "minimum": 1
            },
            "status": {
                "type": "string",
                "description": "状态过滤",
                "enum": ["open", "closed", "all"],
                "default": "open"
            },
            "limit": {
                "type": "integer",
                "description": "返回数量限制",
                "minimum": 1,
                "maximum": 100,
                "default": 20
            }
        },
        "required": ["project_id"]
    },
    tool_type=MCPToolType.READ,
    timeout=45
)
async def get_work_packages(
    project_id: int,
    status: str = "open",
    limit: int = 20,
    client: OpenProjectClient = Depends(get_openproject_client)
) -> Dict[str, Any]:
    """获取工作包列表的MCP工具"""
    # 模拟API调用
    await asyncio.sleep(0.2)

    # 模拟工作包数据
    work_packages = [
        {
            "id": i,
            "subject": f"工作包 {i}",
            "status": "open" if i % 2 == 0 else "closed",
            "priority": "high" if i % 3 == 0 else "normal",
            "due_date": f"2025-0{(i % 12) + 1}-15"
        }
        for i in range(1, min(limit + 1, 11))
    ]

    # 应用状态过滤
    if status != "all":
        work_packages = [wp for wp in work_packages if wp["status"] == status]

    return {
        "project_id": project_id,
        "work_packages": work_packages,
        "total_count": len(work_packages),
        "status_filter": status
    }


@mcp_tool(
    name="create_work_package",
    description="创建新的工作包",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "项目ID",
                "minimum": 1
            },
            "subject": {
                "type": "string",
                "description": "工作包主题",
                "minLength": 1,
                "maxLength": 255
            },
            "description": {
                "type": "string",
                "description": "工作包描述",
                "maxLength": 1000
            },
            "type_id": {
                "type": "integer",
                "description": "工作包类型ID",
                "minimum": 1
            },
            "status_id": {
                "type": "integer",
                "description": "状态ID",
                "minimum": 1
            },
            "priority": {
                "type": "string",
                "description": "优先级",
                "enum": ["low", "normal", "high", "urgent"],
                "default": "normal"
            }
        },
        "required": ["project_id", "subject", "type_id", "status_id"]
    },
    tool_type=MCPToolType.WRITE,
    timeout=60
)
async def create_work_package(
    project_id: int,
    subject: str,
    type_id: int,
    status_id: int,
    description: Optional[str] = None,
    priority: str = "normal",
    client: OpenProjectClient = Depends(get_openproject_client)
) -> Dict[str, Any]:
    """创建工作包的MCP工具"""
    # 模拟创建操作
    await asyncio.sleep(0.3)

    # 模拟新创建的工作包
    new_work_package = {
        "id": 999,  # 模拟新ID
        "project_id": project_id,
        "subject": subject,
        "description": description,
        "type_id": type_id,
        "status_id": status_id,
        "priority": priority,
        "created_at": "2025-10-14T10:00:00Z",
        "updated_at": "2025-10-14T10:00:00Z"
    }

    logger.info("Work package created",
               project_id=project_id,
               subject=subject,
               work_package_id=new_work_package["id"])

    return new_work_package


# API端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "server_type": "optimized_fastapi_mcp",
        "tools_count": len(tool_registry.list_tools())
    }


@app.get("/mcp/tools")
async def list_mcp_tools(user_context: Dict = Depends(require_authentication)):
    """列出可用的MCP工具"""
    tools = tool_registry.list_tools()

    logger.info("MCP tools listed",
               count=len(tools),
               user=user_context.get("user_id"))

    return {"tools": tools}


@app.post("/mcp/tools/{tool_name}")
async def call_mcp_tool(
    tool_name: str,
    request: MCPToolCall,
    user_context: Dict = Depends(require_authentication)
):
    """调用MCP工具"""
    logger.info("MCP tool called",
               tool=tool_name,
               params=request.params,
               user=user_context.get("user_id"))

    try:
        result = await tool_registry.execute_tool(
            tool_name,
            request.params,
            user_context
        )

        return MCPResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("MCP tool execution failed",
                    tool=tool_name,
                    error=str(e),
                    exc_info=True)

        return MCPResponse(
            error=f"Tool execution failed: {str(e)}",
            metadata={"tool_name": tool_name}
        )


# stdio模式支持
async def handle_stdio_mode():
    """处理stdio模式通信"""
    logger.info("Starting optimized stdio mode")

    print("优化的MCP OpenProject服务器 (stdio模式) - 就绪", file=sys.stderr)
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
                request_data = json.loads(line)

                # 验证JSON-RPC 2.0格式
                if not isinstance(request_data, dict) or request_data.get("jsonrpc") != "2.0":
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_data.get("id"),
                        "error": {
                            "code": -32600,
                            "message": "Invalid Request: Must be JSON-RPC 2.0"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    continue

                method = request_data.get("method")
                params = request_data.get("params", {})
                request_id = request_data.get("id")

                # 使用工具注册表处理请求
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {"listChanged": True},
                                "resources": {"subscribe": False, "listChanged": False}
                            },
                            "serverInfo": {
                                "name": "optimized-mcp-openproject-server",
                                "version": "2.1.0"
                            }
                        }
                    }

                elif method == "tools/list":
                    tools = tool_registry.list_tools()
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": tools}
                    }

                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})

                    try:
                        result = await tool_registry.execute_tool(
                            tool_name,
                            arguments,
                            {"user_id": "stdio_user", "authenticated": True}
                        )

                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result.get("data") if result.get("data") else result
                        }
                    except Exception as e:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": str(e)
                            }
                        }

                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }

                # 发送响应
                print(json.dumps(response, separators=(',', ':')))
                sys.stdout.flush()

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
                    "id": request_data.get("id") if 'request_data' in locals() else None,
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


# 主入口点
async def run_optimized_server():
    """运行优化的服务器"""
    # 加载配置
    config = load_config()
    await server_state.initialize(config)

    logger.info("Optimized MCP OpenProject Server started",
               version="2.1.0",
               transport_mode=config.transport_mode,
               tools_count=len(tool_registry.list_tools()))

    if config.transport_mode == "stdio":
        await handle_stdio_mode()
    else:
        # HTTP模式
        uvicorn_config = uvicorn.Config(
            app=app,
            host=config.host,
            port=config.port,
            log_level="info"
        )

        server = uvicorn.Server(uvicorn_config)
        await server.serve()


if __name__ == "__main__":
    asyncio.run(run_optimized_server())