"""
Structural Evaluator for validating report format and required elements.

This evaluator performs basic sanity checks on the generated markdown reports
to ensure they contain all required sections and follow the expected structure.
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime


class EvalResult(Enum):
    """Evaluation result types"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass
class StructuralEvalResult:
    """Results from structural evaluation"""
    overall_score: float  # 0.0 to 1.0
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    detailed_results: Dict[str, Dict[str, Any]]
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the evaluation"""
        return (f"Structural Evaluation: {self.passed_checks}/{self.total_checks} checks passed "
                f"(Score: {self.overall_score:.2f})")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization"""
        result_dict = asdict(self)
        
        # Convert enum values to strings for JSON serialization
        for category, checks in result_dict["detailed_results"].items():
            for check_name, check_result in checks.items():
                if isinstance(check_result["status"], EvalResult):
                    check_result["status"] = check_result["status"].value
        
        # Add metadata
        result_dict["evaluation_type"] = "structural"
        result_dict["timestamp"] = datetime.now().isoformat()
        
        return result_dict


class StructuralEvaluator:
    """
    Evaluates the structural integrity and format compliance of generated reports.
    
    Checks for:
    - Required sections presence
    - Proper markdown formatting
    - Executive summary components
    - Table structure
    - Chart references
    - Currency formatting
    """
    
    def __init__(self):
        self.required_sections = [
            "🚨 Executive Summary",
            "Recent Performance Metrics",
            "Advertising Campaign Effectiveness", 
            "Discount Strategy Performance",
            "Peer Benchmarking Summary",
            "Recommendations"
        ]
        
        self.required_subsections = [
            "Cuisine and Locality",
            "KEY SALES METRICS"
        ]
        
        self.executive_summary_components = [
            "Status",
            "Key Alert", 
            "Top Priority"
        ]
        
        self.status_values = ["HEALTHY", "ATTENTION", "URGENT"]
    
    def evaluate(self, report_content: str, restaurant_id: str = None) -> StructuralEvalResult:
        """
        Perform comprehensive structural evaluation of a report.
        
        Args:
            report_content: The markdown content of the report
            restaurant_id: Optional restaurant ID for context
            
        Returns:
            StructuralEvalResult with detailed evaluation results
        """
        detailed_results = {}
        
        # Run all evaluation checks
        detailed_results["sections"] = self._check_required_sections(report_content)
        detailed_results["executive_summary"] = self._check_executive_summary(report_content)
        detailed_results["tables"] = self._check_table_structure(report_content)
        detailed_results["charts"] = self._check_chart_references(report_content)
        detailed_results["formatting"] = self._check_markdown_formatting(report_content)
        detailed_results["content_quality"] = self._check_content_quality(report_content)
        
        # Calculate overall score
        total_checks = 0
        passed_checks = 0
        warnings = 0
        
        for category, results in detailed_results.items():
            for check, result in results.items():
                total_checks += 1
                if result["status"] == EvalResult.PASS:
                    passed_checks += 1
                elif result["status"] == EvalResult.WARN:
                    warnings += 1
        
        failed_checks = total_checks - passed_checks - warnings
        overall_score = passed_checks / total_checks if total_checks > 0 else 0.0
        
        return StructuralEvalResult(
            overall_score=overall_score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            detailed_results=detailed_results
        )
    
    def _check_required_sections(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Check if all required sections are present"""
        results = {}
        
        for section in self.required_sections:
            present = section in content
            results[f"has_{section.lower().replace(' ', '_').replace('🚨_', '').replace('_-_', '_')}"] = {
                "status": EvalResult.PASS if present else EvalResult.FAIL,
                "description": f"Section '{section}' is present",
                "expected": True,
                "actual": present
            }
        
        for subsection in self.required_subsections:
            present = subsection in content
            results[f"has_{subsection.lower().replace(' ', '_')}"] = {
                "status": EvalResult.PASS if present else EvalResult.FAIL,
                "description": f"Subsection '{subsection}' is present",
                "expected": True,
                "actual": present
            }
        
        return results
    
    def _check_executive_summary(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Check executive summary components"""
        results = {}
        
        # Check if executive summary section exists
        has_exec_summary = "🚨 Executive Summary" in content
        results["has_executive_summary_section"] = {
            "status": EvalResult.PASS if has_exec_summary else EvalResult.FAIL,
            "description": "Executive Summary section exists",
            "expected": True,
            "actual": has_exec_summary
        }
        
        if has_exec_summary:
            # Extract executive summary content
            exec_match = re.search(r'## 🚨 Executive Summary\n(.*?)\n## ', content, re.DOTALL)
            exec_content = exec_match.group(1) if exec_match else ""
            
            # Check for required components
            for component in self.executive_summary_components:
                has_component = f"**{component}**:" in exec_content
                results[f"has_{component.lower().replace(' ', '_')}"] = {
                    "status": EvalResult.PASS if has_component else EvalResult.FAIL,
                    "description": f"Executive summary has {component} component",
                    "expected": True,
                    "actual": has_component
                }
            
            # Check for valid status value
            has_valid_status = any(status in exec_content for status in self.status_values)
            results["has_valid_status_value"] = {
                "status": EvalResult.PASS if has_valid_status else EvalResult.FAIL,
                "description": f"Status is one of {self.status_values}",
                "expected": True,
                "actual": has_valid_status
            }
        
        return results
    
    def _check_table_structure(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Check table formatting and structure"""
        results = {}
        
        # Check for KEY SALES METRICS table
        has_key_metrics_table = "**KEY SALES METRICS**" in content
        results["has_key_metrics_table"] = {
            "status": EvalResult.PASS if has_key_metrics_table else EvalResult.FAIL,
            "description": "KEY SALES METRICS table is present",
            "expected": True,
            "actual": has_key_metrics_table
        }
        
        # Check for OPD labeling
        has_opd_label = "**OPD (Orders Per Day)**" in content
        results["has_opd_labeling"] = {
            "status": EvalResult.PASS if has_opd_label else EvalResult.FAIL,
            "description": "OPD (Orders Per Day) is properly labeled",
            "expected": True,
            "actual": has_opd_label
        }
        
        # Check for Spend Per Cover metric
        has_spend_per_cover = "**Spend Per Cover**" in content
        results["has_spend_per_cover"] = {
            "status": EvalResult.PASS if has_spend_per_cover else EvalResult.FAIL,
            "description": "Spend Per Cover metric is present",
            "expected": True,
            "actual": has_spend_per_cover
        }
        
        # Check for proper table formatting (markdown tables)
        table_pattern = r'\|.*\|.*\n\|[-:]*\|[-:]*\|\n(\|.*\|.*\n)+'
        table_count = len(re.findall(table_pattern, content))
        has_proper_tables = table_count >= 3  # Should have at least 3 tables
        results["has_proper_table_formatting"] = {
            "status": EvalResult.PASS if has_proper_tables else EvalResult.WARN,
            "description": f"Found {table_count} properly formatted markdown tables",
            "expected": ">=3",
            "actual": table_count
        }
        
        return results
    
    def _check_chart_references(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Check chart references and image links"""
        results = {}
        
        # Check for chart reference
        chart_pattern = r'!\[.*\]\(plots/.*\.png\)'
        has_chart_ref = bool(re.search(chart_pattern, content))
        results["has_chart_reference"] = {
            "status": EvalResult.PASS if has_chart_ref else EvalResult.FAIL,
            "description": "Chart reference with proper path is present",
            "expected": True,
            "actual": has_chart_ref
        }
        
        # Check for bookings chart specifically
        has_bookings_chart = "![Bookings Rolling 7-Day](plots/bookings_rolling_7day.png)" in content
        results["has_bookings_chart"] = {
            "status": EvalResult.PASS if has_bookings_chart else EvalResult.FAIL,
            "description": "Bookings rolling 7-day chart is present",
            "expected": True,
            "actual": has_bookings_chart
        }
        
        return results
    
    def _check_markdown_formatting(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Check markdown syntax and formatting"""
        results = {}
        
        # Check for proper header hierarchy
        header_pattern = r'^#{1,6} .+'
        headers = re.findall(header_pattern, content, re.MULTILINE)
        has_headers = len(headers) >= 5  # Should have multiple headers
        results["has_proper_headers"] = {
            "status": EvalResult.PASS if has_headers else EvalResult.WARN,
            "description": f"Found {len(headers)} markdown headers",
            "expected": ">=5",
            "actual": len(headers)
        }
        
        # Check for currency formatting
        currency_pattern = r'₹[\d,]+\.?\d*'
        currency_matches = re.findall(currency_pattern, content)
        has_currency = len(currency_matches) >= 3  # Should have multiple currency values
        results["has_proper_currency_formatting"] = {
            "status": EvalResult.PASS if has_currency else EvalResult.WARN,
            "description": f"Found {len(currency_matches)} properly formatted currency values",
            "expected": ">=3",
            "actual": len(currency_matches)
        }
        
        # Check for bold formatting on key metrics
        bold_metrics = ["**Status**", "**Key Alert**", "**Top Priority**", "**OPD (Orders Per Day)**"]
        bold_count = sum(1 for metric in bold_metrics if metric in content)
        has_bold_formatting = bold_count >= 3
        results["has_bold_key_metrics"] = {
            "status": EvalResult.PASS if has_bold_formatting else EvalResult.WARN,
            "description": f"Found {bold_count} properly bolded key metrics",
            "expected": ">=3",
            "actual": bold_count
        }
        
        return results
    
    def _check_content_quality(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Check basic content quality indicators"""
        results = {}
        
        # Check report length (should be substantial but not too long)
        word_count = len(content.split())
        is_appropriate_length = 200 <= word_count <= 2000
        results["appropriate_length"] = {
            "status": EvalResult.PASS if is_appropriate_length else EvalResult.WARN,
            "description": f"Report has appropriate length ({word_count} words)",
            "expected": "200-2000 words",
            "actual": f"{word_count} words"
        }
        
        # Check for placeholder text or obvious errors
        error_indicators = ["TODO", "PLACEHOLDER", "ERROR", "FAILED", "undefined", "null"]
        has_errors = any(indicator.lower() in content.lower() for indicator in error_indicators)
        results["no_placeholder_text"] = {
            "status": EvalResult.FAIL if has_errors else EvalResult.PASS,
            "description": "No placeholder text or error indicators found",
            "expected": False,
            "actual": has_errors
        }
        
        # Check for restaurant name in title
        title_match = re.search(r'^# (.+) - Performance Summary', content, re.MULTILINE)
        has_restaurant_title = bool(title_match and len(title_match.group(1).strip()) > 0)
        results["has_restaurant_name_in_title"] = {
            "status": EvalResult.PASS if has_restaurant_title else EvalResult.FAIL,
            "description": "Restaurant name is present in title",
            "expected": True,
            "actual": has_restaurant_title
        }
        
        return results
    
    def print_detailed_results(self, eval_result: StructuralEvalResult):
        """Print a detailed, human-readable evaluation report"""
        print(f"\n{'='*60}")
        print(f"STRUCTURAL EVALUATION REPORT")
        print(f"{'='*60}")
        print(f"Overall Score: {eval_result.overall_score:.2f} ({eval_result.passed_checks}/{eval_result.total_checks} checks passed)")
        print(f"Failed: {eval_result.failed_checks}, Warnings: {eval_result.warnings}")
        
        for category, checks in eval_result.detailed_results.items():
            print(f"\n📋 {category.upper()}:")
            for check_name, check_result in checks.items():
                status_icon = "✅" if check_result["status"] == EvalResult.PASS else "❌" if check_result["status"] == EvalResult.FAIL else "⚠️"
                print(f"  {status_icon} {check_result['description']}")
                if check_result["status"] != EvalResult.PASS:
                    print(f"     Expected: {check_result['expected']}, Got: {check_result['actual']}")
        
        print(f"\n{'='*60}")