#!/usr/bin/env python3
"""
Multi-Region System Status and Testing
"""

import asyncio
import httpx
import json
from datetime import datetime

# Region configuration
REGIONS = {
    "8000": {"name": "us-west-1", "flag": "🌴"},
    "8001": {"name": "us-east-1", "flag": "🗽"},
    "8002": {"name": "eu-west-1", "flag": "🇪🇺"},
    "8003": {"name": "ap-south-1", "flag": "🌏"}
}

async def test_region(port, region_info):
    """Test a specific region"""
    region_name = region_info["name"]
    flag = region_info["flag"]
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Test root endpoint
            start_time = asyncio.get_event_loop().time()
            response = await client.get(f"http://localhost:{port}")
            end_time = asyncio.get_event_loop().time()
            
            if response.status_code == 200:
                data = response.json()
                latency = round((end_time - start_time) * 1000, 1)
                
                print(f"✅ {flag} Port {port} ({region_name}): {data['status']} ({latency}ms)")
                return {
                    "port": port,
                    "region": region_name,
                    "status": "healthy",
                    "latency_ms": latency,
                    "data": data
                }
            else:
                print(f"❌ {flag} Port {port} ({region_name}): HTTP {response.status_code}")
                return {"port": port, "region": region_name, "status": "error"}
                
    except Exception as e:
        print(f"🔴 {flag} Port {port} ({region_name}): Not running")
        return {"port": port, "region": region_name, "status": "offline", "error": str(e)}

async def test_all_regions():
    """Test all regions concurrently"""
    print("🌍 Multi-Region E-commerce Recommendation System Status")
    print("=" * 60)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test all regions
    tasks = [test_region(port, info) for port, info in REGIONS.items()]
    results = await asyncio.gather(*tasks)
    
    # Summary
    healthy = [r for r in results if r["status"] == "healthy"]
    offline = [r for r in results if r["status"] == "offline"]
    
    print()
    print("📊 Summary:")
    print(f"✅ Active Regions: {len(healthy)}/4")
    print(f"🔴 Offline Regions: {len(offline)}")
    
    if healthy:
        avg_latency = sum(r["latency_ms"] for r in healthy) / len(healthy)
        print(f"⚡ Average Latency: {avg_latency:.1f}ms")
        
        print("\n🌐 Access URLs:")
        for result in healthy:
            port = result["port"]
            region = result["region"]
            flag = REGIONS[port]["flag"]
            print(f"  {flag} {region}: http://localhost:{port}")
            print(f"     📖 API Docs: http://localhost:{port}/docs")
            print(f"     ❤️ Health: http://localhost:{port}/api/v1/health/")
            print()

async def test_cross_region_features():
    """Test cross-region communication"""
    print("🔄 Testing Cross-Region Features")
    print("-" * 40)
    
    # Find an active region to test from
    active_regions = []
    for port in REGIONS.keys():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"http://localhost:{port}/api/v1/regions/current")
                if response.status_code == 200:
                    active_regions.append(port)
        except:
            continue
    
    if active_regions:
        test_port = active_regions[0]
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"http://localhost:{test_port}/api/v1/regions/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Multi-region health check successful")
                    print(f"📊 Healthy regions: {data.get('healthy_regions', 0)}/{data.get('total_regions', 0)}")
                else:
                    print(f"❌ Cross-region test failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Cross-region test error: {e}")
    else:
        print("❌ No active regions found for cross-region testing")

async def main():
    """Main test function"""
    await test_all_regions()
    print()
    await test_cross_region_features()
    
    print("\n" + "=" * 60)
    print("🎯 Your Multi-Region System is Ready!")
    print("Visit the API documentation at any active region's /docs endpoint")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
