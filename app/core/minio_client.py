from minio import Minio
from minio.error import S3Error
from typing import Optional
import io
import pickle
import pandas as pd
from datetime import timedelta

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class MinIOClient:
    """MinIO client wrapper with region support."""
    
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.region = settings.REGION
        
    def get_bucket_name(self, base_bucket: str) -> str:
        """Get region-specific bucket name."""
        return settings.get_region_bucket(base_bucket)
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if bucket exists."""
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error as e:
            logger.error(f"Error checking bucket {bucket_name}: {e}")
            return False
    
    def create_bucket(self, bucket_name: str) -> bool:
        """Create bucket if it doesn't exist."""
        try:
            if not self.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
                return True
            return True
        except S3Error as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            return False
    
    def upload_object(self, bucket_name: str, object_name: str, data: bytes, 
                     content_type: str = "application/octet-stream") -> bool:
        """Upload object to bucket."""
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded {object_name} to {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading {object_name} to {bucket_name}: {e}")
            return False
    
    def download_object(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """Download object from bucket."""
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading {object_name} from {bucket_name}: {e}")
            return None
    
    def list_objects(self, bucket_name: str, prefix: str = "") -> list:
        """List objects in bucket."""
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing objects in {bucket_name}: {e}")
            return []
    
    def upload_dataframe(self, bucket_name: str, object_name: str, df: pd.DataFrame) -> bool:
        """Upload pandas DataFrame as CSV to bucket."""
        try:
            csv_data = df.to_csv(index=False).encode('utf-8')
            return self.upload_object(bucket_name, object_name, csv_data, "text/csv")
        except Exception as e:
            logger.error(f"Error uploading DataFrame to {bucket_name}/{object_name}: {e}")
            return False
    
    def download_dataframe(self, bucket_name: str, object_name: str) -> Optional[pd.DataFrame]:
        """Download CSV from bucket as pandas DataFrame."""
        try:
            data = self.download_object(bucket_name, object_name)
            if data:
                return pd.read_csv(io.BytesIO(data))
            return None
        except Exception as e:
            logger.error(f"Error downloading DataFrame from {bucket_name}/{object_name}: {e}")
            return None
    
    def upload_model(self, bucket_name: str, object_name: str, model_obj) -> bool:
        """Upload pickled model to bucket."""
        try:
            model_data = pickle.dumps(model_obj)
            return self.upload_object(bucket_name, object_name, model_data, "application/pickle")
        except Exception as e:
            logger.error(f"Error uploading model to {bucket_name}/{object_name}: {e}")
            return False
    
    def download_model(self, bucket_name: str, object_name: str):
        """Download pickled model from bucket."""
        try:
            data = self.download_object(bucket_name, object_name)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error downloading model from {bucket_name}/{object_name}: {e}")
            return None

# Global MinIO client instance
_minio_client: Optional[MinIOClient] = None

def get_minio_client() -> MinIOClient:
    """Get MinIO client instance."""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client
