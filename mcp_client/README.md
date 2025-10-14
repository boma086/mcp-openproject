# MCP Client

Sample implementation of MCP client for AI website integration using FastAPI and langchain-mcp-adapters.

## Features

- **Multi-transport support**: stdio, HTTP, SSE
- **langchain-mcp-adapters integration**: For seamless LangChain compatibility
- **FastAPI backend**: RESTful API endpoints
- **Jinja2 templating**: For report rendering
- **Database support**: PostgreSQL for production, JSON for development

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Configuration

### Development (JSON)
Create `mcp_config.json`:
```json
[
  {
    "desc": "openproject_weekly_report",
    "interaction_mode": "streamful_http",
    "url": "http://localhost:8000/mcp",
    "endpoint": "https://your-openproject.com",
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

### Production (Database)
The application will automatically create the required tables on first run.

## Running

```bash
# Development with JSON config
uvicorn app:app --reload --host 0.0.0.0 --port 3000

# Production with database
uvicorn app:app --host 0.0.0.0 --port 3000
```

## API Endpoints

- `POST /mcp/{desc}`: Execute MCP tool
- `POST /mcp-config`: Add/modify MCP configuration
- `GET /mcp-config`: List MCP configurations
- `DELETE /mcp-config/{desc}`: Remove MCP configuration
- `POST /templates/{name}`: Update Jinja2 template
- `GET /health`: Health check endpoint

## Frontend Integration

The client provides a React component for CopilotKit integration:

```jsx
import MCPToolCaller from './components/MCPToolCaller';

function App() {
  return (
    <MCPToolCaller userId="user123" />
  );
}
```