"""
Image Insights API

A stateless REST microservice that provides fast, deterministic image analysis metrics.
Supports brightness analysis using Rec. 709 perceptual luminance formula.

🔐 Privacy-First Design:
- Images are processed in-memory only
- No storage, no tracking, no data retention
- Each request is completely independent and isolated
- Image data is immediately discarded after analysis
- Only aggregate metrics are returned to users
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.__version__ import __version__
from app.api import image_analysis_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("=" * 80)
    logger.info("🚀 Image Insights API Starting")
    logger.info(f"   Version: {__version__}")
    logger.info(f"   Title: {app.title}")
    logger.info("   Docs: http://localhost:8080/docs")
    logger.info("   Health: http://localhost:8080/health")
    logger.info("   Algorithm: Rec. 709 (ITU-R BT.709) luminance")
    logger.info("=" * 80)
    yield
    # Shutdown
    logger.info("🛑 Image Insights API Shutting Down")


app = FastAPI(
    title="Image Insights API",
    description="""
A lightweight, fast, and portable REST API for image analysis.

## Features

- **Brightness Analysis**: Perceptual brightness scoring using Rec. 709 luminance formula
- **Median Luminance**: Statistical median for images with highlights/shadows
- **Histogram**: Distribution analysis across 10 luminance buckets

## Algorithm

Uses the ITU-R BT.709 (Rec. 709) standard for perceptual luminance:

```
L = 0.2126R + 0.7152G + 0.0722B
```

Brightness scores range from 0 (black) to 100 (white).

## Constraints

- Maximum file size: 5MB
- Supported formats: JPEG, PNG
- Processing timeout: 2 seconds
""",
    version=__version__,
    contact={
        "name": "Image Insights API",
        "url": "https://github.com/hossain-khan/image-insights-api",
        "email": "support@image-insights-api.local",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "health",
            "description": "Health check endpoints to verify API status",
        },
        {
            "name": "image-analysis",
            "description": "Image analysis endpoints for brightness metrics and luminance calculations",
        },
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "details": str(exc)}
    )


# Include routers
app.include_router(image_analysis_router)


@app.get(
    "/",
    tags=["health"],
    summary="Root Health Check",
    response_description="API health status",
    responses={
        200: {
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Healthy API",
                            "value": {
                                "service": "image-insights-api",
                                "version": "1.6.0",
                                "status": "healthy",
                            },
                        }
                    }
                }
            }
        }
    },
)
async def root():
    """Basic health check endpoint to verify API availability."""
    return {"service": "image-insights-api", "version": __version__, "status": "healthy"}


@app.get(
    "/health",
    tags=["health"],
    summary="Detailed Health Check",
    response_description="Detailed API health information",
    responses={
        200: {
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Detailed health status",
                            "value": {
                                "status": "healthy",
                                "service": "image-insights-api",
                                "version": "1.6.0",
                            },
                        }
                    }
                }
            }
        }
    },
)
async def health_check():
    """Detailed health check endpoint with version and service information."""
    return {"status": "healthy", "service": "image-insights-api", "version": __version__}
