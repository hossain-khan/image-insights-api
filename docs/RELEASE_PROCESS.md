# Release Process

This document explains how releases are created and published for the Image Insights API Docker image.

## Quick Overview

The release process is automated via GitHub Actions. To release a new version:

1. Update the version in [../app/__version__.py](../app/__version__.py)
2. Update documentation with new version
3. Merge changes to `main` branch
4. Create and push a git tag (e.g., `v1.2.0`)
5. GitHub Actions automatically builds, tests, and publishes the Docker image

## Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

| Type | When to Increment | Example |
|------|-------------------|---------|
| **MAJOR** | Breaking API changes | `1.0.0` → `2.0.0` |
| **MINOR** | New features (backward-compatible) | `1.0.0` → `1.1.0` |
| **PATCH** | Bug fixes | `1.0.0` → `1.0.1` |

## Step-by-Step Release Guide

### Step 1: Update Version

Edit [../app/__version__.py](../app/__version__.py):

```python
"""Version information for Image Insights API."""

__version__ = "1.2.0"  # Update this
```

### Step 2: Update Documentation

Update version references in user-facing docs:

1. **[API_DOC.md](API_DOC.md)** - Update health check response examples
2. **[swagger.json](swagger.json)** - Update OpenAPI spec version
   - Run `python scripts/export_openapi.py` to regenerate automatically
3. **[../README.md](../README.md)** - Update version badges if needed

### Step 3: Create Release Branch (Optional but Recommended)

```bash
git checkout -b release/v1.2.0
git add app/__version__.py docs/**
git commit -m "chore: bump version to 1.2.0"
git push origin release/v1.2.0
```

Create a Pull Request for review before merging to `main`.

### Step 4: Merge to Main

After PR approval:

```bash
git checkout main
git pull origin main
```

### Step 5: Create and Push Release Tag

```bash
git tag -a v1.2.0 -m "Release v1.2.0 - Brief description of changes"
git push origin v1.2.0
```

**Important:** The tag must be prefixed with `v` (e.g., `v1.2.0`, not `1.2.0`).

## Automated Release Workflow

Once a `v*` tag is pushed, the [../.github/workflows/release.yml](../.github/workflows/release.yml) GitHub Actions workflow automatically:

### 1. **Triggers on Tag Push**
```yaml
on:
  push:
    tags:
      - 'v*'
```

### 2. **Checks Out Code**
Retrieves the repository at the tagged commit.

### 3. **Builds Multi-Platform Docker Images**
- **Platforms:** `linux/amd64` (Intel/AMD) and `linux/arm64` (Apple Silicon)
- **Builder:** Docker Buildx for cross-platform builds
- **Cache:** Uses GitHub Actions cache for faster builds

### 4. **Authenticates and Publishes**
- **Registry:** GitHub Container Registry (ghcr.io)
- **Authentication:** Uses `GITHUB_TOKEN` (automatically provided)
- **Permissions:** Requires `contents: write` and `packages: write`

### 5. **Generates Image Tags**
Multiple tags are created from the semantic version:

```
ghcr.io/hossain-khan/image-insights-api:1.2.0      # Full version
ghcr.io/hossain-khan/image-insights-api:1.2        # Major.minor
ghcr.io/hossain-khan/image-insights-api:1          # Major only
ghcr.io/hossain-khan/image-insights-api:sha-abc123 # Git SHA
```

This allows users to:
- Pin to exact version: `image-insights-api:1.2.0`
- Use latest minor: `image-insights-api:1.2`
- Use latest major: `image-insights-api:1`
- Use development version: `image-insights-api:latest`

### 6. **Creates GitHub Release**
Automatically generates release notes on the Releases page with:
- Changelog (based on commit history and PR descriptions)
- Links to PRs and commits
- Attached artifacts/metadata

## Docker Image Distribution

After release, the Docker image is available at:

```bash
docker pull ghcr.io/hossain-khan/image-insights-api:1.2.0
```

Published images support:
- ✅ `linux/amd64` (Intel/AMD x86-64)
- ✅ `linux/arm64` (ARM 64-bit, Apple Silicon, Raspberry Pi 4+)

## Release Checklist

Before pushing the release tag:

- [ ] Version updated in `app/__version__.py`
- [ ] Documentation updated (API_DOC.md, swagger.json)
- [ ] Changes reviewed in PR
- [ ] All tests passing (`pytest`)
- [ ] Code linted (`ruff check .`)
- [ ] Code formatted (`ruff format .`)
- [ ] Docker image builds locally (`docker build -t test .`)
- [ ] Commit message follows [Conventional Commits](https://www.conventionalcommits.org/)

## Release Notes

When releasing, provide clear release notes in the tag message:

```bash
git tag -a v1.2.0 -m "Release v1.2.0 - Add edge-based brightness analysis

- feat: add left_right edge mode for brightness analysis
- feat: add top_bottom edge mode
- feat: add all edge mode for comprehensive edge analysis
- fix: improve SSRF protection for URL validation
- docs: update API documentation with edge mode examples
- perf: optimize histogram calculation

Breaking Changes: None
"
```

## Monitoring a Release

After pushing a tag:

1. **Watch the workflow:** Visit [Actions](https://github.com/hossain-khan/image-insights-api/actions)
2. **Check the release:** View [Releases](https://github.com/hossain-khan/image-insights-api/releases)
3. **Verify the image:** 
   ```bash
   docker pull ghcr.io/hossain-khan/image-insights-api:1.2.0
   docker run -p 8080:8080 ghcr.io/hossain-khan/image-insights-api:1.2.0
   ```

## Troubleshooting

### Docker Build Fails
- Check Dockerfile syntax: `docker build -t test . --no-cache`
- Ensure all dependencies in `requirements.txt` are compatible
- Run tests locally first: `pytest`

### Release Workflow Doesn't Start
- Verify tag is pushed: `git push origin v1.2.0`
- Check tag format: Must start with `v` (e.g., `v1.2.0`)
- Verify workflow file exists: `.github/workflows/release.yml`

### Image Not Published to Registry
- Check GitHub Actions logs for authentication errors
- Verify repository secrets are configured
- Ensure branch protection rules don't block the workflow

## Pre-release Versions

For testing before a stable release:

```bash
git tag -a v1.2.0-alpha.1 -m "Alpha release for testing"
git push origin v1.2.0-alpha.1
```

Images will be tagged as `1.2.0-alpha.1` automatically.

## Reference

- **Version File:** [../app/__version__.py](../app/__version__.py)
- **Release Workflow:** [../.github/workflows/release.yml](../.github/workflows/release.yml)
- **Semantic Versioning:** https://semver.org/
- **Conventional Commits:** https://www.conventionalcommits.org/
- **GitHub Container Registry:** https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
