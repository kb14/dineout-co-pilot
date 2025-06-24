from typing import Dict, Any
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI

from src.loaders import DataLoader
from src.agents.benchmark import BenchmarkAnalyzerAgent
from src.agents.ads import AdsAnalyzerAgent
from src.agents.discount import DiscountAnalyzerAgent
from src.agents.recommendations import RecommendationAgent
from src.agents.trends import TrendsAgent
from src.agents.report_formatter import ReportFormatterAgent
from src.utils.report_saver import ReportSaver

logger = logging.getLogger(__name__)

class ReportOrchestrator:
    def __init__(self, restaurant_id: str):
        """Initialize the report orchestrator."""
        self.restaurant_id = restaurant_id
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.data_loader = DataLoader()
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report for a restaurant."""
        try:
            # Step 1: Load all required data
            logger.info("Step 1: Loading data...")
            data = self.data_loader.load_data(self.restaurant_id)
            
            # Extract all dataframes
            master_df = data['master']
            metrics_df = data['metrics']
            ads_df = data['ads']
            discounts_df = data['discounts']
            benchmarks_df = data['benchmarks']

            # Step 2: Generate trends analysis
            logger.info("Step 2: Analyzing trends...")
            trends_agent = TrendsAgent(self.llm)
            trends_output = trends_agent.analyze(master_df, metrics_df, ads_df)

            # Step 3: Analyze ad performance
            logger.info("Step 3: Analyzing ad performance...")
            ads_agent = AdsAnalyzerAgent(self.llm)
            ads_output = ads_agent.analyze(master_df, metrics_df, ads_df)

            # Step 4: Analyze discount impact
            logger.info("Step 4: Analyzing discount impact...")
            discount_agent = DiscountAnalyzerAgent(self.llm)
            discount_output = discount_agent.analyze(master_df, metrics_df, discounts_df)

            # Step 5: Generate benchmark analysis
            logger.info("Step 5: Analyzing benchmark data...")
            benchmark_agent = BenchmarkAnalyzerAgent(self.llm)
            benchmark_output = benchmark_agent.analyze(benchmarks_df, trends_output, ads_output, discount_output)

            # Step 6: Generate recommendations
            logger.info("Step 6: Generating recommendations...")
            recommendation_agent = RecommendationAgent(self.llm)
            recommendation_output = recommendation_agent.generate_recommendations(
                trends_output, 
                ads_output, 
                discount_output, 
                benchmark_output
            )

            # Step 7: Format final report
            logger.info("Step 7: Formatting final report...")
            formatter = ReportFormatterAgent(self.llm)
            report_output = formatter.format_report(
                restaurant_info=master_df.iloc[0],
                trends_output=trends_output,
                ads_output=ads_output,
                discount_output=discount_output,
                benchmark_output=benchmark_output,
                recommendation_output=recommendation_output
            )
            
            # Step 8: Save report to disk
            logger.info("Step 8: Saving report to disk...")
            saver = ReportSaver(self.restaurant_id)
            file_paths = saver.save_report(report_output.markdown_report)
            
            # Compile final report
            report = {
                'restaurant_id': self.restaurant_id,
                'markdown_report': report_output.markdown_report,
                'generated_at': datetime.now().isoformat(),
                'markdown_path': file_paths['markdown_path'],
            }
            
            logger.info("Report generation completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise 