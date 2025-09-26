"""
Simple configuration for the recommendation system.
"""

import os
from typing import List, Optional, Dict

class Settings:
    """Application settings."""
    
    # Application settings
    APP_NAME = "Multi-Region E-commerce Recommendation System"
    VERSION = "1.0.0"
    DEBUG = True
    
    # Region configuration
    REGION = os.getenv("REGION", "us-east-1")
    ALLOWED_REGIONS = ["us-east-1", "us-west-1", "eu-west-1", "ap-south-1"]
    
    # MinIO settings
    MINIO_ENDPOINT = "localhost:9000"
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_SECURE = False
    
    # Database settings
    POSTGRES_HOST = "localhost"
    POSTGRES_PORT = 5432
    POSTGRES_DB = "ecommerce_recommendations"
    POSTGRES_USER = "postgres"
    POSTGRES_PASSWORD = "postgres123"
    
    # Redis settings
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    
    # CORS settings
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003"
    ]
    
    # Recommendation settings
    DEFAULT_RECOMMENDATION_COUNT = 10
    MAX_RECOMMENDATION_COUNT = 50
    MIN_USER_INTERACTIONS = 5
    CACHE_TTL = 3600  # 1 hour in seconds
    
    # Cross-region settings
    FAILOVER_ENABLED = True
    REGION_ENDPOINTS = {
        "us-east-1": "http://localhost:8000",
        "us-west-1": "http://localhost:8001", 
        "eu-west-1": "http://localhost:8002",
        "ap-south-1": "http://localhost:8003"
    }
    
    # Model settings
    COLLABORATIVE_FILTERING_COMPONENTS = 50
    SIMILARITY_THRESHOLD = 0.1
    MODEL_UPDATE_INTERVAL = 86400  # 24 hours in seconds
    
    @property
    def database_url(self) -> str:
        """Get database URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def current_region_endpoint(self) -> str:
        """Get current region endpoint."""
        return self.REGION_ENDPOINTS.get(self.REGION, "http://localhost:8000")
    
    def get_region_bucket(self, base_bucket: str) -> str:
        """Get region-specific bucket name."""
        return f"{base_bucket}-{self.REGION.replace('-', '')}"
    
    def get_failover_regions(self) -> List[str]:
        """Get list of failover regions (excluding current)."""
        return [region for region in self.ALLOWED_REGIONS if region != self.REGION]

# Create global settings instance
settings = Settings()
