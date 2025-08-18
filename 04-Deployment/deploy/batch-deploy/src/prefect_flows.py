"""Prefect flows for NYC Taxi batch prediction system"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import shutil
import psutil
from prefect import flow, task, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner
from prefect.blocks.system import Secret

from data_generator import TaxiDataGenerator
from batch_predictor import BatchPredictor
from config.settings import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))


@task(name="generate-batch-data", retries=2, retry_delay_seconds=30)
def generate_batch_data_task(batch_id: str = None) -> Tuple[str, Path]:
    """
    Generate batch data for processing
    
    Args:
        batch_id: Optional batch identifier
        
    Returns:
        Tuple of (batch_id, file_path)
    """
    logger = get_run_logger()
    
    if batch_id is None:
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"🚕 Generating batch data with ID: {batch_id}")
    
    generator = TaxiDataGenerator()
    df, filepath = generator.generate_and_save_batch(batch_id)
    
    logger.info(f"✅ Generated {len(df)} trips, saved to {filepath}")
    
    return batch_id, filepath


@task(name="validate-input-data", retries=1)
def validate_input_data_task(filepath: Path) -> bool:
    """
    Validate input data quality and format
    
    Args:
        filepath: Path to input data file
        
    Returns:
        True if validation passes
    """
    logger = get_run_logger()
    logger.info(f"🔍 Validating input data: {filepath}")
    
    try:
        # Load and validate data
        df = pd.read_parquet(filepath)
        
        # Check required columns
        required_cols = ['PULocationID', 'DOLocationID', 'trip_distance']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Check data quality
        if df.empty:
            raise ValueError("Dataset is empty")
        
        if df['trip_distance'].isna().any():
            raise ValueError("Found null values in trip_distance")
        
        if (df['trip_distance'] <= 0).any():
            raise ValueError("Found non-positive trip distances")
        
        # Check location IDs are in valid range
        for col in ['PULocationID', 'DOLocationID']:
            if (df[col] < settings.MIN_LOCATION_ID).any() or (df[col] > settings.MAX_LOCATION_ID).any():
                raise ValueError(f"Location IDs in {col} outside valid range")
        
        logger.info(f"✅ Data validation passed: {len(df)} valid trips")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data validation failed: {e}")
        raise


@task(name="check-system-resources")
def check_system_resources_task() -> Dict:
    """
    Check system resources before processing
    
    Returns:
        Dictionary with system metrics
    """
    logger = get_run_logger()
    
    metrics = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'memory_available_gb': psutil.virtual_memory().available / (1024**3),
        'disk_usage_percent': psutil.disk_usage('/').percent,
    }
    
    logger.info(f"💻 System metrics: CPU {metrics['cpu_percent']:.1f}%, "
               f"Memory {metrics['memory_percent']:.1f}%, "
               f"Available RAM {metrics['memory_available_gb']:.1f}GB")
    
    # Check resource limits
    if metrics['memory_percent'] > 90:
        logger.warning("⚠️ High memory usage detected")
    
    if metrics['cpu_percent'] > settings.CPU_LIMIT_PERCENT:
        logger.warning("⚠️ High CPU usage detected")
    
    if metrics['memory_available_gb'] < settings.MEMORY_LIMIT_GB:
        logger.warning("⚠️ Low available memory")
    
    return metrics


@task(name="process-batch-predictions", retries=1, retry_delay_seconds=60)
def process_batch_predictions_task(
    batch_id: str, 
    input_path: Path,
    use_parallel: bool = True
) -> Tuple[Path, Dict]:
    """
    Process batch predictions
    
    Args:
        batch_id: Batch identifier
        input_path: Path to input data
        use_parallel: Whether to use parallel processing
        
    Returns:
        Tuple of (output_path, processing_stats)
    """
    logger = get_run_logger()
    logger.info(f"🎯 Processing batch predictions for {batch_id}")
    
    start_time = datetime.now()
    
    # Initialize predictor
    predictor = BatchPredictor()
    
    # Process batch
    predictions_df, output_path = predictor.process_batch_file(
        input_path=input_path,
        batch_id=batch_id,
        use_parallel=use_parallel
    )
    
    # Calculate processing stats
    processing_time = (datetime.now() - start_time).total_seconds()
    throughput = len(predictions_df) / processing_time
    
    stats = {
        'batch_id': batch_id,
        'num_predictions': len(predictions_df),
        'processing_time_seconds': processing_time,
        'throughput_per_second': throughput,
        'mean_duration': float(predictions_df['predicted_duration'].mean()),
        'median_duration': float(predictions_df['predicted_duration'].median()),
        'min_duration': float(predictions_df['predicted_duration'].min()),
        'max_duration': float(predictions_df['predicted_duration'].max()),
        'output_file': str(output_path),
        'file_size_mb': output_path.stat().st_size / (1024 * 1024)
    }
    
    logger.info(f"✅ Batch processing completed: {stats['num_predictions']} predictions "
               f"in {stats['processing_time_seconds']:.2f}s")
    
    return output_path, stats


@task(name="move-to-processed")
def move_to_processed_task(input_path: Path, batch_id: str) -> Path:
    """
    Move processed input file to processed directory
    
    Args:
        input_path: Original input file path
        batch_id: Batch identifier
        
    Returns:
        New path in processed directory
    """
    logger = get_run_logger()
    
    processed_path = settings.DATA_PROCESSED_DIR / f"processed_{batch_id}_{input_path.name}"
    shutil.move(str(input_path), str(processed_path))
    
    logger.info(f"📁 Moved {input_path} to {processed_path}")
    
    return processed_path


@task(name="cleanup-old-files")
def cleanup_old_files_task() -> Dict:
    """
    Clean up old files based on retention settings
    
    Returns:
        Cleanup statistics
    """
    logger = get_run_logger()
    logger.info("🧹 Starting cleanup of old files")
    
    now = datetime.now()
    stats = {
        'output_files_deleted': 0,
        'log_files_deleted': 0,
        'processed_files_deleted': 0,
        'total_space_freed_mb': 0
    }
    
    # Cleanup output files
    output_cutoff = now - timedelta(days=settings.OUTPUT_RETENTION_DAYS)
    for file_path in settings.DATA_OUTPUT_DIR.glob("*.parquet"):
        if datetime.fromtimestamp(file_path.stat().st_mtime) < output_cutoff:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            file_path.unlink()
            stats['output_files_deleted'] += 1
            stats['total_space_freed_mb'] += size_mb
    
    # Cleanup log files
    log_cutoff = now - timedelta(days=settings.LOG_RETENTION_DAYS)
    for file_path in settings.LOGS_DIR.glob("*.log"):
        if datetime.fromtimestamp(file_path.stat().st_mtime) < log_cutoff:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            file_path.unlink()
            stats['log_files_deleted'] += 1
            stats['total_space_freed_mb'] += size_mb
    
    # Cleanup processed files (older than output retention)
    for file_path in settings.DATA_PROCESSED_DIR.glob("*.parquet"):
        if datetime.fromtimestamp(file_path.stat().st_mtime) < output_cutoff:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            file_path.unlink()
            stats['processed_files_deleted'] += 1
            stats['total_space_freed_mb'] += size_mb
    
    logger.info(f"🧹 Cleanup completed: deleted {stats['output_files_deleted']} output files, "
               f"{stats['log_files_deleted']} log files, {stats['processed_files_deleted']} processed files")
    logger.info(f"💾 Total space freed: {stats['total_space_freed_mb']:.2f} MB")
    
    return stats


@flow(
    name="taxi-batch-prediction-flow",
    description="Complete NYC Taxi batch prediction pipeline",
    task_runner=ConcurrentTaskRunner(),
    log_prints=True
)
def taxi_batch_prediction_flow(
    batch_id: Optional[str] = None,
    use_parallel: bool = True,
    skip_data_generation: bool = False,
    input_file_path: Optional[str] = None
) -> Dict:
    """
    Main flow for batch taxi prediction processing
    
    Args:
        batch_id: Optional batch identifier
        use_parallel: Whether to use parallel processing
        skip_data_generation: Skip data generation and use existing file
        input_file_path: Path to existing input file (if skip_data_generation=True)
        
    Returns:
        Flow execution statistics
    """
    logger = get_run_logger()
    logger.info("🚀 Starting NYC Taxi Batch Prediction Flow")
    
    flow_start_time = datetime.now()
    
    # Check system resources
    system_metrics = check_system_resources_task()
    
    # Generate or use existing data
    if skip_data_generation and input_file_path:
        batch_id = batch_id or Path(input_file_path).stem
        input_path = Path(input_file_path)
        logger.info(f"📂 Using existing input file: {input_path}")
    else:
        # Generate batch data
        batch_id, input_path = generate_batch_data_task(batch_id)
    
    # Validate input data
    validation_result = validate_input_data_task(input_path)
    
    if not validation_result:
        raise ValueError("Input data validation failed")
    
    # Process batch predictions
    output_path, processing_stats = process_batch_predictions_task(
        batch_id=batch_id,
        input_path=input_path,
        use_parallel=use_parallel
    )
    
    # Move input file to processed directory
    processed_path = move_to_processed_task(input_path, batch_id)
    
    # Calculate total flow time
    total_flow_time = (datetime.now() - flow_start_time).total_seconds()
    
    # Compile final statistics
    flow_stats = {
        'flow_id': batch_id,
        'total_flow_time_seconds': total_flow_time,
        'system_metrics': system_metrics,
        'processing_stats': processing_stats,
        'input_file': str(processed_path),
        'output_file': str(output_path),
        'flow_completed_at': datetime.now().isoformat(),
        'use_parallel_processing': use_parallel
    }
    
    logger.info(f"🎉 Flow completed successfully in {total_flow_time:.2f}s")
    logger.info(f"📊 Processed {processing_stats['num_predictions']} predictions")
    logger.info(f"📁 Output saved to: {output_path}")
    
    return flow_stats


@flow(
    name="taxi-batch-cleanup-flow",
    description="Cleanup old files and maintain system health"
)
def taxi_batch_cleanup_flow() -> Dict:
    """
    Maintenance flow for cleaning up old files
    
    Returns:
        Cleanup statistics
    """
    logger = get_run_logger()
    logger.info("🧹 Starting cleanup flow")
    
    # Check system resources
    system_metrics = check_system_resources_task()
    
    # Cleanup old files
    cleanup_stats = cleanup_old_files_task()
    
    result = {
        'cleanup_completed_at': datetime.now().isoformat(),
        'system_metrics': system_metrics,
        'cleanup_stats': cleanup_stats
    }
    
    logger.info("✅ Cleanup flow completed")
    
    return result


if __name__ == "__main__":
    # Test the flow locally
    import asyncio
    
    async def test_flow():
        # Test with small batch
        result = await taxi_batch_prediction_flow(
            batch_id="test_local",
            use_parallel=False
        )
        print("Flow result:", result)
    
    asyncio.run(test_flow())
