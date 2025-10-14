"""
Security utilities for MCP OpenProject Server.

Simplified security management using environment variables.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base security error."""
    pass


class AuthenticationError(SecurityError):
    """Authentication failed."""
    pass


class SecurityManager:
    """Simplified security manager using environment variables."""

    def __init__(self, api_key: str = "", encryption_key: str = ""):
        self.api_key = api_key or os.getenv('OPENPROJECT_API_KEY', '')
        self.encryption_key = encryption_key or os.getenv('ENCRYPTION_KEY', 'default-encryption-key')
        self.initialized = False

    def initialize(self) -> None:
        """Initialize security manager."""
        if not self.api_key:
            raise AuthenticationError("API key not configured")
        if not self.encryption_key:
            raise AuthenticationError("Encryption key not configured")
        if len(self.encryption_key) < 16:
            raise AuthenticationError("Encryption key must be at least 16 characters long")

        self.initialized = True
        logger.info("Security manager initialized successfully")

    def validate_api_key(self, provided_key: str) -> bool:
        """Validate API key."""
        if not self.initialized:
            raise AuthenticationError("Security manager not initialized")
        return provided_key == self.api_key

    def get_api_key(self) -> str:
        """Get API key."""
        return self.api_key

    def get_encryption_key(self) -> str:
        """Get encryption key."""
        return self.encryption_key

    def sanitize_input(self, data: Any) -> Any:
        """Basic input sanitization."""
        if isinstance(data, str):
            # Remove control characters
            return ''.join(char for char in data if ord(char) >= 32 or char in '\n\r\t')
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data

    def validate_project_id(self, project_id: int) -> int:
        """Validate project ID."""
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("Project ID must be a positive integer")
        return project_id

    def validate_week_format(self, week: str) -> str:
        """Validate week format (YYYY-WXX)."""
        import re
        if not re.match(r"^20[2-9][0-9]-W([1-9]|[1-4][0-9]|5[0-3])$", week):
            raise ValueError("Week format must be YYYY-WXX (1-53)")
        return week

    async def authenticate(self) -> bool:
        """Simple authentication check."""
        if not self.initialized:
            await self.initialize()
        return True

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.initialized = False
        logger.info("Security manager cleaned up")


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def initialize_security(api_key: str = "", encryption_key: str = "") -> SecurityManager:
    """Initialize global security manager."""
    global _security_manager
    _security_manager = SecurityManager(api_key, encryption_key)
    return _security_manager