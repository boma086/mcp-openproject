# OpenProject API Client - Claude Development Guidelines

## Component Purpose

This directory contains the auto-generated OpenProject API client library based on the official OpenAPI specification. It provides type-safe Python models and API client classes for interacting with OpenProject instances. The client is generated using openapi-generator-cli and serves as the foundation for all OpenProject integrations.

## 🐍 Python Execution Environment
**虚拟环境路径**: `venv/` (项目根目录下)
**执行模式**: 每次Python命令前需要激活虚拟环境
**标准模式**: `source venv/bin/activate && python <script>`
**检测机制**: 如果命令失败，检查是否未激活虚拟环境

## Architecture & Responsibilities

### Generated Components
- **`openproject_api_client/`**: Auto-generated client library
- **`openproject_api_client/apis/`**: API endpoint implementations
- **`openproject_api_client/models/`**: Pydantic models for API resources
- **`test/`**: Auto-generated test suites
- **`.openapi-generator/`**: Generator configuration and metadata

### Key API Modules
- **`ProjectsApi`**: Project management operations
- **`WorkPackagesApi`**: Task and work package management
- **`UsersApi`**: User and team management
- **`ActivitiesApi`**: Activity logging and tracking

## Task Management Approach

### Expert Coordination Requirements
- **API Integration Specialist**: OpenAPI specification analysis, client optimization
- **Python Expert**: Generated code quality, type hints, performance optimization
- **Testing Expert**: Generated test validation, coverage analysis
- **DevOps Engineer**: Generation pipeline, CI/CD integration

### Task Planning Workflow
1. **Specification Analysis**: Review OpenAPI spec for completeness
2. **Generation Optimization**: Configure generator for optimal output
3. **Code Quality Review**: Validate generated Python code patterns
4. **Integration Testing**: Test client against real OpenProject instance
5. **Documentation**: Generate comprehensive API documentation

## Development Standards

### Code Quality Requirements
- **Type Safety**: Full Pydantic model validation
- **Async Support**: Async/await patterns for all API calls
- **Error Handling**: Proper exception hierarchy and handling
- **Performance**: Efficient serialization and connection management

### Custom Extensions
- **Retry Logic**: Exponential backoff for failed requests
- **Rate Limiting**: Request throttling and quota management
- **Caching**: Response caching for frequently accessed data
- **Logging**: Structured logging for API interactions

## Current Development Priorities

### 🔴 Critical Issues (Week 1)
1. **Generation Pipeline**: Automate client regeneration process
2. **Type Validation**: Ensure all models have proper type hints
3. **Async Optimization**: Implement async patterns throughout
4. **Error Handling**: Enhance exception handling and recovery

### 🟡 Important Features (Week 2)
1. **Custom Extensions**: Add retry logic and rate limiting
2. **Performance Optimization**: Connection pooling and caching
3. **Documentation**: Generate comprehensive API docs
4. **Testing Enhancement**: Improve generated test coverage

### 🟢 Enhancement Opportunities (Week 3)
1. **Advanced Features**: Pagination helpers, bulk operations
2. **Monitoring**: API usage metrics and performance tracking
3. **Validation**: Enhanced model validation and custom rules
4. **Utilities**: Helper functions for common operations

## Generation Process

### OpenAPI Specification
- **Source**: https://community.openproject.org/api/v3/spec.yml
- **Version**: OpenProject API v3
- **Format**: OpenAPI 3.0 specification
- **Validation**: Spec validation before generation

### Generator Configuration
```yaml
# .openapi-generator/config.yml
generatorName: python
outputDir: .
inputSpec: https://community.openproject.org/api/v3/spec.yml
templateDir: templates
additionalProperties:
  packageName: openproject_api_client
  projectName: OpenProject API Client
  packageVersion: 1.0.0
  generateSourceCodeOnly: true
```

### Generation Commands
```bash
# Generate client from OpenAPI spec (remember to activate virtual environment)
source venv/bin/activate && openapi-generator-cli generate \
  -i https://community.openproject.org/api/v3/spec.yml \
  -g python \
  -o . \
  --additional-properties=packageName=openproject_api_client,generateSourceCodeOnly=true \
  --skip-validate-spec

# Validate generated code (remember to activate virtual environment)
source venv/bin/activate && python -m pytest test/ -v
source venv/bin/activate && python -m flake8 openproject_api_client/
source venv/bin/activate && python -m mypy openproject_api_client/
```

## API Client Usage

### Basic Usage Patterns
```python
from openproject_api_client.apis import ProjectsApi, WorkPackagesApi
from openproject_api_client.models import Project, WorkPackage

# Initialize API clients
projects_api = ProjectsApi(
    base_url="https://openproject.example.com",
    api_key="your-api-key"
)

work_packages_api = WorkPackagesApi(
    base_url="https://openproject.example.com", 
    api_key="your-api-key"
)

# Fetch projects
projects = await projects_api.get_projects()
for project in projects._embedded.elements:
    print(f"Project: {project.name} (ID: {project.id})")

# Fetch work packages for a project
work_packages = await work_packages_api.get_work_packages(
    project_id=1,
    filters=[{"status_id": {"operator": "!", "values": [""]}}]
)
```

### Async Usage with Connection Pooling
```python
import httpx
from openproject_api_client.apis import ProjectsApi

# Configure HTTP client with connection pooling
http_client = httpx.AsyncClient(
    base_url="https://openproject.example.com",
    headers={"Authorization": "Bearer your-api-key"},
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
)

# Use client with connection pooling
projects_api = ProjectsApi(
    base_url="https://openproject.example.com",
    api_key="your-api-key",
    async_client=http_client
)

try:
    projects = await projects_api.get_projects()
    # Process projects...
finally:
    await http_client.aclose()
```

## Model Architecture

### Core Model Types
- **`ProjectModel`**: Project metadata and configuration
- **`WorkPackageModel`**: Task and work package details
- **`UserModel`**: User profile and permissions
- **`ActivityModel`**: Activity log entries

### Model Validation
```python
from openproject_api_client.models import WorkPackageWriteModel
from pydantic import ValidationError

try:
    # Create work package with validation
    work_package = WorkPackageWriteModel(
        subject="New Task",
        description={"raw": "Task description"},
        project_id=1,
        type_id=1,
        status_id=1
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Custom Model Extensions
```python
# Extend generated models with custom methods
class EnhancedWorkPackage(WorkPackageModel):
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        from datetime import datetime
        return datetime.now().date() > self.due_date
    
    def get_priority_level(self) -> str:
        priority_map = {
            "Low": 1, "Normal": 2, "High": 3, "Urgent": 4
        }
        return priority_map.get(getattr(self.priority, 'name', 'Normal'), 2)
```

## Error Handling & Resilience

### Exception Hierarchy
```python
from openproject_api_client.exceptions import (
    ApiException,
    UnauthorizedException,
    NotFoundException,
    ValidationException,
    RateLimitException
)

try:
    project = await projects_api.get_project(project_id=999)
except NotFoundException:
    print("Project not found")
except UnauthorizedException:
    print("Authentication failed")
except ApiException as e:
    print(f"API error: {e.status} - {e.reason}")
```

### Retry Logic Implementation
```python
import asyncio
from functools import wraps

def retry_on_failure(max_retries=3, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
            return None
        return wrapper
    return decorator

# Apply retry to API calls
@retry_on_failure(max_retries=3)
async def get_project_with_retry(project_id: int):
    return await projects_api.get_project(project_id=project_id)
```

## Performance Optimization

### Connection Pooling
```python
# Optimized HTTP client configuration
http_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0
    ),
    timeout=httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=30.0
    )
)
```

### Response Caching
```python
from functools import lru_cache
from typing import Optional

class CachedProjectsApi(ProjectsApi):
    @lru_cache(maxsize=128)
    def _get_project_cache_key(self, project_id: int) -> str:
        return f"project_{project_id}"
    
    async def get_project_cached(self, project_id: int) -> Optional[ProjectModel]:
        cache_key = self._get_project_cache_key(project_id)
        # Implement cache logic here
        return await self.get_project(project_id=project_id)
```

## Testing Strategy

### Generated Tests
- **Model Validation**: Test all Pydantic model validation
- **API Endpoints**: Test each API endpoint with various inputs
- **Error Scenarios**: Test error handling and edge cases
- **Type Checking**: Verify type hints and mypy compliance

### Custom Integration Tests
```python
import pytest
from openproject_api_client.apis import ProjectsApi

@pytest.mark.asyncio
async def test_projects_api_integration():
    api = ProjectsApi(
        base_url="http://localhost:8090",
        api_key="test-api-key"
    )
    
    # Test project listing
    projects = await api.get_projects()
    assert projects._embedded is not None
    assert len(projects._embedded.elements) > 0
    
    # Test individual project retrieval
    first_project = projects._embedded.elements[0]
    project_detail = await api.get_project(project_id=first_project.id)
    assert project_detail.id == first_project.id
    assert project_detail.name == first_project.name
```

## Integration Points

### with mcp-server
- **Primary Consumer**: MCP server uses this client for all OpenProject interactions
- **Error Propagation**: Proper error handling for MCP protocol responses
- **Performance Optimization**: Connection pooling and async patterns
- **Configuration**: Secure credential management and endpoint configuration

### with mcp-client
- **Indirect Integration**: Through MCP server responses
- **Data Transformation**: Model serialization for template rendering
- **Caching**: Response caching for improved performance
- **Monitoring**: API usage tracking and metrics

## Maintenance & Updates

### Regeneration Process
1. **Update Detection**: Monitor OpenAPI spec changes
2. **Backup Customizations**: Preserve custom extensions and utilities
3. **Regenerate Client**: Run openapi-generator-cli
4. **Restore Customizations**: Re-apply custom extensions
5. **Validation**: Run comprehensive test suite
6. **Documentation**: Update integration documentation

### Version Management
- **Semantic Versioning**: Follow SemVer for client releases
- **Compatibility**: Maintain backward compatibility where possible
- **Deprecation**: Clear deprecation notices for breaking changes
- **Migration**: Provide migration guides for major updates

## Expert Review Checklist

### API Integration Specialist Review Items
- [ ] OpenAPI specification completeness and accuracy
- [ ] Generated code quality and patterns
- [ ] Error handling and exception design
- [ ] Performance optimization opportunities
- [ ] Integration with consuming applications

### Python Expert Review Items
- [ ] Type hints and mypy compliance
- [ ] Async/await pattern implementation
- [ ] Pydantic model validation and design
- [ ] Code organization and structure
- [ ] Performance and memory optimization

### Testing Expert Review Items
- [ ] Generated test coverage and quality
- [ ] Integration test comprehensiveness
- [ ] Error scenario testing
- [ ] Performance and load testing
- [ ] Test maintenance and automation

## Common Tasks & Patterns

### Adding Custom API Methods
```python
class ExtendedWorkPackagesApi(WorkPackagesApi):
    async def get_work_packages_by_status(
        self, 
        project_id: int, 
        status_id: int
    ) -> WorkPackageCollectionModel:
        """Get work packages filtered by status"""
        return await self.get_work_packages(
            filters=[{"status_id": {"operator": "=", "values": [str(status_id)]}}],
            project_id=project_id
        )
    
    async def bulk_update_status(
        self, 
        work_package_ids: list[int], 
        new_status_id: int
    ) -> list[WorkPackageModel]:
        """Update status for multiple work packages"""
        results = []
        for wp_id in work_package_ids:
            updated = await self.update_work_package(
                id=wp_id,
                work_package_write_model={"status_id": new_status_id}
            )
            results.append(updated)
        return results
```

### Custom Model Validation
```python
from pydantic import validator

class ValidatedWorkPackageWrite(WorkPackageWriteModel):
    @validator('subject')
    def subject_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Subject cannot be empty')
        return v.strip()
    
    @validator('due_date')
    def due_date_must_be_future(cls, v):
        if v and v < datetime.now().date():
            raise ValueError('Due date must be in the future')
        return v
```

### Performance Monitoring
```python
import time
from functools import wraps

def monitor_api_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            print(f"API call {func.__name__} took {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            print(f"API call {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Apply monitoring to API calls
monitored_get_project = monitor_api_performance(projects_api.get_project)
```
