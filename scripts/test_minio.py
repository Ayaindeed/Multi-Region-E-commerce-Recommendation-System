#!/usr/bin/env python3
"""
Test MinIO connection and basic operations
"""

from minio import Minio
from minio.error import S3Error
import io
import json
from datetime import datetime

def test_minio_connection():
    """Test basic MinIO operations"""
    print("Testing MinIO Connection and Operations")
    print("=" * 45)
    
    try:
        # Initialize client
        client = Minio(
            'localhost:9000',
            access_key='admin', 
            secret_key='password123',
            secure=False
        )
        
        print(" MinIO client initialized")
        
        # Test 1: List buckets
        buckets = client.list_buckets()
        print(f" Found {len(buckets)} buckets:")
        for bucket in buckets:
            print(f"   🪣 {bucket.name} (created: {bucket.creation_date})")
        
        # Test 2: Create test object
        test_data = {
            'test': 'MinIO connection test',
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        test_content = json.dumps(test_data, indent=2)
        client.put_object(
            'raw-data',
            'test/connection_test.json',
            data=io.BytesIO(test_content.encode()),
            length=len(test_content.encode())
        )
        print(" Test object uploaded successfully")
        
        # Test 3: Read test object
        response = client.get_object('raw-data', 'test/connection_test.json')
        data = response.read().decode()
        print(" Test object downloaded successfully")
        print(f"   Content: {json.loads(data)['test']}")
        
        # Test 4: List objects in bucket
        objects = list(client.list_objects('raw-data', prefix='test/'))
        print(f" Found {len(objects)} test objects")
        
        # Clean up test object
        client.remove_object('raw-data', 'test/connection_test.json')
        print(" Test object cleaned up")
        
        return True
        
    except S3Error as e:
        print(f" MinIO test failed: {e}")
        return False
    except Exception as e:
        print(f" Unexpected error: {e}")
        return False

def main():
    """Main test function"""
    success = test_minio_connection()
    
    if success:
        print("\n All MinIO tests passed!")
        print(" MinIO is ready for the multi-region e-commerce project")
    else:
        print("\n MinIO tests failed!")

if __name__ == "__main__":
    main()
