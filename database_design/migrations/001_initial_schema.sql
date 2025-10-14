-- Initial database schema for MCP Client service
-- Run this with: psql -d mcp_db -f 001_initial_schema.sql

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create main mcp_services table
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

-- Create indexes for mcp_services
CREATE INDEX IF NOT EXISTS idx_mcp_services_user_id ON mcp_services(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_services_desc ON mcp_services(desc);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_services_user_desc ON mcp_services(user_id, desc);

-- Create trigger for updated_at
CREATE TRIGGER update_mcp_services_updated_at
    BEFORE UPDATE ON mcp_services
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create optional mcp_executions table for logging
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

-- Create indexes for mcp_executions
CREATE INDEX IF NOT EXISTS idx_mcp_executions_user_id ON mcp_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_executions_tool_desc ON mcp_executions(tool_desc);
CREATE INDEX IF NOT EXISTS idx_mcp_executions_created_at ON mcp_executions(created_at);

-- Create optional mcp_templates table for custom templates
CREATE TABLE IF NOT EXISTS mcp_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    created_by VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for mcp_templates
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_templates_name ON mcp_templates(name);

-- Create trigger for updated_at
CREATE TRIGGER update_mcp_templates_updated_at
    BEFORE UPDATE ON mcp_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create database user and grant permissions (uncomment as needed)
/*
CREATE USER mcp_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE mcp_db TO mcp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mcp_user;
*/

-- Insert sample data (optional)
-- Uncomment the following lines to insert sample data

-- Sample MCP service configurations
/*
INSERT INTO mcp_services (user_id, desc, interaction_mode, url, endpoint, api_key, params, auth) VALUES
('global', 'openproject_weekly_report', 'streamful_http', 'http://localhost:8000/mcp', 'https://demo.openproject.com', 'demo-api-key', '{"project_id": 1}', '{"type": "api_key", "value": "demo-api-key"}');
*/

-- Sample templates
/*
INSERT INTO mcp_templates (name, content, description) VALUES
('weekly_report.j2', '# {{ project.name }} Weekly Report\n\n**Week**: {{ week }}\n\n## Tasks\n{% for task in work_packages %}- {{ task.subject }} ({{ task.status }})\n{% endfor %}', 'Standard weekly report template');
*/

-- Add comments for documentation
COMMENT ON TABLE mcp_services IS 'MCP service configurations with user isolation';
COMMENT ON TABLE mcp_executions IS 'MCP tool execution logs for debugging and analytics';
COMMENT ON TABLE mcp_templates IS 'Custom Jinja2 templates for report generation';

COMMENT ON COLUMN mcp_services.user_id IS 'User identifier for multi-tenant isolation';
COMMENT ON COLUMN mcp_services.desc IS 'Human-readable description of the MCP service';
COMMENT ON COLUMN mcp_services.interaction_mode IS 'Communication mode: stdio, http, or sse';
COMMENT ON COLUMN mcp_services.url IS 'URL for HTTP/SSE modes';
COMMENT ON COLUMN mcp_services.endpoint IS 'Target service endpoint (e.g., OpenProject URL)';
COMMENT ON COLUMN mcp_services.api_key IS 'API key for authentication';
COMMENT ON COLUMN mcp_services.params IS 'Default parameters for the service';
COMMENT ON COLUMN mcp_services.auth IS 'Authentication configuration';

-- Display completion message
SELECT 'Database schema initialized successfully' as status;