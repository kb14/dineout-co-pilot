import pandas as pd
import logging
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.agents.analyst import AnalystAgent
from src.prompts import DISCOUNT_PERFORMANCE_PROMPT, ANALYST_OUTPUT_INSTRUCTIONS
import traceback

logger = logging.getLogger(__name__)

RELEVANT_TABLES = "restaurant_metrics, discount_history"

class DiscountOutput(BaseModel):
    """Schema for discount analysis output"""
    total_discount_days: int = Field(description="Total days with active discounts")
    avg_discount_percent: float = Field(description="Average discount percentage")
    roi: float = Field(description="ROI from discount campaigns")
    discount_analysis: str = Field(description="Analysis of discount performance")

class DiscountAnalyzerAgent:
    """Agent to analyze discount performance and generate insights"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def analyze(self, master_df: pd.DataFrame, metrics_df: pd.DataFrame, discounts_df: pd.DataFrame) -> DiscountOutput:
        """Analyze discount performance and generate insights"""
        try:
            if discounts_df.empty:
                return self._get_empty_analysis()

            restaurant_id = master_df['restaurant_id'].iloc[0]
            
            analyst_agent = AnalystAgent(self.llm)
            discount_analysis = analyst_agent.run_analysis(DISCOUNT_PERFORMANCE_PROMPT.format(
                restaurant_id=restaurant_id, 
                tables=RELEVANT_TABLES,
                output_format=ANALYST_OUTPUT_INSTRUCTIONS
            ))

            total_discount_days = (discounts_df['end_date'] - discounts_df['start_date']).dt.days.sum() + len(discounts_df)

            return DiscountOutput(
                total_discount_days=total_discount_days,
                avg_discount_percent=discounts_df['discount_percent'].mean(),
                roi=discounts_df['roi_from_discount'].mean(),
                discount_analysis=discount_analysis,
            )

        except Exception as e:
            logger.error(f"Error analyzing discount performance: {str(e)}")
            traceback.print_exc()
            return self._get_empty_analysis()

    def _get_empty_analysis(self) -> DiscountOutput:
        """Return empty analysis when no data is available"""
        return DiscountOutput(
            total_discount_days=0,
            avg_discount_percent=0,
            roi=0,
            discount_analysis="No discount data available",
        ) 