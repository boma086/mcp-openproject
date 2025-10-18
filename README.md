# MCP OpenProject Server

A Model Context Protocol (MCP) server for integrating OpenProject with AI assistants like Windsurf, and other MCP-compatible clients.

**Version**: 0.0.2 | **Status**: Production Ready | **PyPI**: [mcp-openproject](https://pypi.org/project/mcp-openproject/)

## 🚀 Quick Start - 5 Minutes to Running

### Option 1: Install from PyPI or github (Recommended for Users)

```bash
#pipx (isolated environment)
pipx install mcp-openproject
#or Install from PyPI
pip install mcp-openproject
# Install globally from GitHub
pipx install git+https://github.com/boma086/mcp-openproject.git


# Test installation
mcp-openproject --help
```

### Option 2: Development Installation

```bash
# Clone repository
git clone https://github.com/boma086/mcp-openproject.git
cd mcp-openproject

# Install in development mode
pip install -e .
```

## ⚙️ MCP Client Configuration

### Claude Code / Windsurf Configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "mcp-openproject",
      "args": ["server", "--stdio"],
      "env": {
        "OPENPROJECT_BASE_URL": "http://localhost:8090/",
        "OPENPROJECT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```


## Features

- **🚀 PyPI Installation**: Install from PyPI with `pip install mcp-openproject`
- **📡 Multiple Transport Modes**: Stdio (HTTP SSE planned)
- **🔗 OpenProject API Integration**: Complete access to projects, work packages, and tasks
- **🛡️ Security**: Encrypted configuration and API key management
- **🖥️ CLI Interface**: Comprehensive command-line tools
- **🎯 MCP Compatible**: Works with Windsurf, and other MCP clients
- **✅ Production Tested**: Verified installation and CLI functionality

## Configuration

### Required Environment Variables

- `OPENPROJECT_BASE_URL`: Your OpenProject instance URL (e.g., `http://localhost:8090/`)
- `OPENPROJECT_API_KEY`: Your OpenProject API key

### Example Configuration

```bash
# Add to your ~/.bashrc or ~/.zshrc
export OPENPROJECT_BASE_URL="http://localhost:8090/"
export OPENPROJECT_API_KEY="your-api-key-here"
```

## CLI Commands

```bash
# Show help
mcp-openproject --help

# Test connection to OpenProject
mcp-openproject test

# Show current configuration
mcp-openproject config

# Start MCP server in different modes
mcp-openproject server --stdio          # Stdio mode (for MCP clients)
mcp-openproject server --http --port 8000  # HTTP mode

# Check server status
mcp-openproject status
```

## Available MCP Tools

- **Project Management**: List projects, get project details, project statistics
- **Work Packages**: Create, read, update work packages and tasks
- **Weekly Reports**: Generate weekly reports for projects
- **Time Tracking**: Log time entries, track project hours
- **Team Management**: Access user information and team assignments

## Deployment Options

### Local Development

```bash
# Clone and install
git clone https://github.com/boma086/mcp-openproject.git
cd mcp-openproject
pip install -e .

# Run in development mode
uv run mcp-openproject server --stdio
uv run mcp-openproject server --http --port 8000
```

### Production Installation

```bash
# Install from PyPI (recommended for production)
pip install mcp-openproject
# or with pipx for isolated environment
pipx install mcp-openproject

# Run as system service
sudo systemctl enable mcp-openproject
sudo systemctl start mcp-openproject
```

## Architecture

This project uses a comprehensive architecture with:

- **MCP Server**: FastMCP-based implementation with multiple transport modes
- **OpenProject Integration**: Generated API client with full OpenProject support
- **Security Framework**: Encrypted configuration and API key management
- **CLI Interface**: Comprehensive command-line tools for all operations
- **Documentation**: Complete project documentation and guides

### Key Components

- `mcp_server/`: Core MCP server implementation
- `pyproject.toml`: Project configuration with comprehensive dependency management
#- `smithery.yaml`: Smithery platform deployment configuration

## Transport Modes

### ✅ Stdio Mode (Recommended for MCP Clients)
- **Use Case**: Direct integration with Claude Code, Windsurf, and other MCP clients
- **Command**: `mcp-openproject server --stdio`
- **Benefits**: Standard MCP protocol, low latency, secure

###  🚧  HTTP Mode (Planned)
- **Use Case**: Web applications, HTTP API integration
- **Command**: `mcp-openproject server --http --port 8000`
- **Benefits**: RESTful API, web-friendly, CORS support

### 🚧 SSE Mode (Planned)
- **Status**: Planned for future release
- **Use Case**: Real-time updates, streaming responses
- **Command**: `mcp-openproject server --sse --port 8001` (future)

### Getting Help
- **GitHub Issues**: [Report bugs](https://github.com/boma086/mcp-openproject/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/boma086/mcp-openproject/discussions)
- **Documentation**: [Full documentation](https://github.com/boma086/mcp-openproject/tree/main/docs)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Verification

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
