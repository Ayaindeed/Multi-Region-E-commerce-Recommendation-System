from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager
import asyncio

from app.core.simple_config import settings
from app.core.database import get_database, get_redis
from app.core.minio_client import get_minio_client
from app.api import recommendations, health, regions
from app.models.recommendation import RecommendationEngine
from app.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Global recommendation engine instance
recommendation_engine: RecommendationEngine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(f"Starting FastAPI application in {settings.REGION} region")
    
    global recommendation_engine
    try:
        # Initialize services
        minio_client = get_minio_client()
        db = next(get_database())
        redis = get_redis()
        
        # Initialize recommendation engine
        recommendation_engine = RecommendationEngine(
            minio_client=minio_client,
            region=settings.REGION
        )
        
        # Load models in background
        asyncio.create_task(recommendation_engine.load_models())
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application")

# Create FastAPI app
app = FastAPI(
    title="Multi-Region E-commerce Recommendation System",
    description="Enterprise-grade recommendation system with multi-region support using MinIO",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    recommendations.router,
    prefix="/api/v1/recommendations",
    tags=["recommendations"]
)

app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["health"]
)

app.include_router(
    regions.router,
    prefix="/api/v1/regions",
    tags=["regions"]
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Multi-Region E-commerce Recommendation System",
        "region": settings.REGION,
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Contact administrator"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "region": settings.REGION}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "region": settings.REGION
        }
    )

def get_recommendation_engine() -> RecommendationEngine:
    """Dependency to get recommendation engine instance."""
    if recommendation_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendation engine not initialized"
        )
    return recommendation_engine

if __name__ == "__main__":
    # Determine port based on region for multi-region simulation
    port_map = {
        "us-east-1": 8000,
        "us-west-1": 8001,
        "eu-west-1": 8002,
        "ap-south-1": 8003
    }
    
    port = port_map.get(settings.REGION, 8000)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info"
    )
