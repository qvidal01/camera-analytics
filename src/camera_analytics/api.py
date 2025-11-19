"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from camera_analytics.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="Camera Analytics API",
    description="AI-powered security camera analytics",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Camera Analytics API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    """Startup event handler."""
    logger.info("Camera Analytics API starting up")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event handler."""
    logger.info("Camera Analytics API shutting down")
