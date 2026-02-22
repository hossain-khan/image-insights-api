# Copilot Instructions for Image Insights API

## Project Overview

This is a lightweight REST API for image brightness analysis using ITU-R BT.709 (Rec. 709) luminance standard. Built with FastAPI and Python 3.10+.

- **Repository**: https://github.com/hossain-khan/image-insights-api
- **Documentation**: [docs/API_DOC.md](../docs/API_DOC.md)
- **OpenAPI Spec**: [docs/swagger.json](../docs/swagger.json)

## Code Quality Standards

### Style & Formatting

- Follow PEP 8 style guidelines
- Use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Maximum line length: 120 characters
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes

### Architecture

- Keep core business logic in `app/core/` modules
- API endpoints go in `app/api/` directory
- Configuration in `app/config.py`
- Follow single responsibility principle

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Tests are located in `tests/` directory
- Use pytest fixtures from `tests/conftest.py`

## Pre-PR Checklist

**Always run these checks before creating a pull request:**

```bash
# 1. Run linting
ruff check .

# 2. Run formatting check
ruff format --check .

# 3. Run tests
pytest

# 4. Run tests with coverage (optional)
pytest --cov=app --cov-report=term-missing

# 5. Build Docker image to verify it works
docker build -t image-insights-api .
```

### Quick Fix Commands

```bash
# Auto-fix linting issues
ruff check --fix .

# Auto-format code
ruff format .
```

## Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/).

### Version Format: `MAJOR.MINOR.PATCH`

| Type | When to Increment | Example |
|------|-------------------|---------|
| **MAJOR** | Breaking API changes, incompatible changes | `1.0.0` → `2.0.0` |
| **MINOR** | New features, backward-compatible additions | `1.0.0` → `1.1.0` |
| **PATCH** | Bug fixes, documentation, backward-compatible fixes | `1.0.0` → `1.0.1` |

### Centralized Version Management

The version is managed in a single location:

**File**: `app/__version__.py`
```python
"""Version information for Image Insights API."""

__version__ = "1.1.0"
```

This version is automatically used in:
- FastAPI documentation (OpenAPI spec)
- Health check endpoints (`GET /` and `GET /health`)
- Docker image tags (via GitHub Actions release workflow)

**⚠️ IMPORTANT: When updating the version, also update these files:**

1. **`docs/swagger.json`** - Automatically updated via the export script, but manually update version in health check examples
2. **`docs/API_DOC.md`** - Update health check response examples to reflect the new version (lines ~36, ~50)
3. **`app/main.py`** - Update hardcoded versions in OpenAPI examples for health check endpoints

### OpenAPI Spec Generation Workflow

The `docs/swagger.json` is auto-generated from the running API using `scripts/export_openapi.py`. Follow these steps when updating versions:

**Step 1: Update version in code**
```bash
# Edit app/__version__.py
__version__ = "1.6.0"
```

**Step 2: Update hardcoded examples in code** (health check endpoints)

Update the example versions in `app/main.py` for the `GET /` and `GET /health` endpoints:
```python
@app.get("/", ...)
responses={
    200: {
        "content": {
            "application/json": {
                "examples": {
                    "success": {
                        "value": {
                            "version": "1.6.0",  # Update this
                            ...
                        }
                    }
                }
            }
        }
    }
}
```

**Step 3: Update API documentation examples**

Update `docs/API_DOC.md` health check response examples:
```markdown
#### `GET /`
Response:
```json
{
  "version": "1.6.0",  # Update this
  ...
}
```
```

**Step 4: Start the API server**
```bash
python -m uvicorn app.main:app --reload
```

**Step 5: Regenerate OpenAPI spec**
```bash
# In another terminal
python scripts/export_openapi.py
```

This automatically exports the OpenAPI spec to `docs/swagger.json` with all the latest examples.

**Step 6: Verify the spec was updated**
```bash
# Check that versions are correct in the exported spec
python -c "import json; spec = json.load(open('docs/swagger.json')); print('API Version:', spec['info']['version'])"
```

**To update the version:**

1. Edit `app/__version__.py` and update `__version__`:
   ```bash
   # Example: bumping from 1.0.0 to 1.1.0
   echo '__version__ = "1.1.0"' > app/__version__.py
   ```

2. Update `docs/swagger.json`:
   ```json
   "version": "1.1.0"
   ```

3. Update `docs/API_DOC.md` health check examples with the new version

4. Commit all changes:
   ```bash
   git add app/__version__.py docs/swagger.json docs/API_DOC.md
   git commit -m "chore: bump version to 1.1.0"
   ```

3. Create and push the release tag (see Release Process below)

### Release Process

> **📖 Full Documentation:** See [docs/RELEASE_PROCESS.md](../docs/RELEASE_PROCESS.md) for comprehensive release workflow, checklist, and troubleshooting guide.

**Quick Release Workflow:**

**Step 1: Create a release branch**
```bash
git checkout -b release/v1.2.0
```

**Step 2: Update the version** in `app/__version__.py`:
```python
__version__ = "1.2.0"
```

**Step 3: Commit the version bump**
```bash
git add app/__version__.py
git commit -m "chore: bump version to 1.2.0"
```

**Step 4: Push the release branch and create a pull request**
```bash
git push origin release/v1.2.0
```
Then create a PR for review before merging to main.

**Step 5: After PR is merged, create the release tag** on main following semantic versioning:
```bash
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release v1.2.0 - Add edge-based brightness analysis"
git push origin v1.2.0
```

**Step 6: GitHub Actions will automatically** (via [.github/workflows/release.yml](../.github/workflows/release.yml)):
- Build multi-platform Docker images (amd64, arm64)
- Push to GitHub Container Registry (`ghcr.io/hossain-khan/image-insights-api:1.2.0`)
- Create a GitHub Release with auto-generated changelog

**Release Branch Naming Convention:** `release/v<MAJOR>.<MINOR>.<PATCH>`

### Version Examples

- `v1.0.0` → `v1.0.1`: Fixed a bug in histogram calculation
- `v1.0.1` → `v1.1.0`: Added new `contrast` metric
- `v1.1.0` → `v2.0.0`: Changed response format (breaking change)

### Pre-release Versions

For testing releases before stable:
- Alpha: `v1.2.0-alpha.1`
- Beta: `v1.2.0-beta.1`
- Release Candidate: `v1.2.0-rc.1`

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `ci` | CI/CD changes |
| `chore` | Maintenance tasks |

### Examples

```
feat(api): add contrast metric endpoint
fix(core): handle edge case in histogram calculation
docs: update API documentation with new examples
ci: add Python 3.12 to test matrix
```

## Branch Naming

Use descriptive branch names with prefixes:

- `feat/add-contrast-metric`
- `fix/histogram-edge-case`
- `docs/update-api-examples`
- `ci/add-security-scanning`
- `refactor/optimize-luminance-calculation`

## API Constraints

When making changes, respect these constraints:

| Constraint | Value |
|------------|-------|
| Max file size | 5 MB |
| Supported formats | JPEG, PNG |
| Max dimension | 512 px (auto-resized) |
| Response time target | < 100ms |

## Environment Variables

Configure the API using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DETAILED_LOGGING` | `true` | Enable detailed application logging with request info, file details, processing times, and dimensions |

**Usage:**

```bash
# Disable detailed logging for production
docker run -e ENABLE_DETAILED_LOGGING=false image-insights-api

# Or in docker-compose.yml
environment:
  - ENABLE_DETAILED_LOGGING=false
```

## Dependencies

- Keep dependencies minimal
- Pin versions in `requirements.txt`
- Security scan dependencies regularly
- Prefer standard library when possible
