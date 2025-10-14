# MCP Server

MCP (Model Context Protocol) server for OpenProject integration with support for multiple transport modes.

## Features

- **Multi-transport support**: stdio, HTTP, SSE
- **OpenProject API integration**: Via generated FastAPI client
- **FastMCP integration**: For MCP protocol implementation
- **Pydantic models**: For data validation and serialization

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For development with hot reload
pip install -r requirements-dev.txt
```

## Running the Server

### HTTP Mode (for AI websites)
```bash
python mcp_openproject.py \
  --endpoint "https://your-openproject-instance.com" \
  --api-key "your-api-key" \
  --mode http \
  --port 8000
```

### stdio Mode (for IDE integration)
```bash
python mcp_openproject.py \
  --endpoint "https://your-openproject-instance.com" \
  --api-key "your-api-key" \
  --mode stdio
```

### SSE Mode (for real-time updates)
```bash
python mcp_openproject.py \
  --endpoint "https://your-openproject-instance.com" \
  --api-key "your-api-key" \
  --mode sse \
  --port 8000
```

## MCP Tools

### fetch_weekly_report
Fetch weekly report data for a specific project.

```json
{
  "tool": "fetch_weekly_report",
  "params": {
    "project_id": 1
  }
}
```

### get_project_data
Get raw project data as a resource.

```json
{
  "resource": "openproject://projects/{project_id}"
}
```

## stdio Protocol

### Input Format
JSON messages sent to stdin:

```json
{
  "tool": "fetch_weekly_report",
  "params": {
    "project_id": 1
  }
}
```

### Output Format
JSON responses sent to stdout:

```json
{
  "data": {
    "project": {...},
    "work_packages": [...]
  }
}
```

## API Endpoints

- `POST /mcp`: MCP tool execution
- `GET /mcp/sse`: SSE event stream
- `GET /openapi.json`: OpenAPI specification