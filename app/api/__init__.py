"""API module exports."""

from app.api.image_analysis import router as image_analysis_router

__all__ = ["image_analysis_router"]
