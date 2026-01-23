"""
Image Analysis API

A stateless REST microservice that provides fast, deterministic image analysis metrics.
Supports brightness analysis using Rec. 709 perceptual luminance formula.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import image_analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Image Analysis API",
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
    version="1.0.0",
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


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {"service": "image-analysis-api", "version": "1.0.0", "status": "healthy"}


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check endpoint."""
    return {"status": "healthy", "service": "image-analysis-api", "version": "1.0.0"}
