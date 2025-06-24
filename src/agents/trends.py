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
    avg_daily_bookings: float = Field(description="Average daily bookings across the 30 days - also known as OPD (Orders Per Day)")
    avg_revenue_per_booking: float = Field(description="Average revenue per booking across the 30 days")
    avg_spend_per_cover: float = Field(description="Average spend per cover (diner) across the 30 days")
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
    
    def _create_campaign_enhanced_plot(self, data: pd.DataFrame, ads_df: pd.DataFrame, column: str, title: str, output_path: str):
        """Create a 7-day rolling average plot with campaign periods highlighted"""
        self._setup_plot_style()
        
        # Calculate 7-day rolling average
        rolling_avg = data[column].rolling(window=7, min_periods=1).mean()
        
        # Create figure and plot
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Plot the rolling average
        ax.plot(data['date'], rolling_avg, linewidth=2.5, color='#2E86AB', label='7-day Rolling Average')
        
        # Add campaign periods as shaded regions
        for _, campaign in ads_df.iterrows():
            campaign_start = pd.to_datetime(campaign['campaign_start'])
            campaign_end = pd.to_datetime(campaign['campaign_end'])
            
            # Add shaded region for campaign period
            ax.axvspan(campaign_start, campaign_end, alpha=0.2, color='#A23B72', 
                      label='Campaign Period' if _ == 0 else "")
            
            # Add campaign start annotation
            mask = data['date'] >= campaign_start
            campaign_start_value = rolling_avg[mask].iloc[0] if mask.any() else rolling_avg.iloc[0]
            ax.annotate(f'Campaign Start\n₹{campaign["spend"]:,}', 
                       xy=(campaign_start, campaign_start_value),
                       xytext=(10, 20), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#A23B72', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                       fontsize=9, color='white')
        
        # Detect and annotate significant anomalies (drops > 20%)
        pct_change = rolling_avg.pct_change()
        significant_drops = pct_change < -0.2  # 20% drop
        
        for idx, is_drop in enumerate(significant_drops):
            if is_drop and idx > 0:
                date_val = data['date'].iloc[idx]
                value_val = rolling_avg.iloc[idx]
                drop_pct = pct_change.iloc[idx] * 100
                
                ax.annotate(f'⚠️ Drop: {drop_pct:.1f}%', 
                           xy=(date_val, value_val),
                           xytext=(-10, -30), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='#F18F01', alpha=0.8),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                           fontsize=9, color='white')
        
        # Format x-axis to show one label per week
        ax.xaxis.set_major_locator(DayLocator(interval=7))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        
        # Rotate and align the tick labels so they look better
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add labels and title
        ax.set_title(title + ' (with Campaign Analysis)', pad=20, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel(column.capitalize(), fontsize=12)
        
        # Add legend
        ax.legend(loc='upper right')
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def analyze(self, master_df: pd.DataFrame, metrics_df: pd.DataFrame, ads_df: pd.DataFrame = None) -> TrendsOutput:
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
            avg_spend_per_cover=(totals.total_revenue / totals.total_covers) if totals.total_covers > 0 else 0,
            overall_cancellation_rate=(totals.total_cancellations / totals.total_bookings * 100) if totals.total_bookings > 0 else 0,
            avg_rating=metrics_df['avg_rating'].mean()
        )

        # Generate charts
        output_dir = Path(f"outputs/{restaurant_id}/plots")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate and save charts
        bookings_path = output_dir / "bookings_rolling_7day.png"
        bookings_relative_path = "plots/bookings_rolling_7day.png"
        
        # Use enhanced campaign plotting if ads data is available, otherwise use basic plot
        if ads_df is not None and not ads_df.empty:
            self._create_campaign_enhanced_plot(
                metrics_df, 
                ads_df,
                'bookings', 
                '7-Day Rolling Average: Daily Bookings',
                str(bookings_path)
            )
        else:
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




