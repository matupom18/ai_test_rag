import logging
from typing import Dict, Any, Union
from pathlib import Path

from app.config import config
from app.schemas import RouterDecision, QAAnswer, IssueSummary
from app.llm_client import llm_client
from .qa_tool import qa_tool
from .issue_summary_tool import issue_summary_tool

logger = logging.getLogger(__name__)


class RouterAgent:
    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load router prompt template."""
        prompt_path = Path(__file__).parent / "prompts" / "router_prompt.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading router prompt: {e}")
            raise

    def _route_query(self, query: str) -> RouterDecision:
        """Decide which tool to use for the given query."""
        try:
            logger.info(f"Routing query: {query}")

            # Build prompt
            prompt = self.prompt_template.replace("{{query}}", query)

            # Generate routing decision
            messages = [{"role": "user", "content": prompt}]
            response = llm_client.generate_structured_response(messages)

            if not response:
                logger.error("Failed to generate routing decision")
                # Default to QA tool
                return RouterDecision(
                    tool="qa",
                    rationale="Unable to determine appropriate tool, defaulting to QA.",
                    tool_input={"query": query},
                )

            # Validate tool
            tool = response.get("tool", "qa")
            if tool not in ["qa", "issue_summary"]:
                logger.warning(f"Invalid tool '{tool}', defaulting to qa")
                tool = "qa"

            # Extract and validate tool_input
            tool_input = response.get("tool_input", {})
            if tool == "qa":
                if "query" not in tool_input:
                    tool_input["query"] = query
            elif tool == "issue_summary":
                if "issue_text" not in tool_input:
                    tool_input["issue_text"] = query

            rationale = response.get("rationale", "No rationale provided")

            logger.info(f"Router decision: {tool} - {rationale}")

            return RouterDecision(tool=tool, rationale=rationale, tool_input=tool_input)

        except Exception as e:
            logger.error(f"Error in router agent: {e}")
            # Default to QA tool
            return RouterDecision(
                tool="qa",
                rationale="Error in routing, defaulting to QA.",
                tool_input={"query": query},
            )

    def _execute_tool(self, decision: RouterDecision) -> Union[QAAnswer, IssueSummary]:
        """Execute the selected tool based on the routing decision."""
        try:
            if decision.tool == "qa":
                query = decision.tool_input.get("query", "")
                return qa_tool.answer_question(query)
            elif decision.tool == "issue_summary":
                issue_text = decision.tool_input.get("issue_text", "")
                return issue_summary_tool.summarize_issue(issue_text)
            else:
                raise ValueError(f"Unknown tool: {decision.tool}")

        except Exception as e:
            logger.error(f"Error executing tool {decision.tool}: {e}")
            # Return a safe default response
            if decision.tool == "qa":
                query = decision.tool_input.get("query", "")
                return QAAnswer(
                    query=query,
                    answer="เกิดข้อผิดพลาดในการประมวลผล",
                    sources=[],
                    confidence=0.0,
                )
            else:
                issue_text = decision.tool_input.get("issue_text", "")
                return IssueSummary(
                    raw_text=issue_text,
                    reported_issues=[],
                    affected_components=[],
                    severity="Low",
                    suggestions=[],
                )

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query through routing and tool execution."""
        try:
            # Route the query
            decision = self._route_query(query)

            # Execute the selected tool
            result = self._execute_tool(decision)

            return {"decision": decision.dict(), "result": result.dict()}

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "decision": RouterDecision(
                    tool="qa",
                    rationale="Error occurred, falling back to QA tool.",
                    tool_input={"query": query},
                ).dict(),
                "result": QAAnswer(
                    query=query,
                    answer="เกิดข้อผิดพลาดในการประมวลผล",
                    sources=[],
                    confidence=0.0,
                ).dict(),
            }


# Global instance
router_agent = RouterAgent()
