from typing import Dict, Any, List
import logging
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from src.agents.trends import TrendsOutput
from src.agents.ads import AdsOutput
from src.agents.discount import DiscountOutput
from src.agents.benchmark import BenchmarkOutput
from src.prompts import RECOMMENDATION_SYSTEM_PROMPT, RECOMMENDATION_USER_PROMPT

logger = logging.getLogger(__name__)

class RawRecommendation(BaseModel):
    """Raw recommendation data before LLM formatting."""
    action: str = Field(description="The specific action to take")
    current_value: float = Field(description="Current metric value")
    target_value: float = Field(description="Target metric value")
    expected_impact: str = Field(description="Expected impact of taking the action")
    priority: int = Field(description="Priority score (1-5, 1 being highest)", ge=1, le=5)

class RecommendationOutput(BaseModel):
    """Output model for recommendations."""
    llm_summary: str = Field(description="LLM generated recommendations based on all analyses")

class RecommendationAgent:
    """Agent responsible for generating recommendations based on restaurant performance analysis."""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the recommendation agent.
        
        Args:
            llm: Language model for generating recommendations
        """
        self.llm = llm
    
    def _gap_to_priority(self, gap: float) -> int:
        """Convert a gap percentage to a priority score.
        
        Args:
            gap: Percentage difference vs peers (negative means lagging)
            
        Returns:
            Priority score (1-5, where 1 is highest priority)
        """
        if gap <= -25:
            return 1  # Substantial gap
        elif -25 < gap <= -15:
            return 2  # Material gap
        elif -15 < gap <= -5:
            return 3  # Noticeable gap
        else:
            return 5  # No significant gap

    def _get_ads_recommendations(
        self,
        ads_output: AdsOutput,
        benchmark_output: BenchmarkOutput
    ) -> List[RawRecommendation]:
        """Generate advertising-related recommendations."""
        recommendations = []
        ad_cmp = benchmark_output.ads_comparison

        # Case 1: No campaigns in last 30 days
        if ads_output.total_ad_days == 0:
            recommendations.append(
                RawRecommendation(
                    action="Launch a 30-day Ads campaign",
                    current_value=0,
                    target_value=ad_cmp.avg_ad_spend_peer,
                    expected_impact="Match peers' visibility; boost bookings by 10-15%",
                    priority=1
                )
            )
            return recommendations

        # Case 2: Spend low but ROI >= peers
        if ad_cmp.gap_ad_spend <= -15 and ad_cmp.gap_ads_roi >= 0:
            recommendations.append(
                RawRecommendation(
                    action="Scale ad spend",
                    current_value=ads_output.total_spend,
                    target_value=ad_cmp.avg_ad_spend_peer,
                    expected_impact="Maintain ROI, add incremental bookings",
                    priority=self._gap_to_priority(ad_cmp.gap_ad_spend)
                )
            )

        # Case 3: ROI lagging
        if ad_cmp.gap_ads_roi <= -15:
            recommendations.append(
                RawRecommendation(
                    action="Optimise creatives & targeting",
                    current_value=ads_output.roi,
                    target_value=ad_cmp.ads_roi_peer,
                    expected_impact="Lift ROI to peer level",
                    priority=self._gap_to_priority(ad_cmp.gap_ads_roi)
                )
            )

      
        return recommendations

    def _get_discount_recommendations(
        self, 
        discount_output: DiscountOutput,
        benchmark_output: BenchmarkOutput
    ) -> List[RawRecommendation]:
        """Generate discount-related recommendations."""
        recommendations = []
        disc_cmp = benchmark_output.discount_comparison

        # Case 1: No discounts and peers offer significant discounts
        if (discount_output.total_discount_days == 0 and 
            disc_cmp.avg_discount_percentage_peer >= 5):
            recommendations.append(
                RawRecommendation(
                    action=f"Introduce limited-time {disc_cmp.avg_discount_percentage_peer:.0f}% discount",
                    current_value=0,
                    target_value=disc_cmp.avg_discount_percentage_peer,
                    expected_impact="Stay competitive; lift conversions",
                    priority=2
                )
            )
            return recommendations

        # Case 2: Discount % high but ROI low
        if (disc_cmp.gap_discount_percentage >= 10 and 
            disc_cmp.gap_discount_roi <= -15):
            recommendations.append(
                RawRecommendation(
                    action=f"Reduce discount to ~{disc_cmp.avg_discount_percentage_peer:.0f}%",
                    current_value=discount_output.avg_discount_percent,
                    target_value=disc_cmp.avg_discount_percentage_peer,
                    expected_impact="Protect margin; improve ROI",
                    priority=self._gap_to_priority(disc_cmp.gap_discount_roi)
                )
            )

        # Case 3: Discount % low but ROI beats peers
        if (disc_cmp.gap_discount_percentage <= -15 and 
            disc_cmp.gap_discount_roi >= 0):
            recommendations.append(
                RawRecommendation(
                    action="Extend discount to peer level",
                    current_value=discount_output.avg_discount_percent,
                    target_value=disc_cmp.avg_discount_percentage_peer,
                    expected_impact=f"Scale proven {discount_output.avg_discount_percent:.0f}% discount that's driving good ROI",
                    priority=self._gap_to_priority(disc_cmp.gap_discount_percentage)
                )
            )


        return recommendations

    def _get_operational_recommendations(
        self,
        trends_output: TrendsOutput,
        benchmark_output: BenchmarkOutput
    ) -> List[RawRecommendation]:
        """Generate operational recommendations."""
        recommendations = []
        book_cmp = benchmark_output.bookings_comparison
        rev_cmp = benchmark_output.revenue_comparison
        rating_cmp = benchmark_output.rating_comparison

        # Case 1: Bookings significantly below peers
        if book_cmp.gap <= -5:
            recommendations.append(
                RawRecommendation(
                    action="Drive visibility (Ads + Discounts)",
                    current_value=book_cmp.total_bookings,
                    target_value=book_cmp.total_peer_bookings,
                    expected_impact=f"Close {abs(book_cmp.gap):.0f}% bookings gap vs peers",
                    priority=self._gap_to_priority(book_cmp.gap)
                )
            )

        # Case 2: Revenue gap (focus on per-booking value)
        if (rev_cmp.gap <= -15 and 
            abs(rev_cmp.gap) > abs(book_cmp.gap)):  # Revenue gap bigger than bookings gap
            recommendations.append(
                RawRecommendation(
                    action="Upsell higher-value menu items & combos",
                    current_value=rev_cmp.total_revenue,
                    target_value=rev_cmp.total_peer_revenue,
                    expected_impact=f"Close {abs(rev_cmp.gap):.0f}% revenue gap vs peers",
                    priority=self._gap_to_priority(rev_cmp.gap)
                )
            )

        # Case 3: Rating needs improvement
        if rating_cmp.gap <= -5:
            recommendations.append(
                RawRecommendation(
                    action="Improve service touchpoints & prompt reviews",
                    current_value=rating_cmp.rating,
                    target_value=rating_cmp.peer_rating,
                    expected_impact=f"Lift rating from {rating_cmp.rating:.1f} to {rating_cmp.peer_rating:.1f}",
                    priority=self._gap_to_priority(rating_cmp.gap)
                )
            )

        return recommendations

    def generate_recommendations(
        self,
        trends_output: TrendsOutput,
        ads_output: AdsOutput,
        discount_output: DiscountOutput,
        benchmark_output: BenchmarkOutput
    ) -> RecommendationOutput:
        """Generate prioritized recommendations based on all available analyses.
        """
        try:
            # Collect raw recommendations from each area
            raw_recommendations = []
            raw_recommendations.extend(self._get_ads_recommendations(ads_output, benchmark_output))
            raw_recommendations.extend(self._get_discount_recommendations(discount_output, benchmark_output))
            raw_recommendations.extend(self._get_operational_recommendations(trends_output, benchmark_output))

            # Sort by priority
            raw_recommendations.sort(key=lambda x: x.priority)

            # Convert to JSON for LLM
            recommendations_json = [r.model_dump() for r in raw_recommendations]

            # Build user prompt with additional context from campaign / discount analysis
            user_content = RECOMMENDATION_USER_PROMPT.format(
                recommendations_json=json.dumps(recommendations_json, indent=2)
            )
            user_content += "\n\nAdditional Context:\n\n### Ads Campaign Analysis\n" + ads_output.campaign_analysis + "\n\n### Discount Strategy Analysis\n" + discount_output.discount_analysis

            # Format recommendations using LLM
            messages = [
                {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
            
            formatted_recommendations = self.llm.invoke(messages).content.strip()
            return RecommendationOutput(llm_summary=formatted_recommendations)

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return RecommendationOutput(llm_summary="Error generating recommendations") 