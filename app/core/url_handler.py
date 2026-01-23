"""URL handling utilities for downloading images from URLs."""

import httpx
from fastapi import HTTPException

from app.config import settings


async def validate_and_download_from_url(url: str, timeout: float = 10.0) -> bytes:
    """
    Download image from URL with validation and size limits.

    Args:
        url: The URL to download the image from
        timeout: Request timeout in seconds (default: 10)

    Returns:
        The raw image bytes

    Raises:
        HTTPException: If download fails or validation fails
    """
    # Basic URL validation
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail={"error": "URL cannot be empty"})

    url = url.strip()

    # Check URL scheme
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid URL scheme",
                "detail": "URL must start with http:// or https://",
            },
        )

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)

            # Check if request was successful
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Failed to download image from URL",
                        "status_code": response.status_code,
                        "url": url,
                    },
                )

            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            # Be flexible with content-type - sometimes it includes charset
            is_valid_type = any(
                allowed_type in content_type for allowed_type in settings.ALLOWED_CONTENT_TYPES
            )

            if not is_valid_type:
                raise HTTPException(
                    status_code=415,
                    detail={
                        "error": "Unsupported image type from URL",
                        "allowed_types": list(settings.ALLOWED_CONTENT_TYPES),
                        "received_type": content_type,
                    },
                )

            # Get content
            contents = response.content

            # Check file size
            if len(contents) > settings.MAX_FILE_SIZE:
                max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                raise HTTPException(
                    status_code=413,
                    detail={
                        "error": f"Image from URL exceeds maximum allowed size ({max_mb:.0f}MB)",
                        "max_size_bytes": settings.MAX_FILE_SIZE,
                        "received_size_bytes": len(contents),
                    },
                )

            if len(contents) == 0:
                raise HTTPException(
                    status_code=400, detail={"error": "Downloaded image file is empty"}
                )

            return contents

    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=408,
            detail={"error": "Request timeout while downloading image", "url": url},
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Failed to download image from URL",
                "detail": str(e),
                "url": url,
            },
        ) from e
