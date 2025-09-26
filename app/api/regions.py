from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
import httpx
import asyncio
from datetime import datetime

from app.core.config import settings
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

@router.get("/current")
async def get_current_region():
    """Get current region information."""
    return {
        "region": settings.REGION,
        "endpoint": settings.current_region_endpoint,
        "allowed_regions": settings.ALLOWED_REGIONS,
        "failover_enabled": settings.FAILOVER_ENABLED
    }

@router.get("/all")
async def get_all_regions():
    """Get information about all configured regions."""
    return {
        "current_region": settings.REGION,
        "all_regions": settings.REGION_ENDPOINTS,
        "failover_regions": settings.get_failover_regions()
    }

@router.get("/health")
async def check_regions_health():
    """Check health status of all regions."""
    
    async def check_region_health(region: str, endpoint: str) -> Dict[str, Any]:
        """Check health of a specific region."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = asyncio.get_event_loop().time()
                response = await client.get(f"{endpoint}/api/v1/health/")
                end_time = asyncio.get_event_loop().time()
                
                if response.status_code == 200:
                    return {
                        "region": region,
                        "status": "healthy",
                        "response_time_ms": round((end_time - start_time) * 1000, 2),
                        "endpoint": endpoint
                    }
                else:
                    return {
                        "region": region,
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "endpoint": endpoint
                    }
        except Exception as e:
            return {
                "region": region,
                "status": "unreachable",
                "error": str(e),
                "endpoint": endpoint
            }
    
    # Check all regions concurrently
    tasks = [
        check_region_health(region, endpoint)
        for region, endpoint in settings.REGION_ENDPOINTS.items()
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Calculate overall health
    healthy_count = sum(1 for result in results if result["status"] == "healthy")
    total_count = len(results)
    
    return {
        "timestamp": datetime.utcnow(),
        "overall_health": "healthy" if healthy_count == total_count else "degraded",
        "healthy_regions": healthy_count,
        "total_regions": total_count,
        "regions": results
    }

@router.get("/failover")
async def get_failover_info():
    """Get failover configuration and status."""
    if not settings.FAILOVER_ENABLED:
        return {
            "failover_enabled": False,
            "message": "Failover is disabled in configuration"
        }
    
    return {
        "failover_enabled": True,
        "current_region": settings.REGION,
        "failover_regions": settings.get_failover_regions(),
        "failover_order": settings.get_failover_regions()  # Could be customized
    }

@router.post("/failover/{target_region}")
async def test_failover(target_region: str):
    """Test failover to a specific region (for testing purposes)."""
    
    if target_region not in settings.ALLOWED_REGIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target region. Allowed regions: {settings.ALLOWED_REGIONS}"
        )
    
    if target_region == settings.REGION:
        raise HTTPException(
            status_code=400,
            detail="Cannot failover to the same region"
        )
    
    target_endpoint = settings.REGION_ENDPOINTS.get(target_region)
    if not target_endpoint:
        raise HTTPException(
            status_code=400,
            detail=f"No endpoint configured for region {target_region}"
        )
    
    # Test connectivity to target region
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_endpoint}/api/v1/health/")
            
            if response.status_code == 200:
                return {
                    "message": f"Failover test to {target_region} successful",
                    "source_region": settings.REGION,
                    "target_region": target_region,
                    "target_endpoint": target_endpoint,
                    "target_status": "healthy",
                    "timestamp": datetime.utcnow()
                }
            else:
                return {
                    "message": f"Failover test to {target_region} failed",
                    "source_region": settings.REGION,
                    "target_region": target_region,
                    "target_endpoint": target_endpoint,
                    "target_status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.utcnow()
                }
                
    except Exception as e:
        logger.error(f"Failover test to {target_region} failed: {str(e)}")
        return {
            "message": f"Failover test to {target_region} failed",
            "source_region": settings.REGION,
            "target_region": target_region,
            "target_endpoint": target_endpoint,
            "target_status": "unreachable",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/latency")
async def measure_cross_region_latency():
    """Measure latency to all other regions."""
    
    async def measure_latency(region: str, endpoint: str) -> Dict[str, Any]:
        """Measure latency to a specific region."""
        if region == settings.REGION:
            return {
                "region": region,
                "latency_ms": 0,
                "status": "local"
            }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = asyncio.get_event_loop().time()
                response = await client.get(f"{endpoint}/api/v1/health/")
                end_time = asyncio.get_event_loop().time()
                
                latency_ms = round((end_time - start_time) * 1000, 2)
                
                return {
                    "region": region,
                    "latency_ms": latency_ms,
                    "status": "reachable" if response.status_code == 200 else "error"
                }
        except Exception as e:
            return {
                "region": region,
                "latency_ms": None,
                "status": "unreachable",
                "error": str(e)
            }
    
    # Measure latency to all regions
    tasks = [
        measure_latency(region, endpoint)
        for region, endpoint in settings.REGION_ENDPOINTS.items()
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Calculate statistics
    latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None and r["latency_ms"] > 0]
    
    stats = {}
    if latencies:
        stats = {
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2)
        }
    
    return {
        "source_region": settings.REGION,
        "timestamp": datetime.utcnow(),
        "latency_results": results,
        "statistics": stats
    }
