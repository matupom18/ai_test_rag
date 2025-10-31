import logging
from typing import List, Dict, Any
from pathlib import Path

from app.config import config
from app.schemas import QAAnswer
from app.vectordb import vector_db
from app.llm_client import llm_client

logger = logging.getLogger(__name__)


class QATool:
    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load QA prompt template."""
        prompt_path = Path(__file__).parent / "prompts" / "qa_prompt.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading QA prompt: {e}")
            raise

    def _format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results with source tags."""
        context_parts = []

        for result in search_results:
            source = result["metadata"].get("source", "unknown")
            chunk_id = result["metadata"].get("chunk_id", "unknown")
            text = result["text"]

            # Format with clear source tags
            context_parts.append(f"[{source}:{chunk_id}]\n{text}")

        return "\n\n".join(context_parts)

    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on similarity scores."""
        if not search_results:
            return 0.0

        # Use average similarity as confidence heuristic
        similarities = [result["similarity"] for result in search_results]
        avg_similarity = sum(similarities) / len(similarities)

        # Scale to 0-1 range, with some adjustments
        confidence = min(max(avg_similarity * 1.2, 0.1), 1.0)
        return round(confidence, 2)

    def _extract_sources(self, search_results: List[Dict[str, Any]]) -> List[str]:
        """Extract source references from search results."""
        sources = []
        for result in search_results:
            source = result["metadata"].get("source", "unknown")
            chunk_id = result["metadata"].get("chunk_id", "unknown")
            sources.append(f"{source}:{chunk_id}")
        return sources

    def answer_question(self, query: str) -> QAAnswer:
        """Answer a question using document search."""
        try:
            logger.info(f"Processing QA query: {query}")

            # Search for relevant documents
            search_results = vector_db.search(query, top_k=config.TOP_K)

            if not search_results:
                logger.warning("No search results found")
                return QAAnswer(
                    query=query, answer="ไม่พบข้อมูลเพียงพอ", sources=[], confidence=0.0
                )

            # Format context
            context = self._format_context(search_results)
            logger.debug(f"Retrieved context length: {len(context)}")

            # Build prompt
            prompt = self.prompt_template.replace("{{question}}", query)
            prompt = prompt.replace("{{context}}", context)

            # Generate response
            messages = [{"role": "user", "content": prompt}]
            response = llm_client.generate_structured_response(messages)

            if not response:
                logger.error("Failed to generate LLM response")
                return QAAnswer(
                    query=query,
                    answer="ไม่พบข้อมูลเพียงพอ",
                    sources=self._extract_sources(search_results),
                    confidence=0.1,
                )

            # Extract answer and metadata
            answer = response.get("answer", "ไม่พบข้อมูลเพียงพอ")
            confidence = self._calculate_confidence(search_results)
            sources = self._extract_sources(search_results)

            logger.info(f"Generated answer with confidence: {confidence}")

            return QAAnswer(
                query=query, answer=answer, sources=sources, confidence=confidence
            )

        except Exception as e:
            logger.error(f"Error in QA tool: {e}")
            return QAAnswer(
                query=query,
                answer="เกิดข้อผิดพลาดในการประมวลผล",
                sources=[],
                confidence=0.0,
            )


# Global instance
qa_tool = QATool()
