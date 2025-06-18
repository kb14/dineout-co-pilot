from pathlib import Path
import logging
from typing import Dict
from markdown_pdf import MarkdownPdf, Section

logger = logging.getLogger(__name__)

class ReportSaver:
    """Handles saving reports to disk in both markdown and PDF formats."""
    
    def __init__(self, restaurant_id: str):

        self.restaurant_id = restaurant_id
        self.output_dir = Path("outputs") / restaurant_id
        

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        

    def _save_markdown(self, markdown_content: str) -> Path:
        """Save markdown content to file.
        """
        md_path = self.output_dir / "report.md"
        md_path.write_text(markdown_content, encoding="utf-8")
        return md_path
    

    def save_report(self, markdown_content: str) -> Dict[str, str]:
        """Save report in markdown format.
        """
        try:
            self._ensure_output_dir()
            
            # Save markdown
            md_path = self._save_markdown(markdown_content)
            logger.info(f"Saved markdown report to {md_path}")
            # Return paths
            paths = {
                "markdown_path": str(md_path.resolve())
            }
            return paths
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            raise 