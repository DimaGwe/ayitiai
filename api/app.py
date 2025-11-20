"""
FastAPI Application for AYITI AI
Main application setup and configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from api.endpoints import router
from core.config_manager import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AYITI AI system...")
    logger.info(f"Supported languages: {settings.supported_languages}")
    logger.info(f"Vector DB path: {settings.vector_db_path}")

    yield

    # Shutdown
    logger.info("Shutting down AYITI AI system...")


# Create FastAPI application
app = FastAPI(
    title="AYITI AI",
    description="Unified LLM System for Haiti - Agriculture, Education, Fishing, Infrastructure, Health, and Governance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AYITI AI",
        "version": "1.0.0",
        "description": "Unified LLM System for Haiti",
        "supported_languages": settings.supported_languages,
        "sectors": [
            "agriculture",
            "education",
            "fishing",
            "infrastructure",
            "health",
            "governance"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AYITI AI"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode
    )
