import pandas as pd
import logging
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, DateFormatter
import seaborn as sns
from pathlib import Path
import os


logger = logging.getLogger(__name__)


class Totals(BaseModel):
    """Schema for total numbers across the 30 days"""
    total_bookings: int = Field(description="Total bookings across the 30 days")
    total_revenue: float = Field(description="Total revenue across the 30 days")
    total_cancellations: int = Field(description="Total cancellations across the 30 days")
    total_covers: int = Field(description="Total covers across the 30 days")


class Averages(BaseModel):
    """Schema for average numbers across the 30 days"""
    avg_daily_bookings: float = Field(description="Average daily bookings across the 30 days")
    avg_revenue_per_booking: float = Field(description="Average revenue per booking across the 30 days")
    overall_cancellation_rate: float = Field(description="Overall cancellation rate across the 30 days")
    avg_rating: float = Field(description="Average rating across the 30 days")


class Charts(BaseModel):
    """Schema for 7-day rolling average charts path"""
    bookings_rolling_7day_path: str = Field(description="Path to the 7-day rolling average bookings chart")


class TrendsOutput(BaseModel):
    """Schema for snapshot of restaurant metrics, their trends and insights"""
    totals: Totals = Field(description="Total restaurant numbers across the 30 days")
    averages: Averages = Field(description="Average restaurant numbers across the 30 days")
    charts: Charts = Field(description="7-day rolling average charts path")



class TrendsAgent:
    """Agent to calculate totals, averages, charts, trends and insights on the trends"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def _setup_plot_style(self):
        """Set up the plotting style for clean, modern charts"""
        plt.style.use('seaborn-v0_8')
        sns.set_theme()
        sns.set_palette("deep")
        plt.rcParams['figure.figsize'] = [10, 6]
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
    
    def _create_rolling_average_plot(self, data: pd.DataFrame, column: str, title: str, output_path: str):
        """Create a 7-day rolling average plot for the specified column"""
        self._setup_plot_style()
        
        # Calculate 7-day rolling average
        rolling_avg = data[column].rolling(window=7, min_periods=1).mean()
        
        # Create figure and plot
        fig, ax = plt.subplots()
        
        # Plot the rolling average
        ax.plot(data['date'], rolling_avg, linewidth=2)
        
        # Format x-axis to show one label per week
        ax.xaxis.set_major_locator(DayLocator(interval=7))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        
        # Rotate and align the tick labels so they look better
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add labels and title
        ax.set_title(title, pad=20)
        ax.set_xlabel('Date')
        ax.set_ylabel(column.capitalize())
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def analyze(self, master_df: pd.DataFrame, metrics_df: pd.DataFrame) -> TrendsOutput:
        """Calculate and analyze trends in restaurant metrics and generate insights"""
        
        restaurant_id = master_df['restaurant_id'].iloc[0]


        # Calculate totals
        totals = Totals(
            total_bookings=metrics_df['bookings'].sum(),
            total_revenue=metrics_df['revenue'].sum(),
            total_cancellations=metrics_df['cancellations'].sum(),
            total_covers=metrics_df['covers'].sum()
        )

        # Calculate averages
        averages = Averages(
            avg_daily_bookings=metrics_df['bookings'].mean(),
            avg_revenue_per_booking=(totals.total_revenue / totals.total_bookings) if totals.total_bookings > 0 else 0,
            overall_cancellation_rate=(totals.total_cancellations / totals.total_bookings * 100) if totals.total_bookings > 0 else 0,
            avg_rating=metrics_df['avg_rating'].mean()
        )

        # Generate charts
        output_dir = Path(f"outputs/{restaurant_id}/plots")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate and save charts
        bookings_path = output_dir / "bookings_rolling_7day.png"
        bookings_relative_path = "plots/bookings_rolling_7day.png"
        
        self._create_rolling_average_plot(
            metrics_df, 
            'bookings', 
            '7-Day Rolling Average: Daily Bookings',
            str(bookings_path)
        )
        
        
        charts = Charts(
            bookings_rolling_7day_path=bookings_relative_path,
        )


        return TrendsOutput(
            totals=totals,
            averages=averages,
            charts=charts,
        )




