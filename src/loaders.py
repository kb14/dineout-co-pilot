import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the data loader with optional data directory path."""
        self.data_dir = data_dir or Path("data")
    
    def load_data(self, restaurant_id: str) -> Dict[str, pd.DataFrame]:
        """
        Load all data sources for a restaurant.
        
        Args:
            restaurant_id: The ID of the restaurant to load data for
            
        Returns:
            Dictionary containing all dataframes:
            - master: Restaurant master data
            - metrics: Daily performance metrics
            - ads: Advertising campaign data
            - discounts: Discount history
            - benchmarks: Peer benchmark data
        """
        try:
            # Load master data
            master_df = pd.read_csv(self.data_dir / "restaurant_master.csv")
            master_df['onboarded_date'] = pd.to_datetime(master_df['onboarded_date'])
            master_data = master_df[master_df['restaurant_id'] == restaurant_id].copy()
            if master_data.empty:
                raise ValueError(f"Restaurant {restaurant_id} not found in master data")
        
            # Load metrics data
            metrics_df = pd.read_csv(self.data_dir / "restaurant_metrics.csv")
            metrics_df['date'] = pd.to_datetime(metrics_df['date'])
            metrics_data = metrics_df[metrics_df['restaurant_id'] == restaurant_id].copy()
            if metrics_data.empty:
                raise ValueError(f"No metrics data found for restaurant {restaurant_id}")

            # Load ads data
            ads_df = pd.read_csv(self.data_dir / "ads_data.csv")
            ads_df['campaign_start'] = pd.to_datetime(ads_df['campaign_start'])
            ads_df['campaign_end'] = pd.to_datetime(ads_df['campaign_end'])
            ads_data = ads_df[ads_df['restaurant_id'] == restaurant_id].copy()
            if ads_data.empty:
                logger.warning(f"No ads data found for restaurant {restaurant_id}")

            # Load discount data
            discount_df = pd.read_csv(self.data_dir / "discount_history.csv")
            discount_df['start_date'] = pd.to_datetime(discount_df['start_date'])
            discount_df['end_date'] = pd.to_datetime(discount_df['end_date'])
            discount_data = discount_df[discount_df['restaurant_id'] == restaurant_id].copy()
            if discount_data.empty:
                logger.warning(f"No discount history found for restaurant {restaurant_id}")
            
            # Load benchmarks using restaurant's locality and cuisine
            locality = master_data.iloc[0]['locality']
            cuisine = master_data.iloc[0]['cuisine']
            benchmark_df = pd.read_csv(self.data_dir / "peer_benchmarks.csv")
            benchmark_data = benchmark_df[
                (benchmark_df['locality'] == locality) & 
                (benchmark_df['cuisine'] == cuisine)
            ].copy()
            if benchmark_data.empty:
                logger.warning(f"No peer benchmarks found for {locality} - {cuisine}")

            return {
                    'master': master_data,
                    'metrics': metrics_data,
                    'ads': ads_data,
                    'discounts': discount_data,
                    'benchmarks': benchmark_data
                }

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise 