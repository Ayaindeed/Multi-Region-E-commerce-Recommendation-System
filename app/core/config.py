from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "Multi-Region E-commerce Recommendation System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Region configuration
    REGION: str = "us-east-1"
    ALLOWED_REGIONS: List[str] = ["us-east-1", "us-west-1", "eu-west-1", "ap-south-1"]
    
    # MinIO settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    
    # Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ecommerce_recommendations"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres123"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003"
    ]
    
    # Recommendation settings
    DEFAULT_RECOMMENDATION_COUNT: int = 10
    MAX_RECOMMENDATION_COUNT: int = 50
    MIN_USER_INTERACTIONS: int = 5
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # Cross-region settings
    FAILOVER_ENABLED: bool = True
    REGION_ENDPOINTS: dict = {
        "us-east-1": "http://localhost:8000",
        "us-west-1": "http://localhost:8001", 
        "eu-west-1": "http://localhost:8002",
        "ap-south-1": "http://localhost:8003"
    }
    
    # Model settings
    COLLABORATIVE_FILTERING_COMPONENTS: int = 50
    SIMILARITY_THRESHOLD: float = 0.1
    MODEL_UPDATE_INTERVAL: int = 86400  # 24 hours in seconds
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()
