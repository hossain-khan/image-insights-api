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


async def validate_and_download_from_url(url: str, timeout: float | None = None) -> bytes:
    """
    Download image from URL with validation and size limits.

    Args:
        url: The URL to download the image from
        timeout: Request timeout in seconds (default: uses settings.REQUEST_TIMEOUT)

    Returns:
        The raw image bytes

    Raises:
        HTTPException: If download fails or validation fails
    """
    # Use settings timeout if not provided
    if timeout is None:
        timeout = settings.REQUEST_TIMEOUT

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
    # 3. Timeout protection (uses settings.REQUEST_TIMEOUT)
    # 4. Size limits (5MB max, enforced via streaming below)
    # 5. Content-type validation (JPEG/PNG only)
    try:
        async with (
            httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client,
            client.stream("GET", url) as response,
        ):
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

            # Check content type - parse media type properly
            content_type = response.headers.get("content-type", "").lower()
            # Extract media type (before semicolon for charset params)
            media_type = content_type.split(";", 1)[0].strip()

            # Normalize allowed types
            allowed_media_types = {
                allowed_type.split(";", 1)[0].strip().lower()
                for allowed_type in settings.ALLOWED_CONTENT_TYPES
            }

            if media_type not in allowed_media_types:
                raise HTTPException(
                    status_code=415,
                    detail={
                        "error": "Unsupported image type from URL",
                        "allowed_types": list(settings.ALLOWED_CONTENT_TYPES),
                        "received_type": content_type,
                    },
                )

            # Pre-check Content-Length header if present
            content_length_header = response.headers.get("content-length")
            if content_length_header is not None:
                try:
                    content_length = int(content_length_header)
                    if content_length > settings.MAX_FILE_SIZE:
                        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                        raise HTTPException(
                            status_code=413,
                            detail={
                                "error": f"Image from URL exceeds maximum allowed size ({max_mb:.0f}MB)",
                                "max_size_bytes": settings.MAX_FILE_SIZE,
                                "received_size_bytes": content_length,
                            },
                        )
                except ValueError:
                    # Invalid Content-Length header, will check during streaming
                    pass

            # Stream content and enforce size limit while downloading
            contents = bytearray()
            async for chunk in response.aiter_bytes(chunk_size=65536):
                contents.extend(chunk)
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

            return bytes(contents)

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
