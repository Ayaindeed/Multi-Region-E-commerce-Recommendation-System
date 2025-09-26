#!/usr/bin/env python3
"""
Test script for Multi-Region E-commerce Recommendation System
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

# Test configuration
REGIONS = {
    "us-east-1": "http://localhost:8000",
    "us-west-1": "http://localhost:8001", 
    "eu-west-1": "http://localhost:8002",
    "ap-south-1": "http://localhost:8003"
}

TEST_USER_ID = "00012a2ce6f8dcda20c5a5eb29c6b8e3"  # From our processed data

class RecommendationSystemTester:
    """Test suite for the recommendation system."""
    
    def __init__(self):
        self.results = {}
    
    async def test_health_endpoints(self):
        """Test health endpoints for all regions."""
        print("🏥 Testing health endpoints...")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for region, endpoint in REGIONS.items():
                try:
                    start_time = time.time()
                    response = await client.get(f"{endpoint}/api/v1/health/")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"  ✅ {region}: {data['status']} ({(end_time-start_time)*1000:.1f}ms)")
                        self.results[f"health_{region}"] = "PASS"
                    else:
                        print(f"  ❌ {region}: HTTP {response.status_code}")
                        self.results[f"health_{region}"] = "FAIL"
                        
                except Exception as e:
                    print(f"  ❌ {region}: {str(e)}")
                    self.results[f"health_{region}"] = "ERROR"
    
    async def test_detailed_health(self):
        """Test detailed health endpoint."""
        print("\n🔍 Testing detailed health...")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(f"{REGIONS['us-east-1']}/api/v1/health/detailed")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Overall status: {data['status']}")
                    
                    for service, info in data.get('services', {}).items():
                        status = info.get('status', 'unknown')
                        print(f"    - {service}: {status}")
                    
                    self.results["detailed_health"] = "PASS"
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results["detailed_health"] = "FAIL"
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results["detailed_health"] = "ERROR"
    
    async def test_recommendation_endpoint(self):
        """Test user recommendation endpoint."""
        print(f"\n🎯 Testing recommendations for user {TEST_USER_ID}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for region, endpoint in REGIONS.items():
                try:
                    payload = {
                        "count": 5,
                        "exclude_purchased": True
                    }
                    
                    start_time = time.time()
                    response = await client.post(
                        f"{endpoint}/api/v1/recommendations/user/{TEST_USER_ID}",
                        json=payload
                    )
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        data = response.json()
                        rec_count = len(data.get('recommendations', []))
                        processing_time = data.get('processing_time_ms', 0)
                        
                        print(f"  ✅ {region}: {rec_count} recommendations ({processing_time:.1f}ms)")
                        self.results[f"recommendations_{region}"] = "PASS"
                        
                        # Show first recommendation
                        if data.get('recommendations'):
                            first_rec = data['recommendations'][0]
                            print(f"    - Top: {first_rec.get('product_id')} (score: {first_rec.get('score', 0):.3f})")
                    
                    elif response.status_code == 404:
                        print(f"  ⚠️  {region}: User not found (expected for some regions)")
                        self.results[f"recommendations_{region}"] = "SKIP"
                    
                    else:
                        print(f"  ❌ {region}: HTTP {response.status_code}")
                        self.results[f"recommendations_{region}"] = "FAIL"
                        
                except Exception as e:
                    print(f"  ❌ {region}: {str(e)}")
                    self.results[f"recommendations_{region}"] = "ERROR"
    
    async def test_similar_products(self):
        """Test similar products endpoint."""
        print("\n🔗 Testing similar products...")
        
        # Use a product ID from our data
        test_product_id = "aca2eb7d00ea1a7b8ebd4e68314663af"  # Known product from data
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{REGIONS['us-east-1']}/api/v1/recommendations/similar-products/{test_product_id}",
                    params={"count": 5}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    similar_count = len(data.get('similar_products', []))
                    print(f"  ✅ Found {similar_count} similar products")
                    self.results["similar_products"] = "PASS"
                    
                    # Show first similar product
                    if data.get('similar_products'):
                        first_similar = data['similar_products'][0]
                        print(f"    - Top: {first_similar.get('product_id')} (similarity: {first_similar.get('similarity_score', 0):.3f})")
                
                elif response.status_code == 404:
                    print(f"  ⚠️  Product not found (expected if product not in training data)")
                    self.results["similar_products"] = "SKIP"
                
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results["similar_products"] = "FAIL"
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results["similar_products"] = "ERROR"
    
    async def test_trending_products(self):
        """Test trending products endpoint."""
        print("\n🔥 Testing trending products...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{REGIONS['us-east-1']}/api/v1/recommendations/trending",
                    params={"count": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    trending_count = len(data.get('trending_products', []))
                    print(f"  ✅ Found {trending_count} trending products")
                    self.results["trending_products"] = "PASS"
                    
                    # Show top trending product
                    if data.get('trending_products'):
                        top_trending = data['trending_products'][0]
                        print(f"    - Top: {top_trending.get('product_id')} (trend score: {top_trending.get('trend_score', 0):.3f})")
                
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results["trending_products"] = "FAIL"
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results["trending_products"] = "ERROR"
    
    async def test_stats_endpoint(self):
        """Test recommendation stats endpoint."""
        print("\n📊 Testing stats endpoint...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{REGIONS['us-east-1']}/api/v1/recommendations/stats")
                
                if response.status_code == 200:
                    data = response.json()
                    model_stats = data.get('model_stats', {})
                    
                    print(f"  ✅ Stats retrieved")
                    print(f"    - Models loaded: {model_stats.get('models_loaded', False)}")
                    print(f"    - User count: {model_stats.get('user_count', 'N/A')}")
                    print(f"    - Product count: {model_stats.get('product_count', 'N/A')}")
                    print(f"    - Matrix density: {model_stats.get('matrix_density', 0):.4f}")
                    
                    self.results["stats"] = "PASS"
                
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results["stats"] = "FAIL"
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results["stats"] = "ERROR"
    
    async def test_region_endpoints(self):
        """Test region-specific endpoints."""
        print("\n🌍 Testing region endpoints...")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Test current region
                response = await client.get(f"{REGIONS['us-east-1']}/api/v1/regions/current")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Current region: {data.get('region')}")
                    print(f"    - Failover enabled: {data.get('failover_enabled')}")
                    self.results["region_current"] = "PASS"
                
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results["region_current"] = "FAIL"
                
                # Test regions health
                response = await client.get(f"{REGIONS['us-east-1']}/api/v1/regions/health")
                
                if response.status_code == 200:
                    data = response.json()
                    overall_health = data.get('overall_health')
                    healthy_regions = data.get('healthy_regions', 0)
                    total_regions = data.get('total_regions', 0)
                    
                    print(f"  ✅ Multi-region health: {overall_health}")
                    print(f"    - Healthy regions: {healthy_regions}/{total_regions}")
                    self.results["region_health"] = "PASS"
                
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results["region_health"] = "FAIL"
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results["region_current"] = "ERROR"
                self.results["region_health"] = "ERROR"
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.results.values() if result == "PASS")
        failed = sum(1 for result in self.results.values() if result == "FAIL")
        errors = sum(1 for result in self.results.values() if result == "ERROR")
        skipped = sum(1 for result in self.results.values() if result == "SKIP")
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🚨 Errors: {errors}")
        print(f"⏭️  Skipped: {skipped}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if failed > 0 or errors > 0:
            print("\n❌ Failed/Error Tests:")
            for test_name, result in self.results.items():
                if result in ["FAIL", "ERROR"]:
                    print(f"  - {test_name}: {result}")
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 Multi-Region E-commerce Recommendation System Test Suite")
        print("="*60)
        
        # Basic connectivity
        await self.test_health_endpoints()
        await self.test_detailed_health()
        
        # Core functionality
        await self.test_recommendation_endpoint()
        await self.test_similar_products()
        await self.test_trending_products()
        await self.test_stats_endpoint()
        
        # Multi-region features
        await self.test_region_endpoints()
        
        # Print summary
        self.print_summary()

async def main():
    """Main test function."""
    tester = RecommendationSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
