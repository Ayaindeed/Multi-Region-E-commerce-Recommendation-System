#!/usr/bin/env python3
"""
MinIO Setup Script for Multi-Region E-commerce Project
Handles bucket creation, data upload, and MinIO client configuration
"""

import os
import sys
from pathlib import Path
from minio import Minio
from minio.error import S3Error
import pandas as pd
import json
from datetime import datetime
import io

class MinIOManager:
    def __init__(self):
        # MinIO connection settings
        self.minio_client = Minio(
            'localhost:9000',
            access_key='admin',
            secret_key='password123',
            secure=False  # HTTP for local development
        )
        
        # Project paths
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / 'data'
        self.raw_data_dir = self.data_dir / 'raw'
        self.processed_data_dir = self.data_dir / 'processed'
        
        # Bucket configuration
        self.buckets = {
            'raw-data': 'Raw e-commerce datasets from Olist',
            'processed-data': 'Cleaned and transformed datasets',
            'models': 'Machine learning models and artifacts',
            'region-1': 'Data for region 1 (Southeast/South Brazil)',
            'region-2': 'Data for region 2 (Northeast/North/Central-West Brazil)',
            'backups': 'Database backups and snapshots'
        }
        
    def test_connection(self):
        """Test MinIO connection"""
        try:
            # Try to list buckets
            buckets = self.minio_client.list_buckets()
            print("MinIO connection successful!")
            print(f"Found {len(buckets)} existing buckets")
            return True
        except S3Error as e:
            print(f"MinIO connection failed: {e}")
            print("Make sure MinIO is running: docker-compose up -d")
            return False
    
    def create_buckets(self):
        """Create all required MinIO buckets"""
        print("Creating MinIO buckets...")
        
        for bucket_name, description in self.buckets.items():
            try:
                if not self.minio_client.bucket_exists(bucket_name):
                    self.minio_client.make_bucket(bucket_name)
                    print(f"Created bucket: {bucket_name}")
                    
                    # Add bucket metadata
                    tags = {
                        'project': 'multi-region-ecommerce',
                        'description': description,
                        'created': datetime.now().isoformat()
                    }
                    
                    # Note: MinIO doesn't support bucket tagging in the same way as AWS S3
                    # We'll store metadata as a JSON object in each bucket
                    metadata_content = json.dumps(tags, indent=2)
                    self.minio_client.put_object(
                        bucket_name,
                        '_metadata.json',
                        data=io.BytesIO(metadata_content.encode()),
                        length=len(metadata_content.encode())
                    )
                    
                else:
                    print(f"Bucket already exists: {bucket_name}")

            except S3Error as e:
                print(f"Failed to create bucket {bucket_name}: {e}")

        print("Bucket creation complete!")

    def upload_raw_data(self):
        """Upload raw CSV files to MinIO"""
        print("Uploading raw data files...")

        if not self.raw_data_dir.exists():
            print(f"Raw data directory not found: {self.raw_data_dir}")
            return
        
        csv_files = list(self.raw_data_dir.glob('*.csv'))
        
        for csv_file in csv_files:
            try:
                object_name = f"raw/{csv_file.name}"
                self.minio_client.fput_object(
                    'raw-data',
                    object_name,
                    str(csv_file)
                )
                
                file_size = csv_file.stat().st_size / (1024 * 1024)  # MB
                print(f"Uploaded {csv_file.name} ({file_size:.1f} MB)")
                
            except S3Error as e:
                print(f"Failed to upload {csv_file.name}: {e}")
        
        print(f"Uploaded {len(csv_files)} raw data files")
    
    def upload_processed_data(self):
        """Upload processed datasets to MinIO"""
        print("Uploading processed data files...")
        
        if not self.processed_data_dir.exists():
            print(f"Processed data directory not found: {self.processed_data_dir}")
            print("Run the data processing notebook first: notebooks/02_data_processing.ipynb")
            return
        
        # Define file mappings to buckets
        file_mappings = {
            'master_dataset.csv': 'processed-data',
            'completed_orders.csv': 'processed-data', 
            'user_item_matrix.csv': 'processed-data',
            'product_popularity.csv': 'processed-data',
            'region_1_orders.csv': 'region-1',
            'region_2_orders.csv': 'region-2',
            'processing_summary.json': 'processed-data'
        }
        
        uploaded_count = 0
        for filename, bucket in file_mappings.items():
            file_path = self.processed_data_dir / filename
            
            if file_path.exists():
                try:
                    object_name = f"processed/{filename}"
                    self.minio_client.fput_object(bucket, object_name, str(file_path))
                    
                    file_size = file_path.stat().st_size / 1024  # KB
                    print(f"Uploaded {filename} to {bucket} ({file_size:.1f} KB)")
                    uploaded_count += 1
                    
                except S3Error as e:
                    print(f"Failed to upload {filename}: {e}")
            else:
                print(f"File not found: {filename}")
        
        print(f"Uploaded {uploaded_count} processed data files")
    
    def create_sample_model_artifacts(self):
        """Create and upload sample ML model artifacts"""
        print("Creating sample ML model artifacts...")
        
        # Create mock model metadata
        model_metadata = {
            'model_type': 'collaborative_filtering',
            'algorithm': 'matrix_factorization',
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'performance_metrics': {
                'rmse': 0.85,
                'precision_at_5': 0.42,
                'recall_at_5': 0.38
            },
            'training_data': {
                'users': 96000,
                'items': 73,
                'interactions': 112000
            }
        }
        
        try:
            # Upload model metadata
            metadata_content = json.dumps(model_metadata, indent=2)
            self.minio_client.put_object(
                'models',
                'collaborative_filter/v1.0.0/metadata.json',
                data=io.BytesIO(metadata_content.encode()),
                length=len(metadata_content.encode())
            )
            
            print("Uploaded model metadata")
            
            # Create placeholder for model binary (in real scenario, this would be pickled model)
            model_info = "This would contain the actual trained model binary in production"
            self.minio_client.put_object(
                'models',
                'collaborative_filter/v1.0.0/model.pkl',
                data=io.BytesIO(model_info.encode()),
                length=len(model_info.encode())
            )
            
            print("Created model artifact placeholder")
            
        except S3Error as e:
            print(f"Failed to create model artifacts: {e}")
    
    def list_all_objects(self):
        """List all objects in all buckets for verification"""
        print("\\n MinIO Object Inventory:")
        
        total_objects = 0
        total_size = 0
        
        for bucket_name in self.buckets.keys():
            try:
                objects = self.minio_client.list_objects(bucket_name, recursive=True)
                bucket_objects = list(objects)
                
                if bucket_objects:
                    print(f"\\n{bucket_name}:")
                    bucket_size = 0
                    
                    for obj in bucket_objects:
                        size_mb = obj.size / (1024 * 1024)
                        bucket_size += obj.size
                        print(f"   {obj.object_name} ({size_mb:.2f} MB)")
                    
                    total_objects += len(bucket_objects)
                    total_size += bucket_size
                    print(f"   Subtotal: {len(bucket_objects)} objects, {bucket_size/(1024*1024):.2f} MB")
                else:
                    print(f"\\n {bucket_name}: (empty)")
                    
            except S3Error as e:
                print(f" Error listing objects in {bucket_name}: {e}")
        
        print(f"\\n Total: {total_objects} objects, {total_size/(1024*1024):.2f} MB across {len(self.buckets)} buckets")
    
    def setup_bucket_policies(self):
        """Set up bucket access policies (simplified for local development)"""
        print(" Setting up bucket policies...")
        
        # In a real multi-region setup, you'd configure:
        # - Regional access policies
        # - Cross-region replication rules
        # - Lifecycle management policies
        
        # For this demo, we'll create policy documentation
        policies = {
            'raw-data': 'Read-only access for data scientists and analysts',
            'processed-data': 'Read-write for ETL processes, read-only for applications',
            'models': 'Read-write for ML engineers, read-only for prediction services',
            'region-1': 'Primary access for Southeast/South Brazil users',
            'region-2': 'Primary access for Northeast/North/Central-West Brazil users',
            'backups': 'Admin access only, automated backup processes'
        }
        
        policy_doc = {
            'bucket_policies': policies,
            'access_patterns': {
                'data_scientists': ['raw-data:read', 'processed-data:read'],
                'ml_engineers': ['processed-data:read', 'models:read-write'],
                'api_services': ['models:read', 'region-1:read', 'region-2:read'],
                'backup_service': ['backups:read-write']
            },
            'created_at': datetime.now().isoformat()
        }
        
        try:
            policy_content = json.dumps(policy_doc, indent=2)
            self.minio_client.put_object(
                'raw-data',
                '_access_policies.json',
                data=io.BytesIO(policy_content.encode()),
                length=len(policy_content.encode())
            )
            
            print("Access policies documented")
            
        except S3Error as e:
            print(f" Failed to create policy documentation: {e}")

def main():
    """Main setup function"""
    print(" MinIO Setup for Multi-Region E-commerce Project")
    print("=" * 55)
    
    # Initialize MinIO manager
    minio_mgr = MinIOManager()
    
    # Test connection
    if not minio_mgr.test_connection():
        print("\\n Setup failed - MinIO not accessible")
        sys.exit(1)
    
    # Create buckets
    minio_mgr.create_buckets()
    
    # Upload raw data
    minio_mgr.upload_raw_data()
    
    # Upload processed data (if available)
    minio_mgr.upload_processed_data()
    
    # Create model artifacts
    minio_mgr.create_sample_model_artifacts()
    
    # Set up policies
    minio_mgr.setup_bucket_policies()
    
    # Show inventory
    minio_mgr.list_all_objects()
    
if __name__ == "__main__":
    main()
