# OpenProject API Client - Condensed Reference

## Overview

This directory contains the auto-generated OpenProject API client library based on the official OpenAPI specification. It provides type-safe Python models and API client classes for interacting with OpenProject instances.

**Note**: This documentation condenses 355+ auto-generated files into essential reference information. For complete API details, refer to the [OpenProject API Documentation](https://docs.openproject.org/api/).

## Quick Start

### Basic Usage
```python
from openproject_api_client.apis import ProjectsApi, WorkPackagesApi
from openproject_api_client.models import Project, WorkPackage

# Initialize API client
projects_api = ProjectsApi(
    base_url="https://your.openproject.instance",
    api_key="your-api-key"
)

# Get projects
projects = await projects_api.get_projects()
for project in projects._embedded.elements:
    print(f"Project: {project.name} (ID: {project.id})")
```

## Core API Modules

### Primary APIs
- **`ProjectsApi`**: Project management operations
- **`WorkPackagesApi`**: Task and work package management
- **`UsersApi`**: User and team management
- **`ActivitiesApi`**: Activity logging and tracking
- **`AttachmentsApi`**: File attachment operations
- **`CategoriesApi`**: Work package categories
- **`PrioritiesApi`**: Priority level management
- **`StatusesApi`**: Status management
- **`TypesApi`**: Work package types
- **`VersionsApi`**: Project version management

### Configuration APIs
- **`ConfigurationApi`**: System configuration
- **`MembershipsApi`**: Project memberships
- **`RolesApi`**: Role management
- **`GroupsApi`**: Group management

### Key Model Classes
- **`ProjectModel`**: Project metadata and configuration
- **`WorkPackageModel`**: Task and work package details
- **`UserModel`**: User profile and permissions
- **`ActivityModel`**: Activity log entries

## Common Operations

### Project Management
```python
# List projects
projects = await projects_api.get_projects()

# Get specific project
project = await projects_api.get_project(project_id=123)

# Create project
new_project = await projects_api.create_project(
    project_write_model={
        "name": "New Project",
        "description": {"raw": "Project description"},
        "identifier": "new-project"
    }
)

# Update project
updated = await projects_api.update_project(
    project_id=123,
    project_write_model={"name": "Updated Name"}
)
```

### Work Package Management
```python
# List work packages
work_packages = await work_packages_api.get_work_packages()

# Filter work packages
filtered = await work_packages_api.get_work_packages(
    filters=[
        {"status_id": {"operator": "=", "values": ["1"]}},
        {"project_id": {"operator": "=", "values": ["123"]}}
    ]
)

# Create work package
new_wp = await work_packages_api.create_work_package(
    work_package_write_model={
        "subject": "New Task",
        "description": {"raw": "Task description"},
        "project_id": 123,
        "type_id": 1,
        "status_id": 1
    }
)

# Update work package
updated_wp = await work_packages_api.update_work_package(
    id=456,
    work_package_write_model={"status_id": 2}
)
```

### User Management
```python
# List users
users = await users_api.get_users()

# Get current user
current_user = await users_api.get_user(user_id="me")

# Create user
new_user = await users_api.create_user(
    user_write_model={
        "login": "username",
        "email": "user@example.com",
        "firstName": "First",
        "lastName": "Last"
    }
)
```

## Authentication

### API Key Authentication
```python
# Using API key (recommended)
api = ProjectsApi(
    base_url="https://your.openproject.instance",
    api_key="your-api-key"
)
```

### OAuth Authentication
```python
# Using OAuth token
api = ProjectsApi(
    base_url="https://your.openproject.instance",
    access_token="your-oauth-token"
)
```

## Error Handling

```python
from openproject_api_client.exceptions import (
    ApiException,
    NotFoundException,
    UnauthorizedException,
    ValidationException
)

try:
    project = await projects_api.get_project(project_id=999)
except NotFoundException:
    print("Project not found")
except UnauthorizedException:
    print("Authentication failed")
except ValidationException as e:
    print(f"Validation error: {e}")
except ApiException as e:
    print(f"API error: {e.status} - {e.reason}")
```

## Filtering and Querying

### Basic Filters
```python
# Filter by status
projects = await projects_api.get_projects(
    filters=[{"active": {"operator": "=", "values": ["true"]}}]
)

# Filter by multiple criteria
work_packages = await work_packages_api.get_work_packages(
    filters=[
        {"status_id": {"operator": "!", "values": [""]}},
        {"due_date": {"operator": "<t+", "values": ["7"]}}
    ]
)
```

### Sorting
```python
# Sort results
projects = await projects_api.get_projects(
    sort=[["createdAt", "desc"]]
)
```

### Pagination
```python
# Paginated results
page1 = await projects_api.get_projects(offset=0, pageSize=25)
page2 = await projects_api.get_projects(offset=25, pageSize=25)
```

## Advanced Features

### Batch Operations
```python
# Create multiple work packages
batch_results = []
for wp_data in work_packages_data:
    result = await work_packages_api.create_work_package(
        work_package_write_model=wp_data
    )
    batch_results.append(result)
```

### Async Operations
```python
# Concurrent requests
import asyncio

async def get_multiple_projects(project_ids):
    tasks = [
        projects_api.get_project(project_id=pid)
        for pid in project_ids
    ]
    return await asyncio.gather(*tasks)
```

## Rate Limiting

The client includes built-in rate limiting:
- **Default**: 100 requests per minute
- **Burst**: 10 requests per second
- **Automatic**: Exponential backoff on rate limit exceeded

## Model Validation

All models use Pydantic for validation:
```python
from openproject_api_client.models import WorkPackageWriteModel
from pydantic import ValidationError

try:
    wp = WorkPackageWriteModel(
        subject="Valid Task",
        project_id=123,
        type_id=1,
        status_id=1
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Configuration Options

### Client Configuration
```python
# Custom timeout
api = ProjectsApi(
    base_url="https://your.openproject.instance",
    api_key="your-api-key",
    timeout=30.0
)

# Custom headers
api = ProjectsApi(
    base_url="https://your.openproject.instance",
    api_key="your-api-key",
    default_headers={"User-Agent": "MyApp/1.0"}
)
```

### SSL Configuration
```python
# Custom SSL verification
import ssl

api = ProjectsApi(
    base_url="https://your.openproject.instance",
    api_key="your-api-key",
    verify_ssl=True,
    ssl_context=ssl.create_default_context()
)
```

## Troubleshooting

### Common Issues

**Authentication Failed**
```python
# Check API key and base URL
print(f"Base URL: {api.configuration.host}")
print(f"API Key set: {bool(api.configuration.api_key)}")
```

**Connection Timeout**
```python
# Increase timeout
api.configuration.timeout = 60.0
```

**SSL Certificate Issues**
```python
# Disable SSL verification (not recommended for production)
api.configuration.verify_ssl = False
```

### Debug Mode
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
```

## Complete API Reference

For the complete API reference with all endpoints and models, refer to the official OpenProject documentation:
- [OpenProject API v3 Documentation](https://docs.openproject.org/api/)
- [OpenAPI Specification](https://community.openproject.org/api/v3/spec.yml)

## Version Compatibility

This client is generated from OpenProject API v3 specification and is compatible with:
- OpenProject 12.0+
- Python 3.8+
- FastAPI 0.100+

## Support

For issues and questions:
- OpenProject Community: https://community.openproject.org/
- GitHub Issues: Check the main project repository
- Documentation: https://docs.openproject.org/api/