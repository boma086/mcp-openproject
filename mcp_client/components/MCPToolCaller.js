import React, { useState, useEffect } from 'react';
import { useCopilotAction, useCopilotReadable } from '@copilotkit/react-core';

/**
 * MCP Tool Caller Component for AI Website Integration
 *
 * This component provides CopilotKit integration for calling MCP tools
 * from an AI website frontend. It supports:
 * - Tool execution via CopilotKit actions
 * - State management for tool results
 * - User isolation for multi-tenant environments
 * - Error handling and loading states
 */

function MCPToolCaller({ userId = 'global' }) {
  const [toolState, setToolState] = useState({
    isLoading: false,
    error: null,
    lastResult: null,
    availableTools: []
  });

  const readableState = useCopilotReadable({
    description: "MCP tool execution state and results",
    defaultValue: {
      isLoading: false,
      error: null,
      lastResult: null,
      availableTools: []
    },
  });

  // Update readable state when tool state changes
  useEffect(() => {
    readableState.value = toolState;
  }, [toolState, readableState]);

  // CopilotKit action for calling MCP tools
  useCopilotAction({
    name: "callMCPTool",
    description: "Call a configured MCP tool with parameters",
    parameters: [
      {
        name: "desc",
        type: "string",
        required: true,
        description: "Description of the MCP tool to call (e.g., 'openproject_weekly_report')"
      },
      {
        name: "params",
        type: "object",
        required: false,
        description: "Parameters to pass to the MCP tool",
        default: {}
      },
      {
        name: "userId",
        type: "string",
        required: false,
        description: "User ID for tool isolation",
        default: userId
      }
    ],
    handler: async ({ desc, params, userId }) => {
      try {
        setToolState(prev => ({ ...prev, isLoading: true, error: null }));

        const response = await fetch(`/api/mcp/${desc}?user_id=${userId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            desc,
            params,
            user_id: userId
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        setToolState(prev => ({
          ...prev,
          isLoading: false,
          lastResult: data.result,
          error: null
        }));

        return data.result;
      } catch (error) {
        const errorMessage = error.message || 'Failed to call MCP tool';
        setToolState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage
        }));
        throw error;
      }
    },
  });

  // CopilotKit action for managing MCP configurations
  useCopilotAction({
    name: "manageMCPConfig",
    description: "Add, update, or delete MCP tool configurations",
    parameters: [
      {
        name: "action",
        type: "string",
        required: true,
        description: "Action to perform: 'add', 'update', 'delete', 'list'"
      },
      {
        name: "config",
        type: "object",
        required: false,
        description: "Configuration object for add/update actions"
      },
      {
        name: "desc",
        type: "string",
        required: false,
        description: "Tool description for delete action"
      },
      {
        name: "userId",
        type: "string",
        required: false,
        description: "User ID for configuration management",
        default: userId
      }
    ],
    handler: async ({ action, config, desc, userId }) => {
      try {
        setToolState(prev => ({ ...prev, isLoading: true, error: null }));

        let response;

        switch (action) {
          case 'add':
          case 'update':
            response = await fetch('/api/mcp-config', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                user_id: userId,
                config
              }),
            });
            break;

          case 'delete':
            if (!desc) {
              throw new Error('Tool description is required for delete action');
            }
            response = await fetch(`/api/mcp-config/${desc}?user_id=${userId}`, {
              method: 'DELETE',
            });
            break;

          case 'list':
            response = await fetch(`/api/mcp-config?user_id=${userId}`);
            break;

          default:
            throw new Error(`Unknown action: ${action}`);
        }

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        setToolState(prev => ({
          ...prev,
          isLoading: false,
          error: null
        }));

        return data;
      } catch (error) {
        const errorMessage = error.message || 'Failed to manage MCP configuration';
        setToolState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage
        }));
        throw error;
      }
    },
  });

  // CopilotKit action for template management
  useCopilotAction({
    name: "manageTemplate",
    description: "Update or retrieve Jinja2 templates for report formatting",
    parameters: [
      {
        name: "action",
        type: "string",
        required: true,
        description: "Action to perform: 'update', 'get'"
      },
      {
        name: "templateName",
        type: "string",
        required: true,
        description: "Name of the template to manage"
      },
      {
        name: "content",
        type: "string",
        required: false,
        description: "Template content for update action"
      },
    ],
    handler: async ({ action, templateName, content }) => {
      try {
        setToolState(prev => ({ ...prev, isLoading: true, error: null }));

        let response;

        if (action === 'update') {
          if (!content) {
            throw new Error('Template content is required for update action');
          }
          response = await fetch(`/api/templates/${templateName}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              content,
              user_id: 'admin' // Only admin can update templates
            }),
          });
        } else if (action === 'get') {
          response = await fetch(`/api/templates/${templateName}`);
        } else {
          throw new Error(`Unknown action: ${action}`);
        }

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        setToolState(prev => ({
          ...prev,
          isLoading: false,
          error: null
        }));

        return data;
      } catch (error) {
        const errorMessage = error.message || 'Failed to manage template';
        setToolState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage
        }));
        throw error;
      }
    },
  });

  // Render component status
  return (
    <div className="mcp-tool-caller">
      <div className="mcp-status">
        <h3>MCP Tool Integration Status</h3>
        <div className="status-indicators">
          <span className={`status-indicator ${toolState.isLoading ? 'loading' : 'idle'}`}>
            {toolState.isLoading ? '🔄 Processing...' : '⚡ Ready'}
          </span>
          {toolState.error && (
            <span className="error-indicator">
              ❌ Error: {toolState.error}
            </span>
          )}
        </div>

        {toolState.lastResult && (
          <div className="last-result">
            <h4>Last Result:</h4>
            <pre>{JSON.stringify(toolState.lastResult, null, 2)}</pre>
          </div>
        )}
      </div>

      <div className="mcp-instructions">
        <h4>Available CopilotKit Actions:</h4>
        <ul>
          <li><code>callMCPTool</code> - Execute configured MCP tools</li>
          <li><code>manageMCPConfig</code> - Add/update/delete MCP configurations</li>
          <li><code>manageTemplate</code> - Manage report templates</li>
        </ul>
      </div>
    </div>
  );
}

export default MCPToolCaller;