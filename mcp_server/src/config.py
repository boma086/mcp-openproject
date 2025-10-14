"""
Configuration management for MCP OpenProject Server.

Simplified configuration requiring only 3 environment variables.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Server configuration dataclass."""
    openproject_base_url: str
    openproject_api_key: str
    encryption_key: str
    debug: bool = False

    def validate(self) -> bool:
        """Validate configuration."""
        errors = []

        if not self.openproject_base_url:
            errors.append("OpenProject base URL is required")
        elif not self.openproject_base_url.startswith(('http://', 'https://')):
            errors.append("OpenProject base URL must start with http:// or https://")

        if not self.openproject_api_key:
            errors.append("OpenProject API key is required")

        if not self.encryption_key:
            errors.append("Encryption key is required")
        elif len(self.encryption_key) < 16:
            errors.append("Encryption key must be at least 16 characters long")

        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        return True

    def get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters."""
        return {
            "base_url": self.openproject_base_url,
            "api_key": self.openproject_api_key,
            "timeout": 30,
            "verify_ssl": True
        }

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "encryption_key": self.encryption_key,
            "debug": self.debug,
            "allowed_hosts": ["localhost", "127.0.0.1"]
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "openproject_base_url": self.openproject_base_url,
            "openproject_api_key": "***" + self.openproject_api_key[-4:] if self.openproject_api_key else "",
            "encryption_key": "***" + self.encryption_key[-4:] if self.encryption_key != "default-encryption-key" else "default",
            "debug": self.debug
        }


def load_config() -> ServerConfig:
    """Load configuration from environment variables."""
    # Priority: environment variables > defaults
    openproject_base_url = os.getenv("OPENPROJECT_BASE_URL", "http://localhost:8080")
    openproject_api_key = os.getenv("OPENPROJECT_API_KEY", "")
    encryption_key = os.getenv("ENCRYPTION_KEY", "default-encryption-key")
    debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")

    config = ServerConfig(
        openproject_base_url=openproject_base_url,
        openproject_api_key=openproject_api_key,
        encryption_key=encryption_key,
        debug=debug
    )

    logger.info(f"Configuration loaded: {config.to_dict()}")
    return config


def validate_environment() -> bool:
    """Validate that required environment variables are set."""
    required_vars = {
        "OPENPROJECT_BASE_URL": "OpenProject base URL",
        "OPENPROJECT_API_KEY": "OpenProject API key",
        "ENCRYPTION_KEY": "Encryption key"
    }

    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")

    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        return False

    return True


def get_environment_info() -> Dict[str, Any]:
    """Get information about the current environment."""
    return {
        "python_version": os.sys.version,
        "environment_variables": {
            "OPENPROJECT_BASE_URL": "Set" if os.getenv("OPENPROJECT_BASE_URL") else "Not set",
            "OPENPROJECT_API_KEY": "Set" if os.getenv("OPENPROJECT_API_KEY") else "Not set",
            "ENCRYPTION_KEY": "Set" if os.getenv("ENCRYPTION_KEY") else "Not set",
            "DEBUG": os.getenv("DEBUG", "Not set")
        },
        "working_directory": os.getcwd(),
        "user": os.getenv("USER", "unknown")
    }