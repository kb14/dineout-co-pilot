#!/usr/bin/env python3
import typer
from dotenv import load_dotenv
import sys
from pathlib import Path
from datetime import datetime
import traceback

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.orchestrator import ReportOrchestrator

# Load environment variables
load_dotenv()

app = typer.Typer()


@app.command()
def generate_report(
    restaurant_id: str = typer.Argument(..., help="Restaurant ID to generate report for"),
):
    """
    Generate a comprehensive report for a restaurant using AI analysis and print the results.
    """
    try:
        # Initialize orchestrator
        orchestrator = ReportOrchestrator(restaurant_id)
        
        # Generate report
        report = orchestrator.generate_report()
        
            
    except Exception as e:
        traceback.print_exc()
        typer.echo(f"Error generating report: {str(e)}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 