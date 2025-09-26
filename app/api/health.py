from fastapi import APIRouter, Depends
from datetime import datetime
import time
import psutil
import os

from app.core.config import settings
from app.core.database import get_database, get_redis
from app.core.minio_client import get_minio_client
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "region": settings.REGION,
        "timestamp": datetime.utcnow(),
        "version": settings.VERSION
    }

@router.get("/detailed")
async def detailed_health_check(
    db = Depends(get_database),
    redis_client = Depends(get_redis),
    minio_client = Depends(get_minio_client)
):
    """Detailed health check with dependency status."""
    
    health_status = {
        "status": "healthy",
        "region": settings.REGION,
        "timestamp": datetime.utcnow(),
        "version": settings.VERSION,
        "services": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = {
            "status": "healthy",
            "url": settings.database_url.split('@')[-1]  # Hide credentials
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        redis_info = redis_client.info()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "version": redis_info.get("redis_version"),
            "memory_usage": redis_info.get("used_memory_human")
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check MinIO
    try:
        # Try to list buckets as a connectivity test
        buckets = minio_client.client.list_buckets()
        health_status["services"]["minio"] = {
            "status": "healthy",
            "endpoint": settings.MINIO_ENDPOINT,
            "buckets_count": len(buckets)
        }
    except Exception as e:
        health_status["services"]["minio"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/system")
async def system_health():
    """System resource health check."""
    
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process info
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            "status": "healthy",
            "region": settings.REGION,
            "timestamp": datetime.utcnow(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "process": {
                "pid": os.getpid(),
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "create_time": datetime.fromtimestamp(process.create_time())
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return {
            "status": "error",
            "region": settings.REGION,
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }
