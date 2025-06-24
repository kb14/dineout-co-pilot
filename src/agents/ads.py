import pandas as pd
import logging
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.agents.analyst import AnalystAgent
from src.prompts import ADS_PERFORMANCE_PROMPT, ANALYST_OUTPUT_INSTRUCTIONS
import traceback

logger = logging.getLogger(__name__)


RELEVANT_TABLES = "restaurant_metrics, ads_data"

class AdsOutput(BaseModel):
    """Schema for ads analysis output"""
    total_ad_days: int = Field(description="Total ad days across all campaigns")
    total_spend: float = Field(description="Total ad spend across all campaigns")
    total_impressions: int = Field(description="Total ad impressions")
    total_clicks: int = Field(description="Total ad clicks")
    total_conversions: int = Field(description="Total conversions from ads")
    conversion_rate: float = Field(description="Conversion rate from clicks to bookings (percentage)")
    total_revenue_generated: float = Field(description="Total revenue from ad campaigns")
    roi: float = Field(description="ROI from ad campaigns")
    campaign_analysis: str = Field(description="Campaign analysis of ad performance")
    # llm_summary: str = Field(description="LLM generated insights on ad performance")

class AdsAnalyzerAgent:
    """Agent to analyze ad performance and generate insights"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def analyze(self, master_df: pd.DataFrame, metrics_df: pd.DataFrame, ads_df: pd.DataFrame) -> AdsOutput:
        """Analyze ad performance and generate insights"""
        try:
            if ads_df.empty:
                return self._get_empty_analysis()

            restaurant_id = master_df['restaurant_id'].iloc[0]

            analyst_agent = AnalystAgent(self.llm)
            campaign_analysis = analyst_agent.run_analysis(ADS_PERFORMANCE_PROMPT.format(
                restaurant_id=restaurant_id, 
                tables=RELEVANT_TABLES, 
                output_format=ANALYST_OUTPUT_INSTRUCTIONS
            ))

            # Add 1 to include both start and end dates
            total_ad_days = (ads_df['campaign_end'] - ads_df['campaign_start']).dt.days.sum() + len(ads_df)

            ads_output = AdsOutput(
                total_ad_days=total_ad_days,
                total_spend=ads_df['spend'].sum(),
                total_impressions=ads_df['impressions'].sum(),
                total_clicks=ads_df['clicks'].sum(),
                total_conversions=ads_df['conversions'].sum(),
                conversion_rate=(ads_df['conversions'].sum() / ads_df['clicks'].sum() * 100) if ads_df['clicks'].sum() > 0 else 0,
                total_revenue_generated=ads_df['revenue_generated'].sum(),
                roi=ads_df['revenue_generated'].sum() / ads_df['spend'].sum() if ads_df['spend'].sum() > 0 else 0,
                campaign_analysis=campaign_analysis,
                # llm_summary=""  # TODO: Implement LLM insights
            )

            return ads_output

        except Exception as e:
            logger.error(f"Error analyzing ad performance: {str(e)}")
            traceback.print_exc()
            return self._get_empty_analysis()

    def _get_empty_analysis(self) -> AdsOutput:
        """Return empty analysis when no data is available"""
        return AdsOutput(
            total_ad_days=0,
            total_spend=0,
            total_impressions=0,
            total_clicks=0,
            total_conversions=0,
            conversion_rate=0,
            total_revenue_generated=0,
            roi=0,
            campaign_analysis="No campaign data available",
            # llm_summary="No campaign data available"
        )

