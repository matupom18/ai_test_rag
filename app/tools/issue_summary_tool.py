import logging
from typing import Dict, Any
from pathlib import Path

from app.config import config
from app.schemas import IssueSummary
from app.llm_client import llm_client

logger = logging.getLogger(__name__)


class IssueSummaryTool:
    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load issue summary prompt template."""
        prompt_path = Path(__file__).parent / "prompts" / "issue_summary_prompt.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading issue summary prompt: {e}")
            raise

    def summarize_issue(self, issue_text: str) -> IssueSummary:
        """Summarize an issue text into structured fields."""
        try:
            logger.info(f"Processing issue summary for text: {issue_text[:100]}...")

            # Build prompt
            prompt = self.prompt_template.replace("{{issue_text}}", issue_text)

            # Generate response
            messages = [{"role": "user", "content": prompt}]
            response = llm_client.generate_structured_response(messages)

            if not response:
                logger.error("Failed to generate LLM response for issue summary")
                return IssueSummary(
                    raw_text=issue_text,
                    reported_issues=[],
                    affected_components=[],
                    severity="Low",
                    suggestions=[],
                )

            # Extract fields with defaults
            reported_issues = response.get("reported_issues", [])
            affected_components = response.get("affected_components", [])
            severity = response.get("severity", "Low")
            suggestions = response.get("suggestions", [])

            # Validate severity
            valid_severities = ["Low", "Medium", "High", "Critical"]
            if severity not in valid_severities:
                severity = "Low"
                logger.warning(f"Invalid severity '{severity}', defaulting to Low")

            logger.info(f"Generated issue summary with severity: {severity}")

            return IssueSummary(
                raw_text=issue_text,
                reported_issues=reported_issues,
                affected_components=affected_components,
                severity=severity,
                suggestions=suggestions,
            )

        except Exception as e:
            logger.error(f"Error in issue summary tool: {e}")
            return IssueSummary(
                raw_text=issue_text,
                reported_issues=[],
                affected_components=[],
                severity="Low",
                suggestions=[],
            )


# Global instance
issue_summary_tool = IssueSummaryTool()
