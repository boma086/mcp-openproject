"""
Simple Configuration System for MCP OpenProject Server

Designed for end users - just set 3 environment variables and go!
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """Simple server configuration for end users."""

    # Required: User must configure these
    openproject_base_url: str
    openproject_api_key: str
    encryption_key: str

    # Optional: Sensible defaults provided
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"
    transport_mode: str = "stdio"

    # JWT: Auto-generated if not provided
    jwt_secret_key: Optional[str] = None

    # Performance: Reasonable defaults
    max_connections: int = 10
    timeout: int = 30
    metrics_port: int = 8001

    def __post_init__(self):
        """Post-initialization setup."""
        # Auto-generate JWT secret if not provided
        if not self.jwt_secret_key:
            import secrets
            self.jwt_secret_key = secrets.token_urlsafe(32)

        # Validate required fields
        if not self.openproject_base_url:
            raise ValueError("OPENPROJECT_BASE_URL is required")
        if not self.openproject_api_key:
            raise ValueError("OPENPROJECT_API_KEY is required")
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY is required")

        # Validate URL format
        if not self.openproject_base_url.startswith(('http://', 'https://')):
            raise ValueError("OPENPROJECT_BASE_URL must start with http:// or https://")


def load_config() -> ServerConfig:
    """Load configuration from environment variables.

    Users only need to set 3 variables in .env file:
    - OPENPROJECT_BASE_URL
    - OPENPROJECT_API_KEY
    - ENCRYPTION_KEY
    """
    return ServerConfig(
        # Required configuration
        openproject_base_url=os.getenv('OPENPROJECT_BASE_URL', ''),
        openproject_api_key=os.getenv('OPENPROJECT_API_KEY', ''),
        encryption_key=os.getenv('ENCRYPTION_KEY', ''),

        # Optional configuration with defaults
        host=os.getenv('MCP_HOST', '0.0.0.0'),
        port=int(os.getenv('MCP_PORT', '8000')),
        debug=os.getenv('MCP_DEBUG', 'false').lower() == 'true',
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        log_format=os.getenv('LOG_FORMAT', 'json'),
        transport_mode=os.getenv('MCP_MODE', 'stdio'),
        jwt_secret_key=os.getenv('JWT_SECRET_KEY'),
        max_connections=int(os.getenv('MAX_CONNECTIONS', '10')),
        timeout=int(os.getenv('TIMEOUT', '30')),
        metrics_port=int(os.getenv('METRICS_PORT', '8001'))
    )