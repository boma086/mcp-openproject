"""
MCP OpenProject CLI - Command Line Interface

Provides command line interface for MCP OpenProject server operations.
Supports command format: mcp-openproject server --stdio
"""

import argparse
import asyncio
import sys
import os
import logging
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server.src.config import ServerConfig, load_config
from mcp_server.transports.stdio import StdioTransport
from mcp_server.transports.http import HttpTransport
from mcp_server.transports.sse import SseTransport


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-openproject",
        description="MCP OpenProject Server - CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-openproject server --stdio                    # Run in stdio mode (for MCP clients)
  mcp-openproject server --http --port 8000          # Run in HTTP mode
  mcp-openproject server --sse --port 8001          # Run in SSE mode
  mcp-openproject config                              # Show current configuration
  mcp-openproject status                             # Check server status
  mcp-openproject test                               # Run tests
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run MCP server")
    server_parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run in stdio mode (for MCP client integration)"
    )
    server_parser.add_argument(
        "--http",
        action="store_true",
        help="Run in HTTP mode"
    )
    server_parser.add_argument(
        "--sse",
        action="store_true",
        help="Run in SSE mode"
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    server_parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost)"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration")

    # Status command
    status_parser = subparsers.add_parser("status", help="Check server status")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")

    # Global arguments
    parser.add_argument(
        "--endpoint",
        type=str,
        help="OpenProject base URL (default: OPENPROJECT_BASE_URL env var)"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenProject API key (default: OPENPROJECT_API_KEY env var)"
    )

    parser.add_argument(
        "--encryption-key",
        type=str,
        help="Encryption key (default: ENCRYPTION_KEY env var)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )

    return parser


def load_config_from_args(args) -> ServerConfig:
    """Load configuration from arguments and environment."""
    # Priority: command line args > environment variables > defaults
    endpoint = args.endpoint or os.getenv("OPENPROJECT_BASE_URL", "http://localhost:8080")
    api_key = args.api_key or os.getenv("OPENPROJECT_API_KEY", "")
    encryption_key = args.encryption_key or os.getenv("ENCRYPTION_KEY", "default-encryption-key")

    return ServerConfig(
        openproject_base_url=endpoint,
        openproject_api_key=api_key,
        encryption_key=encryption_key
    )


async def cmd_server(args) -> None:
    """Run MCP server."""
    config = load_config_from_args(args)

    # Set environment variables for compatibility
    if config.openproject_base_url:
        os.environ["OPENPROJECT_BASE_URL"] = config.openproject_base_url
    if config.openproject_api_key:
        os.environ["OPENPROJECT_API_KEY"] = config.openproject_api_key
    if config.encryption_key:
        os.environ["ENCRYPTION_KEY"] = config.encryption_key

    # Determine transport mode
    if args.stdio:
        transport = StdioTransport(config)
        mode = "stdio"
    elif args.http:
        transport = HttpTransport(config, host=args.host, port=args.port)
        mode = "http"
    elif args.sse:
        transport = SseTransport(config, host=args.host, port=args.port)
        mode = "sse"
    else:
        # Default to stdio mode
        transport = StdioTransport(config)
        mode = "stdio"

    logger.info(f"Starting MCP OpenProject Server in {mode} mode...")

    try:
        # Start transport
        await transport.start()
        await transport.serve()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await transport.stop()


def cmd_config(args) -> None:
    """Show current configuration."""
    config = load_config_from_args(args)

    print("MCP OpenProject Configuration:")
    print(f"  Endpoint: {config.openproject_base_url}")
    print(f"  API Key: {'***' + config.openproject_api_key[-4:] if config.openproject_api_key else 'Not set'}")
    print(f"  Encryption Key: {'***' + config.encryption_key[-4:] if config.encryption_key != 'default-encryption-key' else 'Default'}")

    # Check environment variables
    print("\nEnvironment Variables:")
    print(f"  OPENPROJECT_BASE_URL: {os.getenv('OPENPROJECT_BASE_URL', 'Not set')}")
    print(f"  OPENPROJECT_API_KEY: {'Set' if os.getenv('OPENPROJECT_API_KEY') else 'Not set'}")
    print(f"  ENCRYPTION_KEY: {'Set' if os.getenv('ENCRYPTION_KEY') else 'Not set'}")


async def cmd_status_async(args) -> bool:
    """Check server status."""
    config = load_config_from_args(args)

    if not config.openproject_api_key:
        print("❌ Error: API key not configured")
        return False

    try:
        from mcp_server.src.openproject_client import create_openproject_client

        async with await create_openproject_client(config) as client:
            # Try to get a simple API response
            status = await client.get("/api/v3/status")

            print("✅ MCP OpenProject Server Status:")
            print(f"  Endpoint: {config.openproject_base_url}")
            print(f"  Connection: OK")
            print(f"  API Response: {status.get('status', 'Unknown')}")
            return True

    except Exception as e:
        print(f"❌ Error connecting to OpenProject API:")
        print(f"  Endpoint: {config.openproject_base_url}")
        print(f"  Error: {e}")
        return False


def cmd_status(args) -> bool:
    """Check server status."""
    return asyncio.run(cmd_status_async(args))


async def cmd_test_async(args) -> bool:
    """Run tests against OpenProject API."""
    config = load_config_from_args(args)

    if not config.openproject_api_key:
        print("❌ Error: API key not configured")
        return False

    print("🧪 Running MCP OpenProject Tests...")

    try:
        from mcp_server.src.openproject_client import create_openproject_client

        async with await create_openproject_client(config) as client:
            # Test API connectivity
            print("  Testing API connectivity...")
            status = await client.get("/api/v3/status")
            print(f"  ✅ API Status: {status.get('status', 'Unknown')}")

            # Test project access
            print("  Testing project access...")
            projects = await client.get("/api/v3/projects", params={"pageSize": 1})
            print(f"  ✅ Projects accessible: {projects.get('count', 0)} total")

            # Test work packages
            print("  Testing work package access...")
            work_packages = await client.get("/api/v3/work_packages", params={"pageSize": 1})
            print(f"  ✅ Work packages accessible: {work_packages.get('count', 0)} total")

            print("\n✅ All tests passed!")
            return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def cmd_test(args) -> bool:
    """Run tests."""
    return asyncio.run(cmd_test_async(args))


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Route to appropriate command
    if args.command == "server":
        asyncio.run(cmd_server(args))
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "test":
        cmd_test(args)
    else:
        # Default behavior - show help
        parser.print_help()


# Entry points for pyproject.toml
def server():
    """Server command entry point."""
    parser = argparse.ArgumentParser(prog="mcp-openproject-server")
    parser.add_argument("--stdio", action="store_true", help="Run in stdio mode")
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode")
    parser.add_argument("--sse", action="store_true", help="Run in SSE mode")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")

    args = parser.parse_args()

    # Create minimal args object
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None
            self.stdio = args.stdio
            self.http = args.http
            self.sse = args.sse
            self.port = args.port
            self.host = args.host
            self.log_level = "INFO"

    asyncio.run(cmd_server(SimpleArgs()))


def config():
    """Config command entry point."""
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None

    cmd_config(SimpleArgs())


def status():
    """Status command entry point."""
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None

    cmd_status(SimpleArgs())


def test():
    """Test command entry point."""
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None

    cmd_test(SimpleArgs())


if __name__ == "__main__":
    main()