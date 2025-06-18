import pandas as pd
import logging
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import traceback
from src.agents.trends import TrendsOutput
from src.agents.ads import AdsOutput
from src.agents.discount import DiscountOutput
from src.prompts import BENCHMARK_SYSTEM_PROMPT, BENCHMARK_USER_PROMPT
import json

logger = logging.getLogger(__name__)



class BookingsComparison(BaseModel):
    """Comparison of bookings against peers across the 30 days"""
    total_bookings: int = Field(description="Total bookings of restaurant across the 30 days")
    total_peer_bookings: int = Field(description="Total bookings of peers across the 30 days")
    gap: float = Field(description="% difference in bookings vs peers")

class RevenueComparison(BaseModel):
    """Comparison of revenue against peers across the 30 days"""
    total_revenue: int = Field(description="Total revenue of restaurant across the 30 days")
    total_peer_revenue: int = Field(description="Total revenue of peers across the 30 days")
    gap: float = Field(description="% difference in revenue vs peers")


class RatingComparison(BaseModel):
    """Comparison of rating against peers across the 30 days"""
    rating: float = Field(description="Average Rating of restaurant across the 30 days")
    peer_rating: float = Field(description="Average Rating of peers across the 30 days")
    gap: float = Field(description="% difference in rating vs peers")

class AdsComparison(BaseModel):
    """Comparison of ads stats against peers"""
    avg_ad_spend: int = Field(description="Average ad spend of restaurant per day for the campaign activated days")
    ads_roi: float = Field(description="Avg Ads ROI of restaurant for campaign activated days")
    avg_ad_spend_peer: int = Field(description="Average ad spend of peers per day for last 30 days")
    ads_roi_peer: float = Field(description="Ads ROI of peers for last 30 days")
    gap_ads_roi: float = Field(description="% difference in ads ROI vs peers")
    gap_ad_spend: float = Field(description="% difference in ad spend vs peers")


class DiscountComparison(BaseModel):
    """Comparison of discount stats against peers"""
    avg_discount_percentage: float = Field(description="Average discount percentage of restaurant for discount days")
    discount_roi: float = Field(description="Avg Discount ROI of restaurant for discount days")
    avg_discount_percentage_peer: float = Field(description="Average discount percentage of peers for last 30 days")
    discount_roi_peer: float = Field(description="Discount ROI of peers for last 30 days")
    gap_discount_roi: float = Field(description="% difference in discount ROI vs peers")
    gap_discount_percentage: float = Field(description="% difference in discount percentage vs peers")
    


class BenchmarkOutput(BaseModel):
    """Schema for benchmark analysis output"""
    bookings_comparison: BookingsComparison = Field(description="Comparison of bookings against peers across the 30 days")
    revenue_comparison: RevenueComparison = Field(description="Comparison of revenue against peers across the 30 days")
    rating_comparison: RatingComparison = Field(description="Comparison of rating against peers across the 30 days")
    ads_comparison: AdsComparison = Field(description="Comparison of ads stats against peers")
    discount_comparison: DiscountComparison = Field(description="Comparison of discount stats against peers")
    llm_summary: str = Field(description="LLM generated insights on competitive position")

class BenchmarkAnalyzerAgent:
    """Agent to analyze restaurant performance against peer benchmarks"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def analyze(self, benchmarks_df: pd.DataFrame, trends_output: TrendsOutput, 
                ads_output: AdsOutput, discount_output: DiscountOutput) -> BenchmarkOutput:
        """Analyze restaurant performance against peer benchmarks"""
        try:
            if benchmarks_df.empty:
                return self._get_empty_analysis()
            
            # Bookings comparison
            total_bookings = trends_output.totals.total_bookings
            total_peer_bookings = benchmarks_df['avg_bookings'].iloc[0]
            bookings_gap = ((total_bookings - total_peer_bookings) / total_peer_bookings * 100) if total_peer_bookings > 0 else 0
            
            bookings_comparison = BookingsComparison(
                total_bookings=total_bookings,
                total_peer_bookings=int(total_peer_bookings),
                gap=round(bookings_gap, 2)
            )

            # Revenue comparison
            total_revenue = trends_output.totals.total_revenue
            total_peer_revenue = benchmarks_df['avg_revenue'].iloc[0]
            revenue_gap = ((total_revenue - total_peer_revenue) / total_peer_revenue * 100) if total_peer_revenue > 0 else 0
            
            revenue_comparison = RevenueComparison(
                total_revenue=int(total_revenue),
                total_peer_revenue=int(total_peer_revenue),
                gap=round(revenue_gap, 2)
            )

            # Rating comparison
            avg_rating = trends_output.averages.avg_rating
            peer_rating = benchmarks_df['avg_rating'].iloc[0]
            rating_gap = ((avg_rating - peer_rating) / peer_rating * 100) if peer_rating > 0 else 0
            
            rating_comparison = RatingComparison(
                rating=round(avg_rating, 2),
                peer_rating=round(peer_rating, 2),
                gap=round(rating_gap, 2)
            )

            # Ads comparison
            avg_ad_spend = ads_output.total_spend / ads_output.total_ad_days if ads_output.total_ad_days > 0 else 0
            ads_roi = ads_output.roi
            avg_ad_spend_peer = benchmarks_df['avg_ads_spend'].iloc[0] / 30  # Convert to daily average
            ads_roi_peer = benchmarks_df['avg_roi'].iloc[0]
            ads_roi_gap = ((ads_roi - ads_roi_peer) / ads_roi_peer * 100) if ads_roi_peer > 0 else 0
            ad_spend_gap = ((avg_ad_spend - avg_ad_spend_peer) / avg_ad_spend_peer * 100) if avg_ad_spend_peer > 0 else 0
            
            ads_comparison = AdsComparison(
                avg_ad_spend=int(avg_ad_spend),
                ads_roi=round(ads_roi, 2),
                avg_ad_spend_peer=int(avg_ad_spend_peer),
                ads_roi_peer=round(ads_roi_peer, 2),
                gap_ads_roi=round(ads_roi_gap, 2),
                gap_ad_spend=round(ad_spend_gap, 2)
            )

            # Discount comparison
            avg_discount_percentage = discount_output.avg_discount_percent
            discount_roi = discount_output.roi
            avg_discount_percentage_peer = benchmarks_df['avg_discount_percentage'].iloc[0]
            discount_roi_peer = benchmarks_df['avg_discount_roi'].iloc[0]
            discount_roi_gap = ((discount_roi - discount_roi_peer) / discount_roi_peer * 100) if discount_roi_peer > 0 else 0
            discount_percentage_gap = ((avg_discount_percentage - avg_discount_percentage_peer) / avg_discount_percentage_peer * 100) if avg_discount_percentage_peer > 0 else 0
            
            discount_comparison = DiscountComparison(
                avg_discount_percentage=round(avg_discount_percentage, 2),
                discount_roi=round(discount_roi, 2),
                avg_discount_percentage_peer=round(avg_discount_percentage_peer, 2),
                discount_roi_peer=round(discount_roi_peer, 2),
                gap_discount_roi=round(discount_roi_gap, 2),
                gap_discount_percentage=round(discount_percentage_gap, 2)
            )

            # Generate LLM summary
            core_metrics = {
                "bookings_comparison": bookings_comparison.model_dump(),
                "revenue_comparison": revenue_comparison.model_dump(),
                "rating_comparison": rating_comparison.model_dump()
            }

            ads_data = {
                "ads_comparison": ads_comparison.model_dump()
            }

            discount_data = {
                "discount_comparison": discount_comparison.model_dump()
            }

            messages = [
                {"role": "system", "content": BENCHMARK_SYSTEM_PROMPT},
                {"role": "user", "content": BENCHMARK_USER_PROMPT.format(
                    core_metrics_json=json.dumps(core_metrics, indent=4),
                    ads_json=json.dumps(ads_data, indent=4),
                    discount_json=json.dumps(discount_data, indent=4)
                )}
            ]
            
            llm_summary = self.llm.invoke(messages).content
            
            return BenchmarkOutput(
                bookings_comparison=bookings_comparison,
                revenue_comparison=revenue_comparison,
                rating_comparison=rating_comparison,
                ads_comparison=ads_comparison,
                discount_comparison=discount_comparison,
                llm_summary=llm_summary
            )
            
        except Exception as e:
            logger.error(f"Error analyzing benchmark performance: {str(e)}")
            traceback.print_exc()
            return self._get_empty_analysis()

    def _get_empty_analysis(self) -> BenchmarkOutput:
        """Return empty analysis when no data is available"""
        return BenchmarkOutput(
            bookings_comparison=BookingsComparison(total_bookings=0, total_peer_bookings=0, gap=0),
            revenue_comparison=RevenueComparison(total_revenue=0, total_peer_revenue=0, gap=0),
            rating_comparison=RatingComparison(rating=0, peer_rating=0, gap=0),
            ads_comparison=AdsComparison(avg_ad_spend=0, ads_roi=0, avg_ad_spend_peer=0, ads_roi_peer=0, gap_ads_roi=0, gap_ad_spend=0),
            discount_comparison=DiscountComparison(avg_discount_percentage=0, discount_roi=0, avg_discount_percentage_peer=0, discount_roi_peer=0, gap_discount_roi=0, gap_discount_percentage=0),
            llm_summary="No benchmark data available"
        )
    