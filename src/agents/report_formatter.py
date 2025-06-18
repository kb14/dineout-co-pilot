from typing import Dict, Any, Union
import logging
import json
import pandas as pd
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from src.agents.trends import TrendsOutput
from src.agents.ads import AdsOutput
from src.agents.discount import DiscountOutput
from src.agents.benchmark import BenchmarkOutput
from src.agents.recommendations import RecommendationOutput
from src.prompts import REPORT_FORMATTER_SYSTEM_PROMPT, REPORT_FORMATTER_USER_PROMPT

logger = logging.getLogger(__name__)

class ReportOutput(BaseModel):
    """Output model for the formatted report."""
    markdown_report: str = Field(description="Final markdown formatted report")

class ReportFormatterAgent:
    """Agent responsible for formatting all analyses into a final markdown report."""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the report formatter agent.
        
        Args:
            llm: Language model for generating the formatted report
        """
        self.llm = llm
    
    def format_report(
        self,
        restaurant_info: pd.Series,
        trends_output: TrendsOutput,
        ads_output: AdsOutput,
        discount_output: DiscountOutput,
        benchmark_output: BenchmarkOutput,
        recommendation_output: RecommendationOutput
    ) -> ReportOutput:
        """Format all analyses into a final markdown report.
        
        Args:
            restaurant_info: Basic restaurant information (name, city, cuisine, etc.)
            trends_output: Output from trends analysis
            ads_output: Output from ads analysis
            discount_output: Output from discount analysis
            benchmark_output: Output from benchmark analysis
            recommendation_output: Output from recommendation analysis
            
        Returns:
            ReportOutput containing the final markdown formatted report
        """
        try:
            restaurant_info = restaurant_info.to_dict()
            
            # Prepare JSON sections for the prompt
            restaurant_info_json = {
                "name": restaurant_info.get("restaurant_name", ""),
                "city": restaurant_info.get("city", ""),
                "locality": restaurant_info.get("locality", ""),
                "cuisine": restaurant_info.get("cuisine", "")
            }
            
            recent_performance_metrics_json = trends_output.model_dump()
            
            # Handle no ad campaigns case
            if ads_output.total_ad_days == 0:
                advertising_campaign_analysis_json = {
                    "summary": "No recent advertising campaigns",
                    # "peer_comparison": benchmark_output.ads_comparison.model_dump()
                }
            else:
                advertising_campaign_analysis_json = ads_output.model_dump()
            
            # Handle no discounts case
            if discount_output.total_discount_days == 0:
                discount_strategy_analysis_json = {
                    "summary": "No recent discount campaigns",
                    # "peer_comparison": benchmark_output.discount_comparison.model_dump()
                }
            else:
                discount_strategy_analysis_json = discount_output.model_dump()
            
            peer_benchmarking_summary_json = benchmark_output.model_dump()
            recommended_next_steps_json = {
                "bullets": recommendation_output.llm_summary.split("\n")
            }
            
            # Build messages for the LLM
            messages = [
                {"role": "system", "content": REPORT_FORMATTER_SYSTEM_PROMPT},
                {"role": "user", "content": REPORT_FORMATTER_USER_PROMPT.format(
                    restaurant_info_json=json.dumps(restaurant_info_json, indent=4),
                    recent_performance_metrics_json=json.dumps(recent_performance_metrics_json, indent=4),
                    advertising_campaign_analysis_json=json.dumps(advertising_campaign_analysis_json, indent=4),
                    discount_strategy_analysis_json=json.dumps(discount_strategy_analysis_json, indent=4),
                    peer_benchmarking_summary_json=json.dumps(peer_benchmarking_summary_json, indent=4),
                    recommended_next_steps_json=json.dumps(recommended_next_steps_json, indent=4)
                )}
            ]
            
            # Generate the markdown report
            markdown_report = self.llm.invoke(messages).content
            
            return ReportOutput(markdown_report=markdown_report)
            
        except Exception as e:
            logger.error(f"Error formatting report: {str(e)}")
            return ReportOutput(
                markdown_report="# Error Generating Report\n\nThere was an error while generating the report. Please try again."
            ) 