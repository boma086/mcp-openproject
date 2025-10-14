#!/usr/bin/env python3
"""
OpenProject API Client with proper resource management and connection pooling.

Provides a robust, production-ready client for OpenProject API integration
with connection pooling, retry logic, and proper error handling.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from dataclasses import dataclass
import httpx
import backoff
from pydantic import BaseModel, Field

# Import OpenProject API client
try:
    from openproject_api_client.apis.work_packages_api import WorkPackagesApi
    from openproject_api_client.apis.projects_api import ProjectsApi
    from openproject_api_client.api_client import ApiClient
    from openproject_api_client.configuration import Configuration
    from openproject_api_client.exceptions import ApiException
except ImportError as e:
    logging.warning(f"OpenProject API client not available: {e}")
    # Fallback for development
    WorkPackagesApi = None
    ProjectsApi = None
    ApiClient = None
    Configuration = None
    ApiException = None

try:
    from .config import get_config
    from .security import SecurityError, AuthenticationError
except ImportError:
    # Fallback for testing without full config
    def get_config():
        return None
    class SecurityError(Exception):
        pass
    class AuthenticationError(Exception):
        pass

logger = logging.getLogger(__name__)


@dataclass
class OpenProjectError:
    """OpenProject API error representation."""
    status_code: int
    error_code: Optional[str]
    message: str
    details: Optional[Dict[str, Any]] = None


class OpenProjectClientError(Exception):
    """Base exception for OpenProject client errors."""

    def __init__(self, message: str, error: Optional[OpenProjectError] = None):
        super().__init__(message)
        self.error = error


class OpenProjectConnectionError(OpenProjectClientError):
    """Connection-related errors."""
    pass


class OpenProjectAuthenticationError(OpenProjectClientError):
    """Authentication-related errors."""
    pass


class OpenProjectRateLimitError(OpenProjectClientError):
    """Rate limiting errors."""
    pass


class WorkPackageInfo(BaseModel):
    """Work package information model."""
    id: Optional[int] = None
    subject: str = Field(..., description="Work package subject")
    description: Optional[Dict[str, Any]] = Field(None, description="Work package description")
    status: Optional[str] = Field(None, description="Work package status")
    priority: Optional[str] = Field(None, description="Work package priority")
    assignee: Optional[str] = Field(None, description="Assignee name")
    due_date: Optional[str] = Field(None, description="Due date")
    created_at: Optional[str] = Field(None, description="Creation date")
    updated_at: Optional[str] = Field(None, description="Last update date")


class ProjectInfo(BaseModel):
    """Project information model."""
    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    identifier: str = Field(..., description="Project identifier")
    description: Optional[Dict[str, Any]] = Field(None, description="Project description")
    created_at: Optional[str] = Field(None, description="Creation date")
    updated_at: Optional[str] = Field(None, description="Last update date")


class WeeklyReportData(BaseModel):
    """Weekly report data model."""
    project: ProjectInfo
    work_packages: List[WorkPackageInfo]
    week: str
    summary: Optional[str] = None


class HTTPClientManager:
    """Manages HTTP client lifecycle with connection pooling."""

    def __init__(self, config):
        """
        Initialize HTTP client manager.

        Args:
            config: Configuration instance (unused, we use env vars directly)
        """
        self._client: Optional[httpx.AsyncClient] = None
        # Simple: use environment variable or default
        max_connections = int(os.getenv('MAX_CONNECTIONS', '10'))
        self._semaphore = asyncio.Semaphore(max_connections)

    async def get_client(self) -> httpx.AsyncClient:
        """
        Get HTTP client instance, creating if necessary.

        Returns:
            Configured HTTP client
        """
        if self._client is None or self._client.is_closed:
            await self._create_client()
        return self._client

    async def _create_client(self):
        """Create new HTTP client with proper configuration."""
        # Simple: use environment variables directly
        base_url = os.getenv('OPENPROJECT_BASE_URL', 'http://localhost:8080/')
        timeout = int(os.getenv('TIMEOUT', '30'))

        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            headers={
                "User-Agent": "MCP-OpenProject-Server/1.0",
                "Accept": "application/hal+json",
                "Content-Type": "application/json"
            }
        )
        logger.info("HTTP client created with connection pooling")

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("HTTP client closed")

    @asynccontextmanager
    async def request_context(self):
        """Context manager for HTTP requests with semaphore limiting."""
        async with self._semaphore:
            client = await self.get_client()
            try:
                yield client
            except httpx.RequestError as e:
                logger.error(f"HTTP request failed: {e}")
                raise OpenProjectConnectionError(f"HTTP request failed: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        if self._client and not self._client.is_closed:
            # Note: This is not ideal, should use explicit close
            try:
                asyncio.create_task(self.close())
            except:
                pass


class OpenProjectClient:
    """
    Production-ready OpenProject API client with connection pooling,
    retry logic, and proper error handling.
    """

    def __init__(self, config=None):
        """
        Initialize OpenProject client.

        Args:
            config: Configuration instance
        """
        self.config = config or get_config()
        self.http_manager = HTTPClientManager(self.config)
        self._api_client: Optional[ApiClient] = None
        self._projects_api: Optional[ProjectsApi] = None
        self._work_packages_api: Optional[WorkPackagesApi] = None

        # Simple: get API key from environment variable
        self.api_key = os.getenv('OPENPROJECT_API_KEY', '')
        if not self.api_key:
            raise AuthenticationError("OpenProject API key not configured. Please set OPENPROJECT_API_KEY environment variable.")

    async def _get_api_client(self) -> ApiClient:
        """
        Get configured API client instance.

        Returns:
            Configured API client
        """
        if self._api_client is None:
            if Configuration is None:
                raise OpenProjectClientError("OpenProject API client not available")

            # Simple: use environment variable for base URL
            base_url = os.getenv('OPENPROJECT_BASE_URL', 'http://localhost:8080/')
            configuration = Configuration(
                host=base_url,
                api_key=self.api_key,
                api_key_prefix="apikey"
            )

            # Use our HTTP client for better connection management
            http_client = await self.http_manager.get_client()
            self._api_client = ApiClient(configuration=configuration)

            # Replace the default REST client with our configured one
            if hasattr(self._api_client, 'client'):
                self._api_client.client = http_client

            logger.info("API client initialized")

        return self._api_client

    async def get_projects_api(self) -> ProjectsApi:
        """
        Get Projects API instance.

        Returns:
            Projects API client
        """
        if self._projects_api is None:
            if ProjectsApi is None:
                raise OpenProjectClientError("Projects API not available")

            api_client = await self._get_api_client()
            self._projects_api = ProjectsApi(api_client=api_client)

        return self._projects_api

    async def get_work_packages_api(self) -> WorkPackagesApi:
        """
        Get Work Packages API instance.

        Returns:
            Work Packages API client
        """
        if self._work_packages_api is None:
            if WorkPackagesApi is None:
                raise OpenProjectClientError("Work Packages API not available")

            api_client = await self._get_api_client()
            self._work_packages_api = WorkPackagesApi(api_client=api_client)

        return self._work_packages_api

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, OpenProjectConnectionError, ApiException),
        max_tries=3,
        base=1,
        max_value=30
    )
    async def get_project(self, project_id: int) -> ProjectInfo:
        """
        Get project information.

        Args:
            project_id: Project ID

        Returns:
            Project information

        Raises:
            OpenProjectClientError: If request fails
        """
        try:
            projects_api = await self.get_projects_api()
            project_result = await projects_api.get_project(project_id=project_id)

            # Extract project data from API response
            project_data = self._extract_project_data(project_result)
            logger.info(f"Retrieved project {project_id}: {project_data.name}")

            return project_data

        except ApiException as e:
            if e.status == 401:
                raise OpenProjectAuthenticationError("Authentication failed", OpenProjectError(
                    status_code=e.status,
                    message="Invalid API credentials"
                ))
            elif e.status == 404:
                raise OpenProjectClientError(f"Project {project_id} not found", OpenProjectError(
                    status_code=e.status,
                    message=f"Project {project_id} not found"
                ))
            else:
                raise OpenProjectClientError(f"API error: {e}", OpenProjectError(
                    status_code=e.status,
                    message=str(e)
                ))
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            raise OpenProjectClientError(f"Failed to get project {project_id}: {e}")

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, OpenProjectConnectionError, ApiException),
        max_tries=3,
        base=1,
        max_value=30
    )
    async def get_work_packages(self, project_id: int, filters: Optional[List[Dict[str, Any]]] = None) -> List[WorkPackageInfo]:
        """
        Get work packages for a project.

        Args:
            project_id: Project ID
            filters: Optional filters for work packages

        Returns:
            List of work package information

        Raises:
            OpenProjectClientError: If request fails
        """
        try:
            work_packages_api = await self.get_work_packages_api()

            # Default filters if none provided
            if filters is None:
                filters = [{"status_id": {"operator": "!", "values": [""]}}]

            work_packages_result = await work_packages_api.get_work_packages(
                filters=filters,
                project_id=project_id
            )

            # Extract work package data
            work_packages_data = self._extract_work_packages_data(work_packages_result)
            logger.info(f"Retrieved {len(work_packages_data)} work packages for project {project_id}")

            return work_packages_data

        except ApiException as e:
            if e.status == 401:
                raise OpenProjectAuthenticationError("Authentication failed", OpenProjectError(
                    status_code=e.status,
                    message="Invalid API credentials"
                ))
            elif e.status == 404:
                raise OpenProjectClientError(f"Project {project_id} not found", OpenProjectError(
                    status_code=e.status,
                    message=f"Project {project_id} not found"
                ))
            else:
                raise OpenProjectClientError(f"API error: {e}", OpenProjectError(
                    status_code=e.status,
                    message=str(e)
                ))
        except Exception as e:
            logger.error(f"Failed to get work packages for project {project_id}: {e}")
            raise OpenProjectClientError(f"Failed to get work packages for project {project_id}: {e}")

    async def get_weekly_report(self, project_id: int, week: Optional[str] = None) -> WeeklyReportData:
        """
        Get weekly report data for a project.

        Args:
            project_id: Project ID
            week: Optional week identifier

        Returns:
            Weekly report data

        Raises:
            OpenProjectClientError: If request fails
        """
        try:
            # Get project and work packages concurrently
            project_task = self.get_project(project_id)
            work_packages_task = self.get_work_packages(project_id)

            project, work_packages = await asyncio.gather(
                project_task,
                work_packages_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(project, Exception):
                raise project
            if isinstance(work_packages, Exception):
                raise work_packages

            # Create weekly report
            report = WeeklyReportData(
                project=project,
                work_packages=work_packages,
                week=week or "current",
                summary=f"Found {len(work_packages)} work packages"
            )

            logger.info(f"Generated weekly report for project {project_id}, week {week or 'current'}")
            return report

        except Exception as e:
            logger.error(f"Failed to generate weekly report for project {project_id}: {e}")
            raise

    def _extract_project_data(self, project_result) -> ProjectInfo:
        """Extract project data from API response."""
        if hasattr(project_result, '__dict__'):
            return ProjectInfo(
                id=getattr(project_result, 'id', 0),
                name=getattr(project_result, 'name', 'Unknown Project'),
                identifier=getattr(project_result, 'identifier', ''),
                description=getattr(project_result, 'description', {}),
                created_at=getattr(project_result, 'created_at', ''),
                updated_at=getattr(project_result, 'updated_at', '')
            )
        elif isinstance(project_result, dict):
            return ProjectInfo(**project_result)
        else:
            # Fallback for unexpected response format
            return ProjectInfo(
                id=project_result.get('id', 0),
                name=project_result.get('name', 'Unknown Project'),
                identifier=project_result.get('identifier', ''),
                description=project_result.get('description', {}),
                created_at=project_result.get('created_at', ''),
                updated_at=project_result.get('updated_at', '')
            )

    def _extract_work_packages_data(self, work_packages_result) -> List[WorkPackageInfo]:
        """Extract work packages data from API response."""
        work_packages_list = []

        # Handle different response formats
        if hasattr(work_packages_result, '_embedded') and hasattr(work_packages_result._embedded, 'elements'):
            work_packages_list = work_packages_result._embedded.elements
        elif hasattr(work_packages_result, 'elements'):
            work_packages_list = work_packages_result.elements
        elif isinstance(work_packages_result, dict):
            work_packages_list = work_packages_result.get('_embedded', {}).get('elements', [])
        else:
            work_packages_list = work_packages_result if isinstance(work_packages_result, list) else []

        # Convert to WorkPackageInfo models
        wp_info = []
        for wp in work_packages_list:
            if hasattr(wp, '__dict__'):
                wp_info.append(WorkPackageInfo(
                    id=getattr(wp, 'id', None),
                    subject=getattr(wp, 'subject', ''),
                    description=getattr(wp, 'description', {}),
                    status=getattr(getattr(wp, 'status', None), 'name', None),
                    priority=getattr(getattr(wp, 'priority', None), 'name', None),
                    assignee=getattr(getattr(wp, 'assignee', None), 'name', None),
                    due_date=getattr(wp, 'due_date', None),
                    created_at=getattr(wp, 'created_at', None),
                    updated_at=getattr(wp, 'updated_at', None)
                ))
            elif isinstance(wp, dict):
                wp_info.append(WorkPackageInfo(**wp))

        return wp_info

    async def close(self):
        """Close client and cleanup resources."""
        await self.http_manager.close()
        self._api_client = None
        self._projects_api = None
        self._work_packages_api = None
        logger.info("OpenProject client closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Client factory function
async def create_openproject_client(config=None) -> OpenProjectClient:
    """
    Create and configure OpenProject client.

    Args:
        config: Configuration instance

    Returns:
        Configured OpenProject client
    """
    return OpenProjectClient(config)