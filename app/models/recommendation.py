import asyncio
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pickle
import time
import httpx

from app.core.config import settings
from app.core.minio_client import MinIOClient
from app.models.schemas import (
    RecommendationItem, RecommendationRequest, RecommendationResponse,
    TrendingProduct, SimilarProduct, AggregationMethod
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class RecommendationEngine:
    """Main recommendation engine with multi-region support."""
    
    def __init__(self, minio_client: MinIOClient, region: str):
        self.minio_client = minio_client
        self.region = region
        self.startup_time = time.time()
        
        # Model storage
        self.user_item_matrix = None
        self.svd_model = None
        self.user_similarities = None
        self.item_similarities = None
        self.product_features = None
        self.trending_products = None
        
        # Buckets
        self.processed_bucket = f"processed-{region.replace('-', '')}"
        self.models_bucket = f"models-{region.replace('-', '')}"
        
        # Model state
        self.models_loaded = False
        self.last_model_update = None
        
    async def load_models(self):
        """Load or create recommendation models."""
        try:
            logger.info("Loading recommendation models...")
            
            # Load processed data
            await self._load_processed_data()
            
            # Try to load existing models
            if await self._load_existing_models():
                logger.info("Loaded existing models from MinIO")
            else:
                # Train new models if none exist
                logger.info("Training new models...")
                await self._train_models()
                await self._save_models()
            
            self.models_loaded = True
            self.last_model_update = datetime.utcnow()
            logger.info("Model loading completed successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise
    
    async def _load_processed_data(self):
        """Load processed data from MinIO."""
        try:
            # Load user-item matrix
            user_item_data = self.minio_client.download_dataframe(
                self.processed_bucket, 
                "user_item_matrix.csv"
            )
            if user_item_data is not None:
                self.user_item_matrix = user_item_data.set_index('user_id')
                logger.info(f"Loaded user-item matrix: {self.user_item_matrix.shape}")
            
            # Load product features
            products_data = self.minio_client.download_dataframe(
                self.processed_bucket,
                "products_with_features.csv"
            )
            if products_data is not None:
                self.product_features = products_data.set_index('product_id')
                logger.info(f"Loaded product features: {self.product_features.shape}")
            
        except Exception as e:
            logger.error(f"Error loading processed data: {str(e)}")
            raise
    
    async def _load_existing_models(self) -> bool:
        """Try to load existing models from MinIO."""
        try:
            # Check if models bucket exists
            if not self.minio_client.bucket_exists(self.models_bucket):
                return False
            
            # Load SVD model
            svd_data = self.minio_client.download_model(self.models_bucket, "svd_model.pkl")
            if svd_data:
                self.svd_model = svd_data
                logger.info("Loaded SVD model")
            
            # Load similarities
            user_sim_data = self.minio_client.download_model(self.models_bucket, "user_similarities.pkl")
            if user_sim_data:
                self.user_similarities = user_sim_data
                logger.info("Loaded user similarities")
            
            item_sim_data = self.minio_client.download_model(self.models_bucket, "item_similarities.pkl")
            if item_sim_data:
                self.item_similarities = item_sim_data
                logger.info("Loaded item similarities")
            
            return all([self.svd_model is not None, 
                       self.user_similarities is not None, 
                       self.item_similarities is not None])
            
        except Exception as e:
            logger.error(f"Error loading existing models: {str(e)}")
            return False
    
    async def _train_models(self):
        """Train recommendation models."""
        if self.user_item_matrix is None:
            raise ValueError("User-item matrix not loaded")
        
        try:
            # Train SVD model for collaborative filtering
            logger.info("Training SVD model...")
            self.svd_model = TruncatedSVD(
                n_components=settings.COLLABORATIVE_FILTERING_COMPONENTS,
                random_state=42
            )
            
            # Fit SVD on user-item matrix
            user_item_dense = self.user_item_matrix.fillna(0).values
            self.svd_model.fit(user_item_dense)
            
            # Compute user similarities
            logger.info("Computing user similarities...")
            user_features = self.svd_model.transform(user_item_dense)
            self.user_similarities = cosine_similarity(user_features)
            
            # Compute item similarities
            logger.info("Computing item similarities...")
            item_features = self.svd_model.components_.T
            self.item_similarities = cosine_similarity(item_features)
            
            logger.info("Model training completed")
            
        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            raise
    
    async def _save_models(self):
        """Save models to MinIO."""
        try:
            # Create models bucket if not exists
            if not self.minio_client.bucket_exists(self.models_bucket):
                self.minio_client.create_bucket(self.models_bucket)
            
            # Save SVD model
            if self.svd_model:
                self.minio_client.upload_model(self.models_bucket, "svd_model.pkl", self.svd_model)
                logger.info("Saved SVD model")
            
            # Save similarities
            if self.user_similarities is not None:
                self.minio_client.upload_model(self.models_bucket, "user_similarities.pkl", self.user_similarities)
                logger.info("Saved user similarities")
            
            if self.item_similarities is not None:
                self.minio_client.upload_model(self.models_bucket, "item_similarities.pkl", self.item_similarities)
                logger.info("Saved item similarities")
                
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
            raise
    
    async def get_user_recommendations(
        self,
        user_id: str,
        count: int = 10,
        exclude_purchased: bool = True,
        min_rating: Optional[float] = None,
        categories: Optional[List[str]] = None
    ) -> List[RecommendationItem]:
        """Get personalized recommendations for a user."""
        
        if not self.models_loaded:
            raise ValueError("Models not loaded")
        
        try:
            # Check if user exists in matrix
            if user_id not in self.user_item_matrix.index:
                # Return popular/trending items for new users
                return await self._get_popular_recommendations(count, categories, min_rating)
            
            # Get user index
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            
            # Get user similarities
            user_sim_scores = self.user_similarities[user_idx]
            similar_users = np.argsort(user_sim_scores)[::-1][1:21]  # Top 20 similar users
            
            # Get recommendations based on similar users
            recommendations = []
            user_purchased = set(self.user_item_matrix.loc[user_id].dropna().index) if exclude_purchased else set()
            
            # Aggregate scores from similar users
            product_scores = {}
            for sim_user_idx in similar_users:
                sim_user_id = self.user_item_matrix.index[sim_user_idx]
                sim_score = user_sim_scores[sim_user_idx]
                
                if sim_score < settings.SIMILARITY_THRESHOLD:
                    break
                
                # Get this user's purchases/ratings
                user_ratings = self.user_item_matrix.loc[sim_user_id].dropna()
                for product_id, rating in user_ratings.items():
                    if product_id not in user_purchased:
                        if product_id not in product_scores:
                            product_scores[product_id] = 0
                        product_scores[product_id] += sim_score * rating
            
            # Sort by score and create recommendation items
            sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
            
            for product_id, score in sorted_products[:count]:
                rec_item = await self._create_recommendation_item(
                    product_id, score, categories, min_rating
                )
                if rec_item:
                    recommendations.append(rec_item)
            
            # Fill remaining slots with popular items if needed
            if len(recommendations) < count:
                popular_recs = await self._get_popular_recommendations(
                    count - len(recommendations), categories, min_rating
                )
                existing_ids = {rec.product_id for rec in recommendations}
                for rec in popular_recs:
                    if rec.product_id not in existing_ids:
                        recommendations.append(rec)
            
            return recommendations[:count]
            
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            # Fallback to popular recommendations
            return await self._get_popular_recommendations(count, categories, min_rating)
    
    async def _get_popular_recommendations(
        self, 
        count: int, 
        categories: Optional[List[str]] = None,
        min_rating: Optional[float] = None
    ) -> List[RecommendationItem]:
        """Get popular product recommendations."""
        
        try:
            if self.user_item_matrix is None:
                return []
            
            # Calculate popularity scores (sum of ratings)
            popularity_scores = self.user_item_matrix.sum(axis=0).sort_values(ascending=False)
            
            recommendations = []
            for product_id, score in popularity_scores.head(count * 2).items():  # Get more to filter
                rec_item = await self._create_recommendation_item(
                    product_id, score / popularity_scores.max(), categories, min_rating
                )
                if rec_item:
                    recommendations.append(rec_item)
                    if len(recommendations) >= count:
                        break
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting popular recommendations: {str(e)}")
            return []
    
    async def _create_recommendation_item(
        self,
        product_id: str,
        score: float,
        categories: Optional[List[str]] = None,
        min_rating: Optional[float] = None
    ) -> Optional[RecommendationItem]:
        """Create a recommendation item with product details."""
        
        try:
            # Get product features if available
            product_info = {}
            if self.product_features is not None and product_id in self.product_features.index:
                product_row = self.product_features.loc[product_id]
                product_info = {
                    'product_name': product_row.get('product_category_name', product_id),
                    'category': product_row.get('product_category_name'),
                    'price': product_row.get('price'),
                }
            
            # Apply category filter
            if categories and product_info.get('category'):
                if product_info['category'] not in categories:
                    return None
            
            # Apply rating filter (if we have ratings data)
            if min_rating and 'rating' in product_info:
                if product_info['rating'] < min_rating:
                    return None
            
            return RecommendationItem(
                product_id=product_id,
                product_name=product_info.get('product_name'),
                category=product_info.get('category'),
                score=min(score, 1.0),  # Normalize score
                price=product_info.get('price'),
                rating=product_info.get('rating'),
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Error creating recommendation item for {product_id}: {str(e)}")
            return None
    
    async def get_similar_products(self, product_id: str, count: int = 10) -> List[SimilarProduct]:
        """Get similar products based on product ID."""
        
        if not self.models_loaded or self.item_similarities is None:
            return []
        
        try:
            if product_id not in self.user_item_matrix.columns:
                return []
            
            # Get product index
            product_idx = self.user_item_matrix.columns.get_loc(product_id)
            
            # Get similarity scores
            sim_scores = self.item_similarities[product_idx]
            similar_indices = np.argsort(sim_scores)[::-1][1:count+1]  # Exclude self
            
            similar_products = []
            for idx in similar_indices:
                sim_product_id = self.user_item_matrix.columns[idx]
                similarity_score = sim_scores[idx]
                
                # Get product info
                product_name = None
                category = None
                if self.product_features is not None and sim_product_id in self.product_features.index:
                    product_row = self.product_features.loc[sim_product_id]
                    product_name = product_row.get('product_category_name')
                    category = product_row.get('product_category_name')
                
                similar_products.append(SimilarProduct(
                    product_id=sim_product_id,
                    product_name=product_name,
                    similarity_score=similarity_score,
                    category=category
                ))
            
            return similar_products
            
        except Exception as e:
            logger.error(f"Error getting similar products for {product_id}: {str(e)}")
            return []
    
    async def get_trending_products(
        self, 
        count: int = 20, 
        category: Optional[str] = None,
        time_window_hours: int = 24
    ) -> List[TrendingProduct]:
        """Get trending products (mock implementation for demo)."""
        
        try:
            if self.user_item_matrix is None:
                return []
            
            # Simple trending based on recent popularity (mock implementation)
            # In a real system, this would use time-based interaction data
            popularity_scores = self.user_item_matrix.sum(axis=0).sort_values(ascending=False)
            
            trending_products = []
            for product_id, interaction_count in popularity_scores.head(count * 2).items():
                # Get product info
                product_name = None
                product_category = None
                if self.product_features is not None and product_id in self.product_features.index:
                    product_row = self.product_features.loc[product_id]
                    product_name = product_row.get('product_category_name')
                    product_category = product_row.get('product_category_name')
                
                # Apply category filter
                if category and product_category != category:
                    continue
                
                # Mock trend score (in real system, calculate based on growth rate)
                trend_score = float(interaction_count) / popularity_scores.max()
                
                trending_products.append(TrendingProduct(
                    product_id=product_id,
                    product_name=product_name,
                    category=product_category,
                    trend_score=trend_score,
                    interaction_count=int(interaction_count),
                    growth_rate=np.random.uniform(0.1, 2.0),  # Mock growth rate
                    region=self.region
                ))
                
                if len(trending_products) >= count:
                    break
            
            return trending_products
            
        except Exception as e:
            logger.error(f"Error getting trending products: {str(e)}")
            return []
    
    async def get_cross_region_recommendations(
        self,
        user_id: str,
        regions: List[str],
        count: int = 10,
        aggregation_method: AggregationMethod = AggregationMethod.MERGE
    ) -> Dict[str, Any]:
        """Get recommendations from multiple regions and aggregate them."""
        
        try:
            region_results = {}
            
            # Query each region
            async with httpx.AsyncClient(timeout=10.0) as client:
                tasks = []
                for region in regions:
                    if region == self.region:
                        # Local region
                        continue
                    
                    endpoint = settings.REGION_ENDPOINTS.get(region)
                    if endpoint:
                        task = self._query_region_recommendations(client, endpoint, user_id, count)
                        tasks.append((region, task))
                
                # Execute all requests
                for region, task in tasks:
                    try:
                        result = await task
                        if result:
                            region_results[region] = result
                    except Exception as e:
                        logger.error(f"Failed to get recommendations from {region}: {str(e)}")
            
            # Add local recommendations
            local_recs = await self.get_user_recommendations(user_id, count)
            if local_recs:
                region_results[self.region] = local_recs
            
            # Aggregate results
            aggregated_recs = self._aggregate_cross_region_results(
                region_results, count, aggregation_method
            )
            
            return {
                "aggregated_recommendations": aggregated_recs,
                "region_results": {
                    region: [rec.dict() for rec in recs] 
                    for region, recs in region_results.items()
                },
                "regions_queried": list(region_results.keys()),
                "aggregation_method": aggregation_method
            }
            
        except Exception as e:
            logger.error(f"Error getting cross-region recommendations: {str(e)}")
            return {"error": str(e)}
    
    async def _query_region_recommendations(
        self, client: httpx.AsyncClient, endpoint: str, user_id: str, count: int
    ) -> Optional[List[RecommendationItem]]:
        """Query recommendations from a specific region."""
        
        try:
            response = await client.post(
                f"{endpoint}/api/v1/recommendations/user/{user_id}",
                json={"count": count},
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return [RecommendationItem(**item) for item in data["recommendations"]]
            
        except Exception as e:
            logger.error(f"Error querying region {endpoint}: {str(e)}")
        
        return None
    
    def _aggregate_cross_region_results(
        self,
        region_results: Dict[str, List[RecommendationItem]],
        count: int,
        method: AggregationMethod
    ) -> List[RecommendationItem]:
        """Aggregate recommendations from multiple regions."""
        
        if not region_results:
            return []
        
        if method == AggregationMethod.MERGE:
            # Simple merge with deduplication
            all_recs = []
            seen_products = set()
            
            for region, recs in region_results.items():
                for rec in recs:
                    if rec.product_id not in seen_products:
                        all_recs.append(rec)
                        seen_products.add(rec.product_id)
            
            # Sort by score and return top count
            return sorted(all_recs, key=lambda x: x.score, reverse=True)[:count]
        
        elif method == AggregationMethod.HIGHEST_SCORE:
            # Keep only the highest score for each product
            product_best = {}
            
            for region, recs in region_results.items():
                for rec in recs:
                    if rec.product_id not in product_best or rec.score > product_best[rec.product_id].score:
                        product_best[rec.product_id] = rec
            
            return sorted(product_best.values(), key=lambda x: x.score, reverse=True)[:count]
        
        # Default to merge
        return self._aggregate_cross_region_results(region_results, count, AggregationMethod.MERGE)
    
    async def get_model_stats(self) -> Dict[str, Any]:
        """Get model statistics."""
        
        stats = {
            "models_loaded": self.models_loaded,
            "last_model_update": self.last_model_update.isoformat() if self.last_model_update else None,
            "region": self.region,
            "startup_time": datetime.fromtimestamp(self.startup_time).isoformat()
        }
        
        if self.models_loaded:
            if self.user_item_matrix is not None:
                stats["user_count"] = len(self.user_item_matrix.index)
                stats["product_count"] = len(self.user_item_matrix.columns)
                stats["total_interactions"] = int(self.user_item_matrix.count().sum())
                stats["matrix_density"] = float(
                    self.user_item_matrix.count().sum() / 
                    (len(self.user_item_matrix.index) * len(self.user_item_matrix.columns))
                )
            
            if self.svd_model is not None:
                stats["svd_components"] = self.svd_model.n_components
                stats["explained_variance_ratio"] = float(self.svd_model.explained_variance_ratio_.sum())
        
        return stats
    
    async def refresh_models(self):
        """Refresh models (reload from data)."""
        
        try:
            logger.info("Refreshing models...")
            await self.load_models()
            logger.info("Model refresh completed")
        except Exception as e:
            logger.error(f"Error refreshing models: {str(e)}")
            raise
