"""Batch prediction engine for NYC Taxi duration prediction"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)


class BatchPredictor:
    """High-performance batch prediction engine with parallel processing"""
    
    def __init__(self, model_path: Path = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self.dv = None
        self._load_model()
        
    def _load_model(self) -> None:
        """Load the trained model and vectorizer"""
        try:
            logger.info(f"🔄 Loading model from {self.model_path}")
            with open(self.model_path, 'rb') as f_in:
                self.dv, self.model = pickle.load(f_in)
            logger.info("✅ Model and DictVectorizer loaded successfully")
        except FileNotFoundError:
            logger.error(f"❌ Model file not found: {self.model_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for batch prediction
        
        Args:
            df: DataFrame with trip data
            
        Returns:
            DataFrame with prepared features
        """
        logger.info(f"🔧 Preparing features for {len(df)} trips")
        
        # Create feature copy
        features_df = df.copy()
        
        # Create PU_DO feature
        features_df['PU_DO'] = (
            features_df['PULocationID'].astype(str) + '_' + 
            features_df['DOLocationID'].astype(str)
        )
        
        # Select only required features
        feature_cols = ['PU_DO', 'trip_distance']
        features_df = features_df[feature_cols]
        
        logger.info(f"✅ Features prepared: {len(features_df)} rows, {len(feature_cols)} features")
        return features_df
    
    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform batch predictions on the entire dataset
        
        Args:
            df: DataFrame with trip data
            
        Returns:
            DataFrame with predictions added
        """
        logger.info(f"🎯 Starting batch prediction for {len(df)} trips")
        start_time = datetime.now()
        
        # Prepare features
        features_df = self.prepare_features(df)
        
        # Convert to dict format for DictVectorizer
        feature_dicts = features_df.to_dict('records')
        
        # Transform features
        logger.info("🔄 Transforming features...")
        X = self.dv.transform(feature_dicts)
        
        # Make predictions
        logger.info("🔄 Making predictions...")
        predictions = self.model.predict(X)
        
        # Add predictions to original dataframe
        result_df = df.copy()
        result_df['predicted_duration'] = predictions
        result_df['prediction_timestamp'] = datetime.now()
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        throughput = len(df) / processing_time
        
        logger.info(f"✅ Batch prediction completed!")
        logger.info(f"📊 Processed {len(df)} trips in {processing_time:.2f}s")
        logger.info(f"⚡ Throughput: {throughput:.1f} predictions/second")
        logger.info(f"📈 Prediction stats: mean={predictions.mean():.2f}, "
                   f"std={predictions.std():.2f}, "
                   f"min={predictions.min():.2f}, "
                   f"max={predictions.max():.2f}")
        
        return result_df
    
    def predict_batch_parallel(
        self, 
        df: pd.DataFrame, 
        chunk_size: int = None,
        max_workers: int = None
    ) -> pd.DataFrame:
        """
        Perform parallel batch predictions for large datasets
        
        Args:
            df: DataFrame with trip data
            chunk_size: Size of each processing chunk
            max_workers: Maximum number of worker threads
            
        Returns:
            DataFrame with predictions added
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        max_workers = max_workers or settings.MAX_WORKERS
        
        logger.info(f"🚀 Starting parallel batch prediction")
        logger.info(f"📊 Dataset: {len(df)} trips, chunk_size: {chunk_size}, workers: {max_workers}")
        
        start_time = datetime.now()
        
        # Split dataframe into chunks
        chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
        logger.info(f"📦 Split into {len(chunks)} chunks")
        
        # Process chunks in parallel
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks
            future_to_chunk = {
                executor.submit(self.predict_batch, chunk): i 
                for i, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ Completed chunk {chunk_idx + 1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"❌ Error processing chunk {chunk_idx}: {e}")
                    raise
        
        # Combine all results
        final_result = pd.concat(results, ignore_index=True)
        
        # Calculate final stats
        processing_time = (datetime.now() - start_time).total_seconds()
        throughput = len(final_result) / processing_time
        
        logger.info(f"🎉 Parallel batch prediction completed!")
        logger.info(f"📊 Processed {len(final_result)} trips in {processing_time:.2f}s")
        logger.info(f"⚡ Throughput: {throughput:.1f} predictions/second")
        
        return final_result
    
    def save_predictions(
        self, 
        df: pd.DataFrame, 
        batch_id: str,
        output_format: str = "parquet"
    ) -> Path:
        """
        Save predictions to output directory
        
        Args:
            df: DataFrame with predictions
            batch_id: Batch identifier
            output_format: Output format (parquet, csv, json)
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"predictions_{batch_id}_{timestamp}.{output_format}"
        filepath = settings.DATA_OUTPUT_DIR / filename
        
        # Save in requested format
        if output_format == "parquet":
            df.to_parquet(filepath, index=False)
        elif output_format == "csv":
            df.to_csv(filepath, index=False)
        elif output_format == "json":
            df.to_json(filepath, orient="records", date_format="iso")
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Log summary statistics
        predictions = df['predicted_duration']
        logger.info(f"💾 Saved predictions to {filepath}")
        logger.info(f"📊 Prediction summary:")
        logger.info(f"  - Total trips: {len(df)}")
        logger.info(f"  - Mean duration: {predictions.mean():.2f} minutes")
        logger.info(f"  - Median duration: {predictions.median():.2f} minutes")
        logger.info(f"  - Duration range: {predictions.min():.2f} - {predictions.max():.2f} minutes")
        
        return filepath
    
    def get_system_metrics(self) -> Dict:
        """Get current system resource usage"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available_gb': psutil.virtual_memory().available / (1024**3),
            'disk_usage_percent': psutil.disk_usage('/').percent,
        }
    
    def process_batch_file(
        self, 
        input_path: Path, 
        batch_id: str = None,
        use_parallel: bool = True
    ) -> Tuple[pd.DataFrame, Path]:
        """
        Process a complete batch file from input to output
        
        Args:
            input_path: Path to input data file
            batch_id: Optional batch identifier
            use_parallel: Whether to use parallel processing
            
        Returns:
            Tuple of (predictions_df, output_path)
        """
        if batch_id is None:
            batch_id = input_path.stem
            
        logger.info(f"🔄 Processing batch file: {input_path}")
        
        # Check system resources
        metrics = self.get_system_metrics()
        logger.info(f"💻 System metrics: CPU {metrics['cpu_percent']:.1f}%, "
                   f"Memory {metrics['memory_percent']:.1f}%, "
                   f"Available RAM {metrics['memory_available_gb']:.1f}GB")
        
        # Load data
        if input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv':
            df = pd.read_csv(input_path)
        else:
            raise ValueError(f"Unsupported file format: {input_path.suffix}")
        
        logger.info(f"📂 Loaded {len(df)} trips from {input_path}")
        
        # Choose processing method based on data size and settings
        if use_parallel and len(df) > settings.CHUNK_SIZE:
            predictions_df = self.predict_batch_parallel(df)
        else:
            predictions_df = self.predict_batch(df)
        
        # Save predictions
        output_path = self.save_predictions(predictions_df, batch_id)
        
        return predictions_df, output_path


if __name__ == "__main__":
    # Test the batch predictor
    logging.basicConfig(level=logging.INFO)
    
    predictor = BatchPredictor()
    
    # Create test data
    test_data = pd.DataFrame({
        'trip_id': ['test_001', 'test_002', 'test_003'],
        'PULocationID': [161, 236, 142],
        'DOLocationID': [236, 161, 79],
        'trip_distance': [2.5, 1.8, 4.2]
    })
    
    # Test prediction
    results = predictor.predict_batch(test_data)
    print("\n🧪 Test Results:")
    print(results[['trip_id', 'predicted_duration']].to_string(index=False))
