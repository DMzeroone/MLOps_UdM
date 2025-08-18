"""Data generator for NYC Taxi batch prediction system"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class TaxiDataGenerator:
    """Generates realistic NYC taxi trip data for batch processing"""
    
    def __init__(self):
        self.rng = np.random.default_rng(seed=42)
        
    def generate_batch_data(
        self, 
        num_trips: int = None,
        timestamp: datetime = None
    ) -> pd.DataFrame:
        """
        Generate a batch of taxi trip data
        
        Args:
            num_trips: Number of trips to generate (default from settings)
            timestamp: Timestamp for the batch (default: now)
            
        Returns:
            DataFrame with trip data
        """
        if num_trips is None:
            num_trips = settings.NUM_TRIPS_PER_BATCH
            
        if timestamp is None:
            timestamp = datetime.now()
            
        logger.info(f"🚕 Generating {num_trips} taxi trips for batch at {timestamp}")
        
        # Generate realistic trip data
        data = {
            'trip_id': [f"trip_{timestamp.strftime('%Y%m%d_%H%M%S')}_{i:06d}" 
                       for i in range(num_trips)],
            'batch_timestamp': [timestamp] * num_trips,
            'PULocationID': self._generate_location_ids(num_trips),
            'DOLocationID': self._generate_location_ids(num_trips),
            'trip_distance': self._generate_trip_distances(num_trips),
            'pickup_datetime': self._generate_pickup_times(num_trips, timestamp),
        }
        
        df = pd.DataFrame(data)
        
        # Ensure pickup != dropoff
        same_location_mask = df['PULocationID'] == df['DOLocationID']
        df.loc[same_location_mask, 'DOLocationID'] = (
            df.loc[same_location_mask, 'DOLocationID'] + 1
        ) % settings.MAX_LOCATION_ID + 1
        
        logger.info(f"✅ Generated {len(df)} trips with {df['PULocationID'].nunique()} unique pickup locations")
        
        return df
    
    def _generate_location_ids(self, num_trips: int) -> List[int]:
        """Generate realistic location IDs with Manhattan bias"""
        # Manhattan zones (higher probability)
        manhattan_zones = list(range(12, 80)) + list(range(87, 120)) + list(range(140, 180))
        other_zones = [i for i in range(settings.MIN_LOCATION_ID, settings.MAX_LOCATION_ID + 1) 
                      if i not in manhattan_zones]
        
        # 70% Manhattan, 30% other boroughs
        manhattan_count = int(num_trips * 0.7)
        other_count = num_trips - manhattan_count
        
        locations = (
            self.rng.choice(manhattan_zones, size=manhattan_count).tolist() +
            self.rng.choice(other_zones, size=other_count).tolist()
        )
        
        self.rng.shuffle(locations)
        return locations
    
    def _generate_trip_distances(self, num_trips: int) -> List[float]:
        """Generate realistic trip distances with log-normal distribution"""
        # Log-normal distribution for realistic trip distances
        distances = self.rng.lognormal(mean=1.2, sigma=0.8, size=num_trips)
        
        # Clip to realistic bounds
        distances = np.clip(
            distances, 
            settings.MIN_TRIP_DISTANCE, 
            settings.MAX_TRIP_DISTANCE
        )
        
        # Round to 2 decimal places
        return np.round(distances, 2).tolist()
    
    def _generate_pickup_times(self, num_trips: int, base_timestamp: datetime) -> List[datetime]:
        """Generate pickup times within the batch window"""
        # Generate times within 1 hour window
        time_offsets = self.rng.uniform(0, 3600, size=num_trips)  # seconds
        
        pickup_times = [
            base_timestamp + timedelta(seconds=offset) 
            for offset in time_offsets
        ]
        
        return pickup_times
    
    def save_batch_data(self, df: pd.DataFrame, batch_id: str) -> Path:
        """
        Save batch data to input directory
        
        Args:
            df: DataFrame with trip data
            batch_id: Unique identifier for the batch
            
        Returns:
            Path to saved file
        """
        filename = f"taxi_batch_{batch_id}.parquet"
        filepath = settings.DATA_INPUT_DIR / filename
        
        # Save as parquet for efficiency
        df.to_parquet(filepath, index=False)
        
        logger.info(f"💾 Saved batch data to {filepath}")
        logger.info(f"📊 Batch stats: {len(df)} trips, "
                   f"avg distance: {df['trip_distance'].mean():.2f} miles")
        
        return filepath
    
    def generate_and_save_batch(self, batch_id: str = None) -> Tuple[pd.DataFrame, Path]:
        """
        Generate and save a complete batch
        
        Args:
            batch_id: Optional batch identifier (default: timestamp)
            
        Returns:
            Tuple of (DataFrame, file_path)
        """
        if batch_id is None:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        df = self.generate_batch_data()
        filepath = self.save_batch_data(df, batch_id)
        
        return df, filepath


def create_sample_data() -> None:
    """Create sample data for testing"""
    generator = TaxiDataGenerator()
    
    # Generate 3 sample batches
    for i in range(3):
        batch_id = f"sample_{i+1:02d}"
        df, filepath = generator.generate_and_save_batch(batch_id)
        print(f"Created sample batch: {filepath}")
        print(f"  - {len(df)} trips")
        print(f"  - Distance range: {df['trip_distance'].min():.2f} - {df['trip_distance'].max():.2f} miles")
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_sample_data()
