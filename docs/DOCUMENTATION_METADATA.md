# Documentation Metadata Management

## Overview

This document explains how documentation metadata is managed in the Image Insights API OpenAPI specification.

## Metadata Included in OpenAPI Spec

The auto-generated OpenAPI specification now includes comprehensive metadata:

### Contact Information
```json
"contact": {
  "name": "Image Insights API",
  "url": "https://github.com/hossain-khan/image-insights-api",
  "email": "support@image-insights-api.local"
}
```

### License Information
```json
"license": {
  "name": "MIT",
  "url": "https://opensource.org/licenses/MIT"
}
```

### Version
- Automatically synced from [app/__version__.py](../app/__version__.py)
- Current version: `1.7.0`

### Tag Descriptions
Tags are defined with detailed descriptions in [app/main.py](../app/main.py):
- **health**: Health check endpoints to verify API status
- **image-analysis**: Image analysis endpoints for brightness metrics and luminance calculations

### Endpoint Metadata
Each endpoint includes:
- **summary**: Brief title (e.g., "Analyze Image Brightness")
- **description**: Detailed markdown documentation
- **response_description**: Describes the response format
- **operationId**: Unique identifier for the operation

## Configuration

All metadata is configured in [app/main.py](../app/main.py) using FastAPI's built-in parameters:

```python
app = FastAPI(
    title="Image Insights API",
    description="...",
    version=__version__,
    contact={...},
    license_info={...},
    tags_metadata=[...],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```

## How It Works

### Hybrid Approach

This implementation uses a **hybrid approach**:

1. **Source of Truth**: Code (docstrings, FastAPI decorators)
2. **Auto-Generation**: `scripts/export_openapi.py` exports the spec from the running API
3. **Metadata**: Added via FastAPI configuration (`contact`, `license_info`, `tags_metadata`)
4. **Consistency**: Pre-commit hooks ensure the spec is always in sync

### Benefits

✅ **No Manual Maintenance**: Spec is always in sync with actual code  
✅ **Rich Documentation**: Includes contact, license, and detailed descriptions  
✅ **Single Source of Truth**: All metadata defined in code  
✅ **Scalable**: New endpoints automatically appear in the spec  
✅ **Professional**: Complete OpenAPI 3.1.0 compliance  

## Updating Metadata

### Adding Contact Information
Edit the `contact` dict in [app/main.py](../app/main.py):
```python
contact={
    "name": "Image Insights API",
    "url": "https://github.com/hossain-khan/image-insights-api",
    "email": "support@image-insights-api.local",
}
```

### Updating Version
Edit [app/__version__.py](../app/__version__.py):
```python
__version__ = "1.5.0"
```

### Improving Endpoint Documentation
Update endpoint docstrings and decorators in [app/api/image_analysis.py](../app/api/image_analysis.py):
```python
@router.post(
    "/analysis",
    summary="Analyze Image Brightness",
    response_description="Image analysis results with brightness metrics",
)
async def analyze_image(...):
    """Detailed markdown documentation here."""
```

## Verifying Metadata

After making changes, regenerate the spec:
```bash
# Make sure the API is running
python -m uvicorn app.main:app --reload

# Export the spec
python scripts/export_openapi.py
```

Verify the metadata:
```bash
# Check contact info
python -c "import json; spec = json.load(open('docs/swagger.json')); print(spec['info']['contact'])"

# Check license
python -c "import json; spec = json.load(open('docs/swagger.json')); print(spec['info']['license'])"

# Check version
python -c "import json; spec = json.load(open('docs/swagger.json')); print(spec['info']['version'])"
```

## OpenAPI Specification Format

The spec is generated in **OpenAPI 3.1.0** format, which includes:
- Modern schema standards
- Better tooling support
- Improved documentation rendering
- Full JSON Schema support

View the interactive API documentation:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## Related Files

- [app/__version__.py](../app/__version__.py) - Version management
- [app/main.py](../app/main.py) - FastAPI configuration and metadata
- [app/api/image_analysis.py](../app/api/image_analysis.py) - Endpoint documentation
- [scripts/export_openapi.py](../scripts/export_openapi.py) - Auto-generation script
- [.pre-commit-config.yaml](../.pre-commit-config.yaml) - Git hooks for auto-generation
