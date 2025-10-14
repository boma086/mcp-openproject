#!/usr/bin/env python3
"""
MCP Toolkit - 简化FastAPI_MCP开发的工具集

这个模块提供了一组装饰器和工具函数，简化MCP工具的开发，
同时保持FastAPI_MCP的灵活性和企业级特性。
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field
from fastapi import HTTPException, Depends
import structlog

logger = structlog.get_logger(__name__)


class MCPToolType(str, Enum):
    """MCP工具类型枚举"""
    READ = "read"
    WRITE = "write"
    ACTION = "action"


@dataclass
class MCPToolConfig:
    """MCP工具配置"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    tool_type: MCPToolType = MCPToolType.READ
    requires_auth: bool = True
    audit_log: bool = True
    rate_limit: Optional[int] = None  # 每分钟调用次数限制
    timeout: Optional[int] = None  # 超时时间（秒）
    retry_count: int = 0  # 重试次数


class MCPToolRegistry:
    """MCP工具注册表"""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._configs: Dict[str, MCPToolConfig] = {}
        self._middleware_stack: List[Callable] = []

    def register_tool(
        self,
        config: MCPToolConfig,
        func: Callable
    ) -> None:
        """注册MCP工具"""
        self._tools[config.name] = func
        self._configs[config.name] = config

        logger.info("MCP tool registered",
                   tool_name=config.name,
                   tool_type=config.tool_type,
                   requires_auth=config.requires_auth)

    def get_tool(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        return self._tools.get(name)

    def get_config(self, name: str) -> Optional[MCPToolConfig]:
        """获取工具配置"""
        return self._configs.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具（用于MCP协议响应）"""
        return [
            {
                "name": config.name,
                "description": config.description,
                "inputSchema": config.input_schema
            }
            for config in self._configs.values()
        ]

    def add_middleware(self, middleware: Callable) -> None:
        """添加中间件"""
        self._middleware_stack.append(middleware)

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工具（带中间件支持）"""
        if tool_name not in self._tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        func = self._tools[tool_name]
        config = self._configs[tool_name]

        # 构建执行上下文
        execution_context = {
            "tool_name": tool_name,
            "params": params,
            "config": config,
            "user_context": context or {}
        }

        # 应用中间件链
        for middleware in self._middleware_stack:
            execution_context = await middleware(execution_context)

        # 执行工具
        try:
            if config.timeout:
                result = await asyncio.wait_for(
                    func(**params),
                    timeout=config.timeout
                )
            else:
                result = await func(**params)

            logger.info("MCP tool executed successfully",
                       tool_name=tool_name,
                       params_keys=list(params.keys()),
                       result_type=type(result).__name__)

            return {"data": result}

        except asyncio.TimeoutError:
            logger.error("MCP tool execution timeout",
                        tool_name=tool_name,
                        timeout=config.timeout)
            raise HTTPException(status_code=408, detail="Tool execution timeout")
        except Exception as e:
            logger.error("MCP tool execution failed",
                        tool_name=tool_name,
                        error=str(e),
                        exc_info=True)
            raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


# 全局工具注册表
tool_registry = MCPToolRegistry()


def mcp_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    tool_type: MCPToolType = MCPToolType.READ,
    requires_auth: bool = True,
    audit_log: bool = True,
    rate_limit: Optional[int] = None,
    timeout: Optional[int] = None,
    retry_count: int = 0
) -> Callable:
    """
    MCP工具装饰器

    使用示例:
    @mcp_tool(
        name="get_project",
        description="获取项目信息",
        input_schema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "minimum": 1}
            },
            "required": ["project_id"]
        },
        tool_type=MCPToolType.READ,
        timeout=30
    )
    async def get_project(project_id: int, client: OpenProjectClient = Depends(get_openproject_client)):
        return await client.get_project(project_id)
    """
    def decorator(func: Callable) -> Callable:
        config = MCPToolConfig(
            name=name,
            description=description,
            input_schema=input_schema,
            tool_type=tool_type,
            requires_auth=requires_auth,
            audit_log=audit_log,
            rate_limit=rate_limit,
            timeout=timeout,
            retry_count=retry_count
        )

        # 注册工具
        tool_registry.register_tool(config, func)

        # 添加包装函数以保持原始函数签名
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # 添加MCP元数据
        wrapper._mcp_config = config
        wrapper._is_mcp_tool = True

        return wrapper

    return decorator


# 预定义的中间件
async def auth_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
    """认证中间件"""
    config = context["config"]
    if config.requires_auth:
        user_context = context.get("user_context", {})
        if not user_context.get("authenticated"):
            raise HTTPException(status_code=401, detail="Authentication required")

    return context


async def audit_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
    """审计中间件"""
    config = context["config"]
    if config.audit_log:
        logger.info("MCP tool audit log",
                   tool_name=context["tool_name"],
                   user_id=context["user_context"].get("user_id"),
                   timestamp=asyncio.get_event_loop().time(),
                   params_keys=list(context["params"].keys()))

    return context


async def rate_limit_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
    """限流中间件"""
    config = context["config"]
    if config.rate_limit:
        # 这里可以实现具体的限流逻辑
        # 例如使用Redis进行分布式限流
        pass

    return context


async def validation_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
    """参数验证中间件"""
    config = context["config"]
    params = context["params"]

    # 基于input_schema进行参数验证
    # 这里可以使用Pydantic进行自动验证
    # 简化示例，实际实现会更复杂

    return context


def setup_default_middlewares():
    """设置默认中间件"""
    tool_registry.add_middleware(auth_middleware)
    tool_registry.add_middleware(validation_middleware)
    tool_registry.add_middleware(rate_limit_middleware)
    tool_registry.add_middleware(audit_middleware)


# 工具生成器
def generate_tool_from_openapi(
    endpoint_path: str,
    method: str,
    openapi_spec: Dict[str, Any]
) -> Optional[MCPToolConfig]:
    """
    从OpenAPI规范生成MCP工具配置

    Args:
        endpoint_path: API端点路径
        method: HTTP方法
        openapi_spec: OpenAPI规范字典

    Returns:
        MCPToolConfig对象或None
    """
    try:
        # 解析OpenAPI规范
        paths = openapi_spec.get("paths", {})
        endpoint_spec = paths.get(endpoint_path, {})
        method_spec = endpoint_spec.get(method.lower(), {})

        if not method_spec:
            return None

        # 提取信息
        operation_id = method_spec.get("operationId", f"{method}_{endpoint_path}")
        summary = method_spec.get("summary", "")
        description = method_spec.get("description", summary)

        # 转换参数schema
        parameters = method_spec.get("parameters", [])
        request_body = method_spec.get("requestBody", {})

        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # 处理路径参数
        for param in parameters:
            if param.get("in") == "path":
                param_name = param["name"]
                param_schema = param.get("schema", {})
                input_schema["properties"][param_name] = param_schema
                if param.get("required", False):
                    input_schema["required"].append(param_name)

        # 处理请求体
        if request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            input_schema.update(schema)

        # 确定工具类型
        tool_type = MCPToolType.READ
        if method.lower() in ["post", "put", "patch", "delete"]:
            tool_type = MCPToolType.WRITE

        return MCPToolConfig(
            name=operation_id,
            description=description,
            input_schema=input_schema,
            tool_type=tool_type,
            requires_auth=True,
            audit_log=True
        )

    except Exception as e:
        logger.error("Failed to generate tool from OpenAPI",
                    endpoint_path=endpoint_path,
                    method=method,
                    error=str(e))
        return None


# 示例使用
if __name__ == "__main__":
    # 设置默认中间件
    setup_default_middlewares()

    # 示例工具定义
    @mcp_tool(
        name="get_project_info",
        description="获取项目详细信息",
        input_schema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "项目ID",
                    "minimum": 1
                },
                "include_details": {
                    "type": "boolean",
                    "description": "是否包含详细信息",
                    "default": False
                }
            },
            "required": ["project_id"]
        },
        tool_type=MCPToolType.READ,
        timeout=30
    )
    async def example_get_project(
        project_id: int,
        include_details: bool = False,
        client=None  # 这里会被依赖注入替换
    ):
        """示例工具函数"""
        # 模拟API调用
        await asyncio.sleep(0.1)
        return {
            "id": project_id,
            "name": f"项目 {project_id}",
            "description": "这是一个示例项目",
            "details": {"created_at": "2025-01-01"} if include_details else None
        }

    # 列出所有工具
    tools = tool_registry.list_tools()
    print("已注册的MCP工具:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")

    # 执行工具示例
    async def test_execution():
        result = await tool_registry.execute_tool(
            "get_project_info",
            {"project_id": 123, "include_details": True},
            {"user_id": "test_user", "authenticated": True}
        )
        print("执行结果:", result)

    # 运行测试
    asyncio.run(test_execution())