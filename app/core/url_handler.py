"""URL handling utilities for downloading images from URLs."""

import ipaddress
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from app.config import settings


def _is_private_or_local_url(url: str) -> bool:
    """
    Check if URL points to private/local IP address.

    Args:
        url: The URL to check

    Returns:
        True if URL is private/local, False otherwise
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return True

        # Check for localhost
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return True

        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)
            # Check if it's a private IP
            return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
        except ValueError:
            # Not an IP address, it's a hostname - allow it
            # DNS will resolve to IP, and httpx will handle invalid hostnames
            return False
    except Exception:
        return True


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

    # Check for private/local URLs to prevent SSRF
    if _is_private_or_local_url(url):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid URL",
                "detail": "URLs pointing to private or local network addresses are not allowed",
            },
        )

    # SECURITY NOTE: User-provided URL is used here, which is the intended functionality
    # of this endpoint. SSRF mitigation is implemented via:
    # 1. URL scheme validation (http/https only)
    # 2. Private/local IP blocking (see _is_private_or_local_url)
    # 3. Timeout protection (default 10s)
    # 4. Size limits (5MB max, enforced below)
    # 5. Content-type validation (JPEG/PNG only)
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
