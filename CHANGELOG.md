# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2025-01-16

### ✨ Added
- **MCP Server Implementation**: Complete Model Context Protocol server for OpenProject integration
- **Multiple Transport Modes**:
  - Stdio mode for MCP clients (Claude Code, Windsurf)
  - HTTP mode using fastapi_mcp library
  - SSE mode (planned for future release)
- **OpenProject Integration**: Auto-generated API client with full OpenProject support
- **CLI Interface**: Comprehensive command-line tools
  - `mcp-openproject server --stdio/http/sse`
  - `mcp-openproject config/status/test`
- **Security Framework**: Encrypted configuration and API key management
- **Smithery Platform Support**: Cloud deployment configuration

### 🛠️ Technical Features
- **FastAPI Integration**: HTTP mode with fastapi_mcp v0.4.0
- **OpenProject API Client**: Generated from OpenProject OpenAPI specification
- **Dependency Injection**: Shared service layer architecture
- **Async/Await Support**: Full asynchronous processing
- **Environment Configuration**: Comprehensive environment variable management
- **Error Handling**: Robust error handling and logging with structlog

### 📦 MCP Tools Available
- Project Management (list, details, statistics)
- Work Packages (create, read, update, delete)
- Weekly Reports (automated generation)
- Time Tracking (log entries, hours tracking)
- Team Management (user information, assignments)

### 🚀 Installation & Deployment
- **PyPI Package**: `pip install mcp-openproject`
- **GitHub Installation**: `pipx install git+https://github.com/boma086/mcp-openproject.git`
- **Smithery Deployment**: Zero-install cloud deployment
- **Docker Support**: Container deployment ready

### ✅ Verification Status
- **PyPI Production**: Successfully published to [PyPI](https://pypi.org/project/mcp-openproject/)
- **CLI Testing**: All commands verified working
- **Package Managers**: Tested with pip, uv, pipx
- **MCP Integration**: Stdio and HTTP modes operational
- **Platform Testing**: macOS and Linux verified

### 📚 Documentation
- **Complete README**: User-friendly installation and configuration guide
- **Technical Documentation**: Architecture and implementation details
- **PyPI Publishing Guide**: Complete publishing workflow documentation
- **Transport Modes Documentation**: Detailed technical specifications

### 🔧 Dependencies
- **Core**: fastmcp>=0.3.0, httpx>=0.25.0, pydantic>=2.0.0
- **HTTP Mode**: fastapi>=0.104.0, uvicorn[standard]>=0.24.0, fastapi_mcp>=0.4.0
- **Security**: cryptography>=41.0.0, python-dotenv>=1.0.1
- **Development**: pytest>=7.4.0, black>=23.0.0, ruff>=0.1.0

### 🎯 Supported MCP Clients
- **Claude Code**: Full stdio integration
- **Windsurf**: Complete MCP server configuration
- **General MCP Clients**: Standard MCP protocol compliance

### 🌐 Deployment Options
- **Local Installation**: pip/pipx installation
- **Development Mode**: `pip install -e .` for development
- **Production**: System service deployment
- **Cloud**: Smithery platform integration

---

## Development Roadmap

### [Unreleased]
- [ ] SSE Mode implementation
- [ ] Enhanced monitoring and metrics
- [ ] Additional OpenProject API endpoints
- [ ] Performance optimizations
- [ ] Extended testing coverage

### [Planned for v0.1.0]
- [ ] SSE (Server-Sent Events) transport mode
- [ ] Real-time project updates
- [ ] Enhanced error reporting
- [ ] Configuration validation tools

### [Planned for v0.2.0]
- [ ] WebSocket support
- [ ] Advanced caching mechanisms
- [ ] Multi-tenant support
- [ ] Advanced security features

---

## Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/boma086/mcp-openproject/issues)
- **GitHub Discussions**: [Community discussions and questions](https://github.com/boma086/mcp-openproject/discussions)
- **Documentation**: [Complete project documentation](https://github.com/boma086/mcp-openproject/tree/main/docs)

---

**Note**: This project follows [Semantic Versioning](https://semver.org/). Major version changes indicate breaking changes, minor versions add new features in a backward-compatible manner, and patch versions contain bug fixes.