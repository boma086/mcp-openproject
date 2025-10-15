# MCP OpenProject Server

A Model Context Protocol (MCP) server for integrating OpenProject with AI assistants like Claude, Windsurf, and other MCP-compatible clients.

## Features

- **🚀 GitHub Installation**: Install directly from GitHub with pipx
- **📡 Multiple Transport Modes**: Stdio, HTTP, and SSE support
- **🔗 OpenProject API Integration**: Complete access to projects, work packages, and tasks
- **🛡️ Security**: Encrypted configuration and API key management
- **🖥️ CLI Interface**: Comprehensive command-line tools
- **🎯 MCP Compatible**: Works with Claude Code, Windsurf, and other MCP clients

## Quick Start

### 🚀 Recommended: Install from GitHub (Global)

```bash
# Install directly from GitHub (recommended for MCP clients)
pipx install git+https://github.com/boma086/mcp-openproject.git

# Set environment variables
export OPENPROJECT_BASE_URL="http://localhost:8090/"
export OPENPROJECT_API_KEY="your-api-key-here"
export ENCRYPTION_KEY="your-encryption-key-here"

# Test installation
mcp-openproject --help
```

### 📦 Development Installation

```bash
# Clone and install for development
git clone https://github.com/boma086/mcp-openproject.git
cd mcp-openproject
pip install -e .

# Set environment variables
export OPENPROJECT_BASE_URL="http://localhost:8090/"
export OPENPROJECT_API_KEY="your-api-key-here"
export ENCRYPTION_KEY="your-encryption-key-here"

# Test installation
mcp-openproject test
```

## Configuration

### Required Environment Variables

- `OPENPROJECT_BASE_URL`: Your OpenProject instance URL (e.g., `http://localhost:8090/`)
- `OPENPROJECT_API_KEY`: Your OpenProject API key
- `ENCRYPTION_KEY`: Encryption key for sensitive data (generate one: `openssl rand -hex 32`)

### Example Configuration

```bash
# Add to your ~/.bashrc or ~/.zshrc
export OPENPROJECT_BASE_URL="http://localhost:8090/"
export OPENPROJECT_API_KEY="your-api-key-here"
export ENCRYPTION_KEY="your-32-byte-encryption-key-here"
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
mcp-openproject server --sse --port 8001   # SSE mode

# Check server status
mcp-openproject status
```

## Available MCP Tools

- **Project Management**: List projects, get project details, project statistics
- **Work Packages**: Create, read, update work packages and tasks
- **Time Tracking**: Log time entries, track project hours
- **Reporting**: Generate project reports and summaries
- **Team Management**: Access user information and team assignments

## MCP Client Integration

### Claude Code Configuration

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "mcp-openproject",
      "args": ["server", "--stdio"],
      "env": {
        "OPENPROJECT_BASE_URL": "http://localhost:8090/",
        "OPENPROJECT_API_KEY": "your-api-key-here",
        "ENCRYPTION_KEY": "your-encryption-key-here"
      }
    }
  }
}
```

### Windsurf Configuration

**Step 1: Install MCP Server**
```bash
pipx install git+https://github.com/boma086/mcp-openproject.git
```

**Step 2: Add to Windsurf MCP Configuration**
```json
{
  "mcpServers": {
    "openproject": {
      "command": "mcp-openproject",
      "args": ["server", "--stdio"],
      "env": {
        "OPENPROJECT_BASE_URL": "http://localhost:8090/",
        "OPENPROJECT_API_KEY": "your-api-key-here",
        "ENCRYPTION_KEY": "your-encryption-key-here"
      }
    }
  }
}
```

### General MCP Client Configuration

For any MCP-compatible client:

1. **Install the server**: `pipx install git+https://github.com/boma086/mcp-openproject.git`
2. **Configure environment variables** (as shown above)
3. **Add MCP server configuration**:
   ```json
   {
     "mcpServers": {
       "openproject": {
         "command": "mcp-openproject",
         "args": ["server", "--stdio"]
       }
     }
   }
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
- `docs/`: Comprehensive documentation and guides
- `pyproject.toml`: Project configuration with comprehensive dependency management

## License

MIT License