# Configuration Management

Configuration files and setup for MCP OpenProject integration.

## Overview

The system supports two configuration modes:

1. **Development**: JSON-based configuration with file watching
2. **Production**: Database-based configuration with REST API management

## Development Configuration

### mcp_config.json

Located in the mcp-client directory, this file defines MCP service configurations for development:

```json
[
  {
    "desc": "openproject_weekly_report",
    "interaction_mode": "streamful_http",
    "url": "http://localhost:8000/mcp",
    "endpoint": "https://your-openproject-instance.com",
    "api_key": "your-api-key",
    "params": {
      "project_id": 1
    },
    "auth": {
      "type": "api_key",
      "value": "your-api-key"
    }
  }
]
```

### Configuration Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `desc` | string | Yes | Human-readable description of the service |
| `interaction_mode` | string | Yes | Communication mode: `stdio`, `http`, `sse`, `streamful_http` |
| `url` | string | No | URL for HTTP/SSE modes |
| `endpoint` | string | No | Target service endpoint |
| `api_key` | string | Yes | API key for authentication |
| `params` | object | No | Default parameters for the service |
| `auth` | object | No | Authentication configuration |

### Interaction Modes

- **stdio**: Local process communication via stdin/stdout
- **http**: HTTP REST API endpoints
- **sse**: Server-Sent Events for real-time updates
- **streamful_http**: Alias for http mode

## Production Configuration

### Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/mcp_db

# OpenAI API for report refinement (optional)
OPENAI_API_KEY=your-openai-api-key

# Development mode flag
DEVELOPMENT_MODE=false

# Security settings
SECRET_KEY=your-secret-key-for-jwt-tokens
CORS_ORIGINS=["http://localhost:3000", "https://your-domain.com"]
```

### Database Configuration

MCP services are stored in the `mcp_services` table with the following structure:

```sql
CREATE TABLE mcp_services (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    desc VARCHAR(255) NOT NULL,
    interaction_mode VARCHAR(50) NOT NULL,
    url VARCHAR(255),
    endpoint VARCHAR(255),
    api_key VARCHAR(255) NOT NULL,
    params JSONB,
    auth JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## IDE Configuration

### Cursor IDE

Create `.cursorrules` file in your project root:

```json
{
  "mcp": {
    "servers": {
      "openproject": {
        "command": "python",
        "args": [
          "mcp-server/mcp_openproject.py",
          "--endpoint", "https://your-openproject-instance.com",
          "--api-key", "your-api-key",
          "--mode", "stdio"
        ],
        "env": {
          "PYTHONPATH": "./mcp-server"
        }
      }
    }
  }
}
```

### VS Code with MCP Extension

Create `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "openproject": {
      "command": "python",
      "args": [
        "./mcp-server/mcp_openproject.py",
        "--endpoint", "https://your-openproject-instance.com",
        "--api-key", "your-api-key",
        "--mode", "stdio"
      ]
    }
  }
}
```

## Security Considerations

### API Key Management

1. **Never commit API keys to version control**
2. **Use environment variables for production**
3. **Implement key rotation policies**
4. **Use different keys for different environments**

### Authentication Types

Currently supported:
- `api_key`: Simple API key authentication
- `oauth`: OAuth2 authentication (placeholder, implementation needed)
- `jwt`: JWT token authentication (placeholder, implementation needed)

### CORS Configuration

For production deployment, configure CORS properly:

```python
# In app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  mcp-server:
    build:
      context: ./mcp-server
      dockerfile: Dockerfile
    environment:
      - OPENPROJECT_ENDPOINT=https://your-openproject-instance.com
      - OPENPROJECT_API_KEY=${OPENPROJECT_API_KEY}
    ports:
      - "8000:8000"

  mcp-client:
    build:
      context: ./mcp-client
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mcp_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "3000:3000"
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcp_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

## Monitoring and Logging

### Health Checks

The MCP client provides a health check endpoint:

```bash
curl http://localhost:3000/health
```

### Log Configuration

For production, configure logging levels:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set specific loggers
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

## Configuration Validation

### JSON Schema Validation

Use this schema to validate your `mcp_config.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["desc", "interaction_mode", "api_key"],
    "properties": {
      "desc": {
        "type": "string",
        "minLength": 1,
        "maxLength": 255
      },
      "interaction_mode": {
        "type": "string",
        "enum": ["stdio", "http", "sse", "streamful_http"]
      },
      "url": {
        "type": "string",
        "format": "uri"
      },
      "endpoint": {
        "type": "string",
        "format": "uri"
      },
      "api_key": {
        "type": "string",
        "minLength": 1
      },
      "params": {
        "type": "object",
        "default": {}
      },
      "auth": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": ["api_key", "oauth", "jwt"]
          },
          "value": {
            "type": "string"
          }
        },
        "required": ["type"]
      }
    }
  }
}
```