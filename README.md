# MCP OpenProject Server

A Model Context Protocol (MCP) server for integrating OpenProject with AI assistants like Claude.

## Features

- **Stdio Transport**: Works with Claude Code via stdio protocol
- **OpenProject API Integration**: Full access to projects, work packages, and tasks
- **CLI Interface**: Command-line tools for easy interaction
- **uvx Support**: Zero-dependency execution with uvx

## Quick Start

### Using pip (traditional)

```bash
# Install dependencies
pip install -e .

# Set environment variables
export OPENPROJECT_BASE_URL="http://localhost:8090"
export OPENPROJECT_API_KEY="your-api-key"

# Run MCP server
mcp-openproject server
```

### Using uvx (zero-dependency)

```bash
# Run directly with uvx (no pip install needed)
uvx run --from . mcp-openproject server

# Test the server
uvx run --from . mcp-openproject test
```

## Configuration

Set these environment variables:

- `OPENPROJECT_BASE_URL`: Your OpenProject instance URL
- `OPENPROJECT_API_KEY`: Your OpenProject API key

## CLI Commands

```bash
# Show help
mcp-openproject --help

# Test connection to OpenProject
mcp-openproject test

# Show current configuration
mcp-openproject config

# Start MCP server (stdio mode)
mcp-openproject server
```

## Available Tools

- `list-projects`: List OpenProject projects
- `get-project`: Get project details by ID
- `list-work-packages`: List work packages in a project
- `get-work-package`: Get work package details by ID

## Integration with Claude Code

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "mcp-openproject",
      "args": ["server"]
    }
  }
}
```

## Development

This project uses a minimal architecture with just 4 core files:

- `mcp_server/main.py`: MCP server implementation
- `mcp_server/cli.py`: Command-line interface
- `mcp_server/__init__.py`: Python module structure
- `pyproject.toml`: Project configuration and dependencies

## License

MIT License