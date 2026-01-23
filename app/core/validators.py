"""Input validation utilities for image processing."""

from fastapi import HTTPException, UploadFile

from app.config import settings


async def validate_image_upload(image: UploadFile) -> bytes:
    """
    Validate uploaded image file.
    
    Args:
        image: The uploaded file
        
    Returns:
        The raw image bytes
        
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if image.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "Unsupported image type",
                "allowed_types": list(settings.ALLOWED_CONTENT_TYPES),
                "received_type": image.content_type
            }
        )
    
    # Read content
    contents = await image.read()
    
    # Check file size
    if len(contents) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail={
                "error": f"Image exceeds maximum allowed size ({max_mb:.0f}MB)",
                "max_size_bytes": settings.MAX_FILE_SIZE,
                "received_size_bytes": len(contents)
            }
        )
    
    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail={"error": "Empty image file"}
        )
    
    return contents


def validate_metrics(metrics: str | None) -> set[str]:
    """
    Validate and parse metrics query parameter.
    
    Args:
        metrics: Comma-separated metrics string
        
    Returns:
        Set of validated metric names
        
    Raises:
        HTTPException: If invalid metrics requested
    """
    valid_metrics = {"brightness", "median", "histogram"}
    
    if metrics is None:
        return {"brightness"}  # Default metric
    
    requested = {m.strip().lower() for m in metrics.split(",") if m.strip()}
    
    invalid = requested - valid_metrics
    if invalid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid metrics requested",
                "invalid_metrics": list(invalid),
                "valid_metrics": list(valid_metrics)
            }
        )
    
    if not requested:
        return {"brightness"}
    
    return requested
