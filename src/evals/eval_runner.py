"""
Evaluation runner for testing report quality across different evaluators.

This script can be used to run evaluations on existing reports or as part of
a continuous integration pipeline.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse
import json
from datetime import datetime

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.evals.evaluators.structural import StructuralEvaluator


class EvalRunner:
    """Main evaluation runner that orchestrates different evaluators"""
    
    def __init__(self):
        self.structural_evaluator = StructuralEvaluator()
    
    def save_eval_result(self, result: Dict[str, Any], restaurant_id: str, eval_type: str = "structural"):
        """Save evaluation result to the restaurant's evals directory"""
        if not result["success"]:
            return
        
        # Create evals directory
        evals_dir = Path("outputs") / restaurant_id / "evals"
        evals_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON result
        output_file = evals_dir / f"{eval_type}_eval.json"
        eval_dict = result["result"].to_dict()
        eval_dict["restaurant_id"] = restaurant_id
        eval_dict["report_path"] = result["report_path"]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(eval_dict, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Evaluation results saved to {output_file}")
    
    def run_structural_eval(self, report_path: str, restaurant_id: str = None, save_results: bool = False) -> Dict[str, Any]:
        """Run structural evaluation on a report file"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            result = self.structural_evaluator.evaluate(report_content, restaurant_id)
            eval_result = {
                "success": True,
                "result": result,
                "report_path": report_path
            }
            
            # Save results if requested and restaurant_id is available
            if save_results and restaurant_id:
                self.save_eval_result(eval_result, restaurant_id)
            
            return eval_result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "report_path": report_path
            }
    
    def run_batch_structural_eval(self, reports_dir: str = "outputs", save_results: bool = False) -> Dict[str, Any]:
        """Run structural evaluation on all reports in the outputs directory"""
        outputs_path = Path(reports_dir)
        results = {}
        summary = {"total": 0, "passed": 0, "failed": 0, "avg_score": 0.0}
        
        print(f"🔍 Running structural evaluation on reports in {outputs_path}")
        
        for restaurant_dir in outputs_path.iterdir():
            if restaurant_dir.is_dir() and restaurant_dir.name.startswith('R'):
                restaurant_id = restaurant_dir.name
                report_path = restaurant_dir / "report.md"
                
                if report_path.exists():
                    print(f"\n📊 Evaluating {restaurant_id}...")
                    eval_result = self.run_structural_eval(str(report_path), restaurant_id, save_results)
                    results[restaurant_id] = eval_result
                    
                    summary["total"] += 1
                    if eval_result["success"]:
                        score = eval_result["result"].overall_score
                        summary["avg_score"] += score
                        if score >= 0.8:  # 80% threshold for "passing"
                            summary["passed"] += 1
                        else:
                            summary["failed"] += 1
                        
                        # Print brief summary
                        result = eval_result["result"]
                        print(f"   Score: {score:.2f} ({result.passed_checks}/{result.total_checks} checks)")
                        if result.failed_checks > 0:
                            print(f"   ❌ {result.failed_checks} failed checks")
                        if result.warnings > 0:
                            print(f"   ⚠️  {result.warnings} warnings")
                    else:
                        summary["failed"] += 1
                        print(f"   ❌ Evaluation failed: {eval_result['error']}")
        
        if summary["total"] > 0:
            summary["avg_score"] /= summary["total"]
        
        return {"results": results, "summary": summary}
    
    def print_batch_summary(self, batch_result: Dict[str, Any]):
        """Print a summary of batch evaluation results"""
        summary = batch_result["summary"]
        results = batch_result["results"]
        
        print(f"\n{'='*60}")
        print(f"BATCH EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Reports: {summary['total']}")
        print(f"Passed (≥80%): {summary['passed']}")
        print(f"Failed (<80%): {summary['failed']}")
        print(f"Average Score: {summary['avg_score']:.2f}")
        
        # Show top performers and problem reports
        if results:
            scored_results = []
            for restaurant_id, result in results.items():
                if result["success"]:
                    score = result["result"].overall_score
                    scored_results.append((restaurant_id, score, result["result"]))
            
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\n🏆 TOP PERFORMERS:")
            for restaurant_id, score, result in scored_results[:3]:
                print(f"  {restaurant_id}: {score:.2f} ({result.passed_checks}/{result.total_checks})")
            
            print(f"\n⚠️  NEEDS ATTENTION:")
            for restaurant_id, score, result in scored_results[-3:]:
                if score < 0.8:
                    print(f"  {restaurant_id}: {score:.2f} ({result.failed_checks} failed, {result.warnings} warnings)")
        
        print(f"{'='*60}")


def main():
    """Main entry point for evaluation runner"""
    parser = argparse.ArgumentParser(description="Run evaluations on restaurant reports")
    parser.add_argument("--report", "-r", help="Path to specific report file")
    parser.add_argument("--restaurant-id", "-id", help="Restaurant ID for context")
    parser.add_argument("--batch", "-b", action="store_true", help="Run batch evaluation on all reports")
    parser.add_argument("--outputs-dir", "-o", default="outputs", help="Directory containing report outputs")
    parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed results")
    parser.add_argument("--save-results", "-s", action="store_true", help="Save evaluation results to files")
    
    args = parser.parse_args()
    
    runner = EvalRunner()
    
    if args.batch:
        # Run batch evaluation
        batch_result = runner.run_batch_structural_eval(args.outputs_dir, args.save_results)
        runner.print_batch_summary(batch_result)
        
        if args.detailed:
            print(f"\nDETAILED RESULTS:")
            for restaurant_id, result in batch_result["results"].items():
                if result["success"]:
                    print(f"\n🏪 {restaurant_id}:")
                    runner.structural_evaluator.print_detailed_results(result["result"])
    
    elif args.report:
        # Run evaluation on specific report
        result = runner.run_structural_eval(args.report, args.restaurant_id, args.save_results)
        if result["success"]:
            print(f"✅ Evaluation completed for {args.report}")
            runner.structural_evaluator.print_detailed_results(result["result"])
        else:
            print(f"❌ Evaluation failed: {result['error']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()