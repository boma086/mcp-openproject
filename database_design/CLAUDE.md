# Database Design

Database schema and migration scripts for the MCP Client service.

## Schema Overview

### mcp_services Table

Stores MCP service configurations for user isolation.

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

-- Indexes for performance
CREATE INDEX idx_mcp_services_user_id ON mcp_services(user_id);
CREATE INDEX idx_mcp_services_desc ON mcp_services(desc);
CREATE UNIQUE INDEX idx_mcp_services_user_desc ON mcp_services(user_id, desc);
```

### mcp_executions Table (Optional)

Logs MCP tool executions for debugging and analytics.

```sql
CREATE TABLE mcp_executions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    tool_desc VARCHAR(255) NOT NULL,
    params JSONB,
    status VARCHAR(50) NOT NULL,
    result JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_mcp_executions_user_id ON mcp_executions(user_id);
CREATE INDEX idx_mcp_executions_tool_desc ON mcp_executions(tool_desc);
CREATE INDEX idx_mcp_executions_created_at ON mcp_executions(created_at);
```

### mcp_templates Table (Optional)

Stores custom Jinja2 templates for report generation.

```sql
CREATE TABLE mcp_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    created_by VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE UNIQUE INDEX idx_mcp_templates_name ON mcp_templates(name);
```

## Migration Script

```sql
-- Create database
CREATE DATABASE mcp_db
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- Connect to the database and run the following:

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE IF NOT EXISTS mcp_services (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    desc VARCHAR(255) NOT NULL,
    interaction_mode VARCHAR(50) NOT NULL,
    url VARCHAR(255),
    endpoint VARCHAR(255),
    api_key VARCHAR(255) NOT NULL,
    params JSONB DEFAULT '{}',
    auth JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_mcp_services_user_id ON mcp_services(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_services_desc ON mcp_services(desc);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_services_user_desc ON mcp_services(user_id, desc);

-- Create optional tables for enhanced functionality
CREATE TABLE IF NOT EXISTS mcp_executions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    tool_desc VARCHAR(255) NOT NULL,
    params JSONB DEFAULT '{}',
    status VARCHAR(50) NOT NULL,
    result JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mcp_executions_user_id ON mcp_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_executions_tool_desc ON mcp_executions(tool_desc);
CREATE INDEX IF NOT EXISTS idx_mcp_executions_created_at ON mcp_executions(created_at);

CREATE TABLE IF NOT EXISTS mcp_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    created_by VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_templates_name ON mcp_templates(name);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_mcp_services_updated_at
    BEFORE UPDATE ON mcp_services
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mcp_templates_updated_at
    BEFORE UPDATE ON mcp_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;
```

## Sample Data

```sql
-- Insert sample MCP service configuration
INSERT INTO mcp_services (user_id, desc, interaction_mode, url, endpoint, api_key, params, auth) VALUES
('global', 'openproject_weekly_report', 'streamful_http', 'http://localhost:8000/mcp', 'https://demo.openproject.com', 'demo-api-key', '{"project_id": 1}', '{"type": "api_key", "value": "demo-api-key"}'),
('user1', 'project_management', 'stdio', NULL, 'https://company.openproject.com', 'user1-api-key', '{"project_id": 5}', '{"type": "api_key", "value": "user1-api-key"}'),
('user2', 'enterprise_reports', 'sse', 'http://localhost:8001/mcp', 'https://enterprise.openproject.com', 'enterprise-api-key', '{"project_id": 10, "include_archived": true}', '{"type": "oauth", "provider": "openproject"}');

-- Insert sample templates
INSERT INTO mcp_templates (name, content, description) VALUES
('weekly_report.j2', '# {{ project.name }} Weekly Report\n\n**Week**: {{ week }}\n\n## Tasks\n{% for task in work_packages %}- {{ task.subject }} ({{ task.status }})\n{% endfor %}', 'Standard weekly report template'),
('executive_summary.j2', '# Executive Summary\n\n**Project**: {{ project.name }}\n**Progress**: {{ work_packages|length }} tasks total\n\n## Key Metrics\n- Completed: {{ work_packages|selectattr('status', 'equalto', 'Completed')|list|length }}\n- In Progress: {{ work_packages|selectattr('status', 'equalto', 'In Progress')|list|length }}\n- Blocked: {{ work_packages|selectattr('status', 'equalto', 'Blocked')|list|length }}', 'Executive summary template');
```

## Environment Variables

Set these environment variables for the MCP Client service:

```bash
# Database connection
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/mcp_db

# OpenAI API for report refinement (optional)
OPENAI_API_KEY=your-openai-api-key

# Development mode (use JSON config instead of database)
DEVELOPMENT_MODE=false
```

## Connection Pool Configuration

For production deployment, consider configuring connection pooling:

```python
# In app.py, modify the engine creation:
from sqlalchemy.pool import NullPool

# For serverless environments
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# For production with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    echo=False
)
```