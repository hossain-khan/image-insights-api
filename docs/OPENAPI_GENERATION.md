# OpenAPI Spec Auto-Generation Guide

This project uses an automated workflow to keep the API documentation in sync with your code.

## Overview

The `docs/swagger.json` file is **auto-generated** from your FastAPI application. This ensures the OpenAPI specification always matches your actual API implementation.

## Quick Start

### 1. Export the OpenAPI Spec Manually

If you've made changes to your API endpoints and want to update the documentation:

```bash
# Terminal 1: Start the API server
python -m uvicorn app.main:app --reload

# Terminal 2: Export the OpenAPI spec
python scripts/export_openapi.py
```

**Output:**
```
📡 Fetching OpenAPI spec from http://localhost:8080/openapi.json...
✅ OpenAPI spec exported to docs/swagger.json
```

### 2. Auto-Export with Pre-Commit Hooks

To automatically export the spec whenever you commit, set up pre-commit hooks:

```bash
# Install pre-commit (one-time setup)
pip install pre-commit

# Install the git hooks
pre-commit install

# Now the OpenAPI spec will be auto-exported on each commit
git commit -m "feat: add new endpoint"
```

## Workflow

### When to Update the Spec

The OpenAPI spec is automatically updated when:
- ✅ You run `python scripts/export_openapi.py`
- ✅ You commit code (if pre-commit hooks are installed)
- ✅ CI/CD pipeline runs (if configured)

### Manual Update

```bash
# Start the API
python -m uvicorn app.main:app --reload

# In another terminal
python scripts/export_openapi.py

# The spec is now updated and ready to commit
git add docs/swagger.json
git commit -m "docs: update OpenAPI spec"
```

## Advanced Usage

### Specify a Custom Server URL

If your API is running on a different port:

```bash
python scripts/export_openapi.py --url http://localhost:3000
```

### Specify Output Path

To save to a different location:

```bash
python scripts/export_openapi.py --output path/to/custom/openapi.json
```

## View the Documentation

Once the spec is exported, you can view the interactive API documentation:

- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc
- **OpenAPI JSON:** http://localhost:8080/openapi.json

## Troubleshooting

### Script Says "Could not connect to server"

Make sure the API is running:
```bash
python -m uvicorn app.main:app --reload
```

Then run the export script in another terminal.

### Pre-commit Hook Not Working

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

### Modified swagger.json Not Committed

The pre-commit hook exports the spec but you still need to add it:
```bash
git add docs/swagger.json
git commit --amend --no-edit
```

## Notes

- `docs/swagger.json` is **generated**, not manually maintained
- Always run the export script after API changes
- The pre-commit hook helps automate this process
- Never manually edit `docs/swagger.json` — your changes will be overwritten
