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

### Release Process

1. **Create a release tag** following semantic versioning:
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0 - Description of changes"
   git push origin v1.2.0
   ```

2. **GitHub Actions will automatically**:
   - Build multi-platform Docker images (amd64, arm64)
   - Push to GitHub Container Registry (`ghcr.io/hossain-khan/image-insights-api`)
   - Create a GitHub Release with auto-generated changelog

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
