# MCP Client Component - Claude Development Guidelines

## Component Purpose

This directory contains the MCP client implementation that integrates with AI systems. It provides a FastAPI backend with langchain-mcp-adapters integration, enabling AI websites to consume MCP tools from the MCP server. The component supports both development (JSON configuration) and production (database) modes.

## 🐍 Python Execution Environment
**虚拟环境路径**: `venv/` (项目根目录下)
**执行模式**: 每次Python命令前需要激活虚拟环境
**标准模式**: `source venv/bin/activate && python <script>`
**检测机制**: 如果命令失败，检查是否未激活虚拟环境

## Architecture & Responsibilities

### Core Components
- **`app.py`**: Main FastAPI application with MCP client integration
- **`templates/`**: Jinja2 templates for report rendering
- **`components/`**: Reusable UI and API components

### Key Features
- **Multi-Transport Support**: stdio, HTTP, SSE communication with MCP server
- **Dynamic Configuration**: Runtime MCP tool management
- **Template Rendering**: Jinja2-based report generation
- **AI Integration**: OpenAI LLM enhancement for report refinement
- **Database Backend**: PostgreSQL for production configuration storage

## Task Management Approach

### Expert Coordination Requirements
- **Backend Expert**: FastAPI architecture, async patterns, database design
- **AI Integration Specialist**: LangChain integration, prompt engineering, LLM optimization
- **Frontend Expert**: React/Next.js integration, UI component development
- **DevOps Engineer**: Deployment, monitoring, production configuration

### Task Planning Workflow
1. **Architecture Review**: Validate FastAPI and database design
2. **Integration Testing**: MCP client-server communication validation
3. **Performance Optimization**: Async patterns and caching strategies
4. **Production Readiness**: Security, monitoring, deployment preparation

## Development Standards

### Code Quality Requirements
- **Async-First**: All I/O operations must be async/await
- **Type Safety**: Full type hints with Pydantic models
- **Error Handling**: Structured HTTP exceptions with proper status codes
- **Database Design**: Proper migrations and relationship management

### Integration Points
- **MCP Server**: Consumes tools via langchain-mcp-adapters
- **AI Website Frontend**: Provides REST API for React/Next.js
- **Database**: PostgreSQL for configuration persistence
- **OpenAI API**: Optional LLM enhancement for reports

## Current Development Priorities

### 🔴 Critical Issues (Week 1)
1. **Dependency Resolution**: Align langchain-mcp-adapters with mcp-server
2. **Security Enhancement**: Implement proper authentication and authorization
3. **Error Handling**: Improve HTTP error responses and logging
4. **Database Schema**: Finalize production database design

### 🟡 Important Features (Week 2)
1. **Template System**: Enhanced Jinja2 templates with validation
2. **Caching Strategy**: Implement Redis caching for MCP responses
3. **API Documentation**: OpenAPI/Swagger documentation completion
4. **Testing Suite**: Comprehensive integration tests

### 🟢 Enhancement Opportunities (Week 3)
1. **Advanced AI Features**: Multi-model support, custom prompts
2. **Real-time Updates**: WebSocket integration for live updates
3. **Analytics**: Usage tracking and performance metrics
4. **Multi-tenancy**: Enhanced user isolation and permissions

## API Design

### Core Endpoints
- **`POST /mcp/{desc}`**: Execute MCP tools with parameters
- **`POST /mcp-config`**: Add/update MCP configurations
- **`GET /mcp-config`**: List user MCP configurations
- **`DELETE /mcp-config/{desc}`**: Remove MCP configurations
- **`POST /templates/{template_name}`**: Update Jinja2 templates
- **`GET /templates/{template_name}`**: Retrieve template content

### Request/Response Patterns
```python
# MCP Tool Execution Request
{
    "desc": "openproject_weekly_report",
    "params": {"project_id": 1, "week": "2025-W41"},
    "user_id": "user123"
}

# Response Structure
{
    "result": "Rendered report content",
    "raw_data": {...},
    "tool": "openproject_weekly_report",
    "params": {...}
}
```

## Configuration Management

### Development Mode
```json
[
    {
        "desc": "openproject_weekly_report",
        "interaction_mode": "streamful_http",
        "url": "http://localhost:8000/mcp",
        "endpoint": "http://localhost:8090",
        "api_key": "$OPENPROJECT_API_KEY",
        "params": {"project_id": 1},
        "auth": {"type": "api_key", "value": "$OPENPROJECT_API_KEY"}
    }
]
```

### Production Database Schema
```sql
CREATE TABLE mcp_services (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    desc VARCHAR(255) NOT NULL,
    interaction_mode VARCHAR(50),
    url VARCHAR(255),
    endpoint VARCHAR(255),
    api_key VARCHAR(255),
    params JSONB,
    auth JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Template System

### Jinja2 Template Structure
```jinja2
# weekly_report.j2
# Project Weekly Report
**Project**: {{ project.name }}
**Week**: {{ week }}
**Summary**: {{ summary }}

## Tasks
{% for task in work_packages %}
- **{{ task.subject }}** (Status: {{ task.status }})
  - Assignee: {{ task.assignee or 'Unassigned' }}
  - Due: {{ task.due_date or 'No due date' }}
  - Priority: {{ task.priority or 'Medium' }}
{% endfor %}

## Statistics
- Total Tasks: {{ work_packages|length }}
- Completed: {{ work_packages|selectattr('status', 'equalto', 'Completed')|list|length }}
- In Progress: {{ work_packages|selectattr('status', 'equalto', 'In Progress')|list|length }}
```

## Dependencies & Compatibility

### Core Dependencies
- **fastapi**: Web framework and API development
- **langchain-mcp-adapters**: MCP client integration (>=0.0.9,<0.0.10)
- **sqlalchemy**: Async database ORM
- **asyncpg**: PostgreSQL async driver
- **jinja2**: Template rendering engine
- **pydantic**: Data validation and serialization

### AI Enhancement Dependencies
- **langchain-openai**: OpenAI LLM integration
- **langchain-core**: Core LangChain components
- **watchfiles**: Configuration hot reload for development

### Version Alignment
- **Critical**: langchain-mcp-adapters must match mcp-server version
- **Python**: 3.9+ for async/await support
- **PostgreSQL**: 12+ for JSONB support

## Security Guidelines

### Authentication & Authorization
- **API Key Validation**: Secure token-based authentication
- **User Isolation**: Per-user configuration and data separation
- **Template Security**: Restricted template execution and validation
- **Input Sanitization**: Pydantic validation for all inputs

### Data Protection
- **Credential Encryption**: Secure storage of API keys and tokens
- **Database Security**: Proper connection security and query parameterization
- **HTTPS Enforcement**: TLS for all external communications
- **Rate Limiting**: Abuse prevention and resource protection

## Performance Optimization

### Async Patterns
- **Database Operations**: All database queries use async sessions
- **HTTP Client**: Async httpx for external API calls
- **Template Rendering**: Async template processing where applicable
- **Background Tasks**: Non-blocking operations using FastAPI BackgroundTasks

### Caching Strategy
- **MCP Responses**: Cache tool execution results
- **Template Compilation**: Pre-compile and cache Jinja2 templates
- **Database Queries**: Query result caching for frequently accessed data
- **Configuration**: In-memory configuration with database fallback

## Testing Strategy

### Test Categories
- **Unit Tests**: Individual endpoint and function testing
- **Integration Tests**: MCP client-server communication
- **Database Tests**: ORM operations and migration validation
- **Template Tests**: Jinja2 template rendering validation
- **Security Tests**: Authentication and authorization testing

### Test Execution
```bash
# Install test dependencies (remember to activate virtual environment)
source venv/bin/activate && pip install pytest pytest-asyncio httpx

# Run tests
source venv/bin/activate && pytest -v

# Run with coverage
source venv/bin/activate && pytest --cov=app --cov-report=html
```

## Monitoring & Observability

### Logging Requirements
- **Structured Logging**: JSON format with correlation IDs
- **Request Tracing**: HTTP request/response logging
- **Error Tracking**: Detailed error logging with stack traces
- **Performance Metrics**: Response time and throughput monitoring

### Health Monitoring
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "mcp_servers": await check_mcp_server_health(),
        "external_apis": await check_external_api_health()
    }
```

## Integration Notes

### with MCP Server
- **Transport Compatibility**: Supports stdio, HTTP, SSE modes
- **Configuration Sync**: Dynamic tool discovery and registration
- **Error Propagation**: Proper error handling and retry logic
- **Performance**: Connection pooling and optimization

### with AI Website Frontend
- **REST API**: Clean API contract for React/Next.js consumption
- **Real-time Updates**: WebSocket support for live data updates
- **Authentication**: JWT token validation and user session management
- **Error Handling**: Consistent error responses for frontend consumption

### with OpenAI API
- **Prompt Engineering**: Optimized prompts for report refinement
- **Cost Management**: Token usage tracking and limits
- **Fallback Handling**: Graceful degradation when LLM is unavailable
- **Response Caching**: Cache refined reports to reduce API costs

## Deployment Considerations

### Local Development
```bash
# Install dependencies (remember to activate virtual environment)
source venv/bin/activate && pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/mcp_db"
export OPENAI_API_KEY="your-openai-api-key"

# Run development server
source venv/bin/activate && uvicorn app:app --reload --host 0.0.0.0 --port 3000
```

### Production Deployment
- **Containerization**: Docker image with multi-stage builds
- **Database Migrations**: Alembic for schema management
- **Environment Configuration**: Environment-based config management
- **Load Balancing**: Multiple instances behind load balancer

## Expert Review Checklist

### Backend Expert Review Items
- [ ] FastAPI application architecture and patterns
- [ ] Async database operations and connection pooling
- [ ] API design and REST principles adherence
- [ ] Error handling and HTTP status code usage
- [ ] Security implementation and best practices

### AI Integration Specialist Review Items
- [ ] LangChain integration and prompt engineering
- [ ] MCP client configuration and tool management
- [ ] LLM integration and response handling
- [ ] Template system and rendering optimization
- [ ] Performance optimization for AI workloads

### Frontend Expert Review Items
- [ ] API contract design for frontend consumption
- [ ] Real-time communication patterns
- [ ] Authentication and user session management
- [ ] Error handling for frontend integration
- [ ] Performance optimization for UI responsiveness

## Common Tasks & Patterns

### Adding New MCP Tool Integrations
1. Update database schema for new configuration fields
2. Add Pydantic models for request/response validation
3. Implement tool execution logic with error handling
4. Create corresponding Jinja2 templates
5. Add comprehensive tests and documentation

### Database Schema Updates
1. Create Alembic migration for schema changes
2. Update Pydantic models to match new schema
3. Implement backward compatibility for existing data
4. Add database tests for new functionality
5. Update API documentation

### Template Management
1. Design Jinja2 template with proper escaping
2. Add template validation and security checks
3. Implement template versioning and rollback
4. Create template preview and testing functionality
5. Document template variables and usage patterns
