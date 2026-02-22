[![CI](https://github.com/hossain-khan/image-insights-api/actions/workflows/ci.yml/badge.svg)](https://github.com/hossain-khan/image-insights-api/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://github.com/hossain-khan/image-insights-api/pkgs/container/image-insights-api)
[![GHCR](https://img.shields.io/badge/ghcr.io-image--insights--api-blue?logo=github&logoColor=white)](https://github.com/hossain-khan/image-insights-api/pkgs/container/image-insights-api)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi&logoColor=white)](https://github.com/hossain-khan/image-insights-api/releases)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://github.com/hossain-khan/image-insights-api/releases)

# 🖼️ Image Insights API

A lightweight, containerized REST API that analyzes JPEG and PNG images and returns perceptual brightness metrics using Rec. 709 luminance. Built with FastAPI and Docker for easy deployment anywhere.

## ✨ Features

- **Brightness Analysis**: Perceptual brightness scoring (0-100) using Rec. 709 standard
- **Edge-Based Brightness**: Analyze edges to determine optimal background colors that blend well
- **Median Luminance**: Statistical median for images with extreme highlights/shadows
- **Histogram**: Distribution analysis across 10 luminance buckets
- **Fast & Lightweight**: < 100ms for typical images
- **Portable**: Deploy anywhere Docker runs
- **OpenAPI Documentation**: Auto-generated Swagger UI
- **Privacy-First Design**: Images are never stored; analysis happens in-memory and data is immediately discarded

## 🚀 Quick Start

### Using Pre-built Docker Image (Recommended)

Pull and run the image from GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/hossain-khan/image-insights-api:latest

# Run the container
docker run -p 8080:8080 ghcr.io/hossain-khan/image-insights-api:latest
```

Or use Docker Compose:

```bash
docker compose up -d
```

### Building from Source

```bash
# Build the image locally
docker build -t image-insights-api .

# Run the container
docker run -p 8080:8080 image-insights-api
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 🔐 Privacy & Security

**Your privacy is our priority.** Image Insights API is built with privacy-first design:

- ✅ **Zero Image Storage**: Images are never saved to disk or database
- ✅ **In-Memory Processing Only**: Images are processed in RAM and immediately discarded
- ✅ **Stateless Architecture**: No request tracking, sessions, or user profiles
- ✅ **No Data Retention**: After analysis completes, image data is garbage collected
- ✅ **Safe Logging**: URLs are redacted, no pixel data is logged
- ✅ **No Third-Party Sharing**: All processing is local to your deployment
- ✅ **SSRF Protection**: URL-based analysis blocks private/local network addresses to prevent Server-Side Request Forgery attacks

Each request is independent and isolated. What happens inside stays inside.

## 📖 API Usage

### Endpoints

**Upload-based analysis:**
```
POST /v1/image/analysis
```

**URL-based analysis:**
```
POST /v1/image/analysis/url
```

### Basic Request

```bash
curl -X POST http://localhost:8080/v1/image/analysis \
  -F "image=@photo.jpg"
```

### Response

```json
{
  "brightness_score": 73,
  "average_luminance": 186.3,
  "width": 1920,
  "height": 1080,
  "algorithm": "rec709",
  "processing_time_ms": 45.23
}
```

### URL-Based Image Analysis

Analyze an image directly from a URL:

```bash
curl -X POST http://localhost:8080/v1/image/analysis/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/photo.jpg"}'
```

**Security:** URLs pointing to private/local network addresses are blocked to prevent SSRF attacks.

### Request with All Metrics

```bash
curl -X POST "http://localhost:8080/v1/image/analysis?metrics=brightness,median,histogram" \
  -F "image=@photo.jpg"
```

### Edge-Based Brightness

Analyze image edges to determine background colors that blend well:

```bash
# Analyze left and right edges
curl -X POST "http://localhost:8080/v1/image/analysis?edge_mode=left_right" \
  -F "image=@photo.jpg"

# Analyze top and bottom edges
curl -X POST "http://localhost:8080/v1/image/analysis?edge_mode=top_bottom" \
  -F "image=@photo.jpg"

# Analyze all edges
curl -X POST "http://localhost:8080/v1/image/analysis?edge_mode=all" \
  -F "image=@photo.jpg"
```

**Edge Mode Response:**
```json
{
  "brightness_score": 73,
  "average_luminance": 186.3,
  "edge_brightness_score": 85,
  "edge_average_luminance": 217.4,
  "edge_mode": "left_right",
  "width": 1920,
  "height": 1080,
  "algorithm": "rec709",
  "processing_time_ms": 48.5
}
```

### Full Response

```json
{
  "brightness_score": 73,
  "average_luminance": 186.3,
  "median_luminance": 172.4,
  "histogram": [
    {"range": "0-25", "percent": 2.1},
    {"range": "26-51", "percent": 5.3},
    {"range": "52-76", "percent": 8.7},
    {"range": "77-102", "percent": 12.4},
    {"range": "103-127", "percent": 15.2},
    {"range": "128-153", "percent": 18.6},
    {"range": "154-178", "percent": 14.3},
    {"range": "179-204", "percent": 10.8},
    {"range": "205-229", "percent": 7.1},
    {"range": "230-255", "percent": 5.5}
  ],
  "width": 1920,
  "height": 1080,
  "algorithm": "rec709",
  "processing_time_ms": 52.18
}
```

### Available Metrics

| Metric | Description |
|--------|-------------|
| `brightness` | Brightness score (0-100) and average luminance (default) |
| `median` | Median luminance value |
| `histogram` | Distribution across 10 luminance buckets |

### Edge Modes

| Mode | Description |
|------|-------------|
| `left_right` | Analyze left and right edges (10% of width each) |
| `top_bottom` | Analyze top and bottom edges (10% of height each) |
| `all` | Analyze all four edges (10% from each side) |

Edge mode helps determine background colors that blend well with image edges.

### URL-Based Analysis Examples

Analyze images directly from URLs with full metrics support:

#### Basic URL Request

```bash
curl -X POST http://localhost:8080/v1/image/analysis/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/photo.jpg"}'
```

#### URL Request with All Metrics

```bash
curl -X POST http://localhost:8080/v1/image/analysis/url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/photo.jpg",
    "metrics": "brightness,median,histogram"
  }'
```

#### URL Request with Edge Mode

```bash
curl -X POST http://localhost:8080/v1/image/analysis/url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/photo.jpg",
    "metrics": "brightness,median",
    "edge_mode": "left_right"
  }'
```

**Python Example:**

```python
import requests

url = "http://localhost:8080/v1/image/analysis/url"
payload = {
    "url": "https://example.com/photo.jpg",
    "metrics": "brightness,median,histogram",
    "edge_mode": "all"
}

response = requests.post(url, json=payload)
data = response.json()
print(f"Brightness Score: {data['brightness_score']}")
print(f"Processing Time: {data['processing_time_ms']}ms")
```

**JavaScript/Node.js Example:**

```javascript
const axios = require('axios');

axios.post('http://localhost:8080/v1/image/analysis/url', {
  url: 'https://example.com/photo.jpg',
  metrics: 'brightness,median',
  edge_mode: 'all'
}).then(response => {
  console.log('Brightness Score:', response.data.brightness_score);
  console.log('Processing Time:', response.data.processing_time_ms + 'ms');
});
```

## 📚 API Documentation

Once running, access the interactive documentation:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## 🔬 Algorithm

Uses the **ITU-R BT.709 (Rec. 709)** standard for perceptual luminance:

```
L = 0.2126R + 0.7152G + 0.0722B
```

The brightness score is calculated as:

```
brightness_score = round((average_luminance / 255) * 100)
```

- **0** = Pure black
- **100** = Pure white

## ⚙️ Configuration

### API Constraints

| Setting | Value | Description |
|---------|-------|-------------|
| Max file size | 5MB | Maximum upload size |
| Allowed formats | JPEG, PNG | Supported image types |
| Max dimension | 512px | Images are resized for performance |
| Timeout | 2 seconds | Request processing limit |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DETAILED_LOGGING` | `true` | Enable detailed application logging (request info, processing time, dimensions) |
| `CACHE_ENABLED` | `true` | Enable in-memory LRU+TTL cache for image analysis results |
| `CACHE_MAX_SIZE` | `512` | Maximum number of cached results before LRU eviction |
| `CACHE_TTL_SECONDS` | `86400` | Time-to-live for cache entries in seconds (default: 24 hours) |

**Example:**

```bash
# Disable detailed logging
docker run -p 8080:8080 -e ENABLE_DETAILED_LOGGING=false image-insights-api

# Or with docker-compose
docker compose up -d -e ENABLE_DETAILED_LOGGING=false
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📊 Performance Benchmarks

The API is benchmarked using real sample images to measure performance across different scenarios.

### Quick Benchmark Results

| Image Size | Metrics | Processing Time |
|-----------|---------|-----------------|
| Small (< 50KB) | Brightness only | ~8ms |
| Small (< 50KB) | All metrics + Edge | ~12ms |
| Large (3.2MB) | Brightness only | ~320ms |
| Large (3.2MB) | All metrics + Edge | ~322ms |

See [detailed benchmark results](docs/BENCHMARK.md) for complete analysis.

### Running Benchmarks

```bash
# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Run benchmark (in another terminal)
python scripts/benchmark.py --iterations 10

# Save results to file
python scripts/benchmark.py --output results.md
```

#### Docker Benchmarks

```bash
# Build and run API in Docker
docker build -t image-insights-api .
docker run -d -p 8080:8080 --name api-server image-insights-api

# Run benchmark against Docker container
python scripts/benchmark.py --host http://localhost:8080

# Or run benchmark inside Docker
./scripts/benchmark_docker.sh --inside-container

# Full cycle: build, run, benchmark, cleanup
./scripts/benchmark_docker.sh --build-and-run
```

**Key Performance Characteristics:**
- ✅ Consistent performance (low standard deviation)
- ✅ Fast processing for small images (< 100ms)
- ✅ Efficient large image handling through automatic resizing
- ✅ Minimal overhead for additional metrics (~2-3ms per metric)
- ✅ Edge analysis adds only ~10-20% processing time


## 📁 Project Structure

```
image-insights-api/
├── app/
│   ├── __init__.py
│   ├── __version__.py       # Version management
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── image_analysis.py  # API endpoints
│   │   └── responses.py     # Response models
│   └── core/
│       ├── __init__.py
│       ├── luminance.py     # Brightness calculations
│       ├── resize.py        # Image resizing
│       ├── histogram.py     # Histogram analysis
│       ├── url_handler.py   # URL downloading & SSRF protection
│       └── validators.py    # Input validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_api.py          # API tests
│   └── test_core.py         # Core module tests
├── scripts/
│   ├── benchmark.py         # Performance benchmark script
│   ├── benchmark_docker.sh  # Docker benchmark helper
│   └── export_openapi.py    # OpenAPI spec export
├── docs/
│   ├── API_DOC.md
│   ├── BENCHMARK.md         # Benchmark results
│   ├── PRD.md
│   ├── TECHNICALS.md
│   └── swagger.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 🌐 Deployment

### Cloudflare Containers 🚀 (Recommended for Global Scale)

Deploy to Cloudflare's global network with automatic scaling and zero infrastructure management:

```bash
# Install dependencies
npm install

# Authenticate with Cloudflare
wrangler login

# Deploy to Cloudflare Containers
npm run deploy
```

**Benefits:**
- 🌍 Global distribution across 300+ cities
- 🚀 Automatic scaling (handle spikes with no configuration)
- 💰 Pay only for active instances (~$0.04/vCPU/hour)
- 🔒 Privacy-first: Ephemeral disk aligns with our privacy guarantee
- ⚡ Fast cold starts (2-3 seconds)
- 📊 Built-in monitoring and logs

For detailed Cloudflare setup and deployment instructions, see **[CLOUDFLARE_DEPLOYMENT.md](CLOUDFLARE_DEPLOYMENT.md)**.

After deployment, your API will be available at:
```
https://image-insights-api.<your-account>.workers.dev
```

### Docker Compose (Easiest for Self-Hosted)

The included `docker-compose.yml` is ready for production deployment:

```bash
# Start the service
docker compose up -d

# View logs
docker compose logs -f image-insights-api

# Stop the service
docker compose down

# Update to latest version
docker compose pull && docker compose up -d
```

### Container Platforms

The API is stateless and can be deployed to:

- ☁️ **Cloudflare Containers** (recommended for global scale)
- AWS ECS / Fargate
- Google Cloud Run
- Azure Container Apps
- Kubernetes
- Oracle Cloud Container Instances
- Fly.io
- Any Docker-compatible platform

### Docker Image

Available from GitHub Container Registry:

```bash
docker pull ghcr.io/hossain-khan/image-insights-api:latest
```

**Supported platforms:** `linux/amd64`, `linux/arm64`

### Health Check

```bash
curl http://localhost:8080/health
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
