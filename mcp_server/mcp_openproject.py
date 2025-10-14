#!/usr/bin/env python3
"""
MCP OpenProject Server v2.0 - Production-Ready Architecture

This is the new main entry point that replaces the original mcp_openproject.py
with a FastAPI-based architecture addressing all critical security and performance
issues identified in the backend architect review.

Key Improvements:
- FastAPI base with MCP protocol wrapper (instead of direct FastMCP usage)
- Secure configuration management (no global variables)
- Connection pooling and proper resource management
- Structured error handling with HTTP status codes
- Production-ready security with authentication/authorization
- Comprehensive monitoring and observability
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path
import structlog

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.simple_config import load_config, ServerConfig
from src.security import initialize_security, SecurityError
from src.fastapi_mcp_server import run_server, server_state
from src.openproject_client import OpenProjectClientError

# Configure structured logging
def setup_logging(config: ServerConfig):
    """Setup structured logging configuration."""
    import logging
    import sys

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if config.log_format == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level)
    )

    logger = structlog.get_logger(__name__)
    logger.info("Logging configured",
               level=config.log_level,
               format=config.log_format)


def validate_environment():
    """Validate environment and dependencies."""
    logger = structlog.get_logger(__name__)

    # Check Python version
    if sys.version_info < (3, 9):
        logger.error("Python 3.9+ is required")
        sys.exit(1)

    # Check required environment variables
    required_vars = ["OPENPROJECT_BASE_URL", "OPENPROJECT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error("Missing required environment variables",
                    variables=missing_vars)
        sys.exit(1)

    # Validate OpenProject endpoint format
    endpoint = os.getenv("OPENPROJECT_BASE_URL")
    if not endpoint.startswith(("http://", "https://")):
        logger.error("OPENPROJECT_BASE_URL must start with http:// or https://")
        sys.exit(1)

    logger.info("Environment validation passed")


def print_startup_banner(config: ServerConfig):
    """Print startup banner with configuration summary."""
    # Get transport mode from environment (not in simple config)
    transport_mode = os.getenv('MCP_MODE', 'stdio')

    print("=" * 60)
    print("🚀 MCP OpenProject Server v2.0 - Production Ready")
    print("=" * 60)
    print(f"📡 Transport Mode: {transport_mode.upper()}")
    print(f"🌐 OpenProject Endpoint: {config.openproject_base_url}")
    print(f"🖥️  Server: {config.host}:{config.port}")
    print(f"🔐 Debug Mode: {config.debug}")
    print(f"📝 Log Level: {config.log_level}")

    if transport_mode != "stdio":
        print(f"🌐 HTTP Server: http://{config.host}:{config.port}")
        print(f"📊 Metrics: http://{config.host}:{config.metrics_port}/metrics")
        print(f"❤️  Health Check: http://{config.host}:{config.port}/health")
        print(f"🛠️  API Docs: http://{config.host}:{config.port}/docs")

    print("=" * 60)


async def start_server():
    """Start the MCP server with proper initialization."""
    try:
        # Load and validate configuration
        config = load_config()
        setup_logging(config)

        logger = structlog.get_logger(__name__)
        logger.info("Starting MCP OpenProject Server v2.0",
                   version="2.0.0",
                   transport_mode=config.transport_mode)

        # Validate environment
        validate_environment()

        # Initialize security (config not needed, uses env vars directly)
        try:
            initialize_security()
            logger.info("Security module initialized")
        except Exception as e:
            logger.error("Failed to initialize security module", error=str(e))
            sys.exit(1)

        # Initialize server state
        await server_state.initialize(config)

        # Print startup banner
        if config.transport_mode != "stdio":
            print_startup_banner(config)

        # Start the server
        await run_server()

    except KeyboardInterrupt:
        logger = structlog.get_logger(__name__)
        logger.info("Server stopped by user")
    except Exception as e:
        logger = structlog.get_logger(__name__)
        logger.error("Server startup failed", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if server_state.openproject_client:
            await server_state.cleanup()


def main():
    """Main entry point for the MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="MCP OpenProject Server v2.0 - Production Ready",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # HTTP mode with environment variables
  python mcp_openproject.py --mode http --port 8000

  # stdio mode for IDE integration
  python mcp_openproject.py --mode stdio

  # SSE mode for real-time updates
  python mcp_openproject.py --mode sse --port 8000

  # Development mode with debug logging
  python mcp_openproject.py --mode http --debug

Environment Variables:
  OPENPROJECT_BASE_URL     OpenProject instance URL (required)
  OPENPROJECT_API_KEY     OpenProject API key (required)
  MCP_HOST               Server host (default: 0.0.0.0)
  MCP_PORT               Server port (default: 8000)
  MCP_DEBUG              Enable debug mode (default: false)
  LOG_LEVEL              Logging level (default: INFO)
  LOG_FORMAT             Log format: json or text (default: json)
        """
    )

    parser.add_argument(
        "--mode",
        choices=["stdio", "http", "sse"],
        default=os.getenv("MCP_MODE", "stdio"),
        help="Communication mode (default: stdio, env: MCP_MODE)"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        help="Server host for HTTP/SSE modes (default: 0.0.0.0, env: MCP_HOST)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8000")),
        help="Server port for HTTP/SSE modes (default: 8000, env: MCP_PORT)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("MCP_DEBUG", "false").lower() == "true",
        help="Enable debug mode (env: MCP_DEBUG)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (default: INFO, env: LOG_LEVEL)"
    )
    parser.add_argument(
        "--log-format",
        choices=["json", "text"],
        default=os.getenv("LOG_FORMAT", "json"),
        help="Log format (default: json, env: LOG_FORMAT)"
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="MCP OpenProject Server v2.0.0"
    )

    args = parser.parse_args()

    # Override environment with command line arguments
    if args.mode:
        os.environ["MCP_MODE"] = args.mode
    if args.host:
        os.environ["MCP_HOST"] = args.host
    if args.port:
        os.environ["MCP_PORT"] = str(args.port)
    if args.debug:
        os.environ["MCP_DEBUG"] = "true"
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    if args.log_format:
        os.environ["LOG_FORMAT"] = args.log_format

    # Start the server
    asyncio.run(start_server())


if __name__ == "__main__":
    main()