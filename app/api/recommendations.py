from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import time
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_redis
from app.models.recommendation import RecommendationEngine, RecommendationRequest, RecommendationResponse
from app.models.schemas import UserRecommendations, CrossRegionRequest, RegionStats
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

def get_recommendation_engine() -> RecommendationEngine:
    """Dependency to get recommendation engine."""
    from app.main import recommendation_engine
    if recommendation_engine is None:
        raise HTTPException(status_code=503, detail="Recommendation engine not initialized")
    return recommendation_engine

@router.post("/user/{user_id}", response_model=RecommendationResponse)
async def get_user_recommendations(
    user_id: str,
    request: RecommendationRequest,
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    redis_client = Depends(get_redis)
) -> RecommendationResponse:
    """Get personalized recommendations for a user."""
    
    start_time = time.time()
    
    try:
        # Check cache first
        cache_key = f"recommendations:{user_id}:{request.count}:{request.region or 'default'}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result and not request.force_refresh:
            logger.info(f"Cache hit for user {user_id}")
            return RecommendationResponse.parse_raw(cached_result)
        
        # Generate recommendations
        recommendations = await engine.get_user_recommendations(
            user_id=user_id,
            count=request.count,
            exclude_purchased=request.exclude_purchased,
            min_rating=request.min_rating,
            categories=request.categories
        )
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for user {user_id}"
            )
        
        # Create response
        response = RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations,
            region=settings.REGION,
            generated_at=datetime.utcnow(),
            processing_time_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        # Cache result
        redis_client.setex(
            cache_key,
            settings.CACHE_TTL,
            response.json()
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating recommendations for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/similar-products/{product_id}")
async def get_similar_products(
    product_id: str,
    count: int = Query(default=10, ge=1, le=50),
    engine: RecommendationEngine = Depends(get_recommendation_engine)
):
    """Get similar products based on product ID."""
    
    try:
        similar_products = await engine.get_similar_products(
            product_id=product_id,
            count=count
        )
        
        if not similar_products:
            raise HTTPException(
                status_code=404,
                detail=f"No similar products found for product {product_id}"
            )
        
        return {
            "product_id": product_id,
            "similar_products": similar_products,
            "region": settings.REGION,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error finding similar products for {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/trending")
async def get_trending_products(
    count: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    time_window_hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    engine: RecommendationEngine = Depends(get_recommendation_engine)
):
    """Get trending products in the region."""
    
    try:
        trending_products = await engine.get_trending_products(
            count=count,
            category=category,
            time_window_hours=time_window_hours
        )
        
        return {
            "trending_products": trending_products,
            "category": category,
            "time_window_hours": time_window_hours,
            "region": settings.REGION,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting trending products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/cross-region")
async def get_cross_region_recommendations(
    request: CrossRegionRequest,
    engine: RecommendationEngine = Depends(get_recommendation_engine)
):
    """Get recommendations by querying multiple regions."""
    
    try:
        cross_region_results = await engine.get_cross_region_recommendations(
            user_id=request.user_id,
            regions=request.regions or settings.ALLOWED_REGIONS,
            count=request.count,
            aggregation_method=request.aggregation_method
        )
        
        return {
            "user_id": request.user_id,
            "cross_region_results": cross_region_results,
            "aggregation_method": request.aggregation_method,
            "primary_region": settings.REGION,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting cross-region recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/stats")
async def get_recommendation_stats(
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    redis_client = Depends(get_redis)
):
    """Get recommendation system statistics."""
    
    try:
        # Get basic stats from engine
        model_stats = await engine.get_model_stats()
        
        # Get cache stats
        cache_info = redis_client.info('memory')
        cache_stats = {
            "memory_used": cache_info.get('used_memory_human'),
            "keys_count": redis_client.dbsize(),
            "cache_hits": redis_client.info('stats').get('keyspace_hits', 0),
            "cache_misses": redis_client.info('stats').get('keyspace_misses', 0)
        }
        
        return RegionStats(
            region=settings.REGION,
            model_stats=model_stats,
            cache_stats=cache_stats,
            uptime_seconds=time.time() - engine.startup_time if hasattr(engine, 'startup_time') else 0,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting recommendation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/refresh-models")
async def refresh_models(
    background_tasks: BackgroundTasks,
    engine: RecommendationEngine = Depends(get_recommendation_engine)
):
    """Refresh recommendation models (admin endpoint)."""
    
    try:
        # Add model refresh task to background
        background_tasks.add_task(engine.refresh_models)
        
        return {
            "message": "Model refresh initiated",
            "region": settings.REGION,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error initiating model refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/clear-cache")
async def clear_recommendation_cache(
    pattern: str = Query(default="recommendations:*"),
    redis_client = Depends(get_redis)
):
    """Clear recommendation cache (admin endpoint)."""
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted_count = redis_client.delete(*keys)
            logger.info(f"Cleared {deleted_count} cache entries with pattern: {pattern}")
            return {
                "message": f"Cleared {deleted_count} cache entries",
                "pattern": pattern,
                "region": settings.REGION,
                "timestamp": datetime.utcnow()
            }
        else:
            return {
                "message": "No cache entries found to clear",
                "pattern": pattern,
                "region": settings.REGION,
                "timestamp": datetime.utcnow()
            }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
