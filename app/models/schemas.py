from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AggregationMethod(str, Enum):
    """Cross-region aggregation methods."""
    MERGE = "merge"
    HIGHEST_SCORE = "highest_score"
    WEIGHTED_AVERAGE = "weighted_average"
    ROUND_ROBIN = "round_robin"

class RecommendationItem(BaseModel):
    """Individual recommendation item."""
    product_id: str
    product_name: Optional[str] = None
    category: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0)
    price: Optional[float] = None
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    image_url: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RecommendationRequest(BaseModel):
    """Request model for recommendations."""
    count: int = Field(default=10, ge=1, le=50)
    categories: Optional[List[str]] = None
    exclude_purchased: bool = True
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    force_refresh: bool = False
    region: Optional[str] = None

class RecommendationResponse(BaseModel):
    """Response model for recommendations."""
    user_id: str
    recommendations: List[RecommendationItem]
    region: str
    generated_at: datetime
    processing_time_ms: float
    total_count: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_count = len(self.recommendations)

class UserRecommendations(BaseModel):
    """User recommendations with metadata."""
    user_id: str
    recommendations: List[RecommendationItem]
    generated_at: datetime
    region: str
    algorithm_used: str = "collaborative_filtering"
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class CrossRegionRequest(BaseModel):
    """Cross-region recommendation request."""
    user_id: str
    regions: Optional[List[str]] = None
    count: int = Field(default=10, ge=1, le=50)
    aggregation_method: AggregationMethod = AggregationMethod.MERGE
    
class RegionStats(BaseModel):
    """Regional statistics model."""
    region: str
    model_stats: Dict[str, Any]
    cache_stats: Dict[str, Any]
    uptime_seconds: float
    last_updated: datetime

class TrendingProduct(BaseModel):
    """Trending product model."""
    product_id: str
    product_name: Optional[str] = None
    category: Optional[str] = None
    trend_score: float = Field(..., ge=0.0)
    interaction_count: int = Field(..., ge=0)
    growth_rate: float = 0.0
    region: str

class SimilarProduct(BaseModel):
    """Similar product model."""
    product_id: str
    product_name: Optional[str] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    category: Optional[str] = None
    shared_features: Optional[List[str]] = None
