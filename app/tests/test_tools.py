import pytest
from unittest.mock import patch, MagicMock

from app.tools.qa_tool import QATool, qa_tool
from app.tools.issue_summary_tool import IssueSummaryTool, issue_summary_tool
from app.tools.router_agent import RouterAgent, router_agent
from app.schemas import QAAnswer, IssueSummary, RouterDecision


class TestQATool:
    """Test cases for QA tool functionality."""

    @pytest.fixture
    def qa_tool_instance(self):
        """Create a QATool instance for testing."""
        return QATool()

    def test_load_prompt_success(self, qa_tool_instance):
        """Test successful prompt loading."""
        assert qa_tool_instance.prompt_template is not None
        assert "{{question}}" in qa_tool_instance.prompt_template
        assert "{{context}}" in qa_tool_instance.prompt_template

    def test_format_context(self, qa_tool_instance):
        """Test context formatting with source tags."""
        search_results = [
            {
                "metadata": {"source": "test_file.txt", "chunk_id": "chunk_0"},
                "text": "This is test content.",
                "similarity": 0.8,
                "id": "test_id_1",
                "distance": 0.2,
            },
            {
                "metadata": {"source": "another_file.txt", "chunk_id": "chunk_1"},
                "text": "More test content here.",
                "similarity": 0.7,
                "id": "test_id_2",
                "distance": 0.3,
            },
        ]

        formatted_context = qa_tool_instance._format_context(search_results)

        assert "[test_file.txt:chunk_0]" in formatted_context
        assert "[another_file.txt:chunk_1]" in formatted_context
        assert "This is test content." in formatted_context
        assert "More test content here." in formatted_context

    def test_calculate_confidence(self, qa_tool_instance):
        """Test confidence score calculation."""
        # High similarity results
        high_similarity = [
            {"similarity": 0.9},
            {"similarity": 0.8},
            {"similarity": 0.85},
        ]
        confidence = qa_tool_instance._calculate_confidence(high_similarity)
        assert confidence >= 0.8
        assert confidence <= 1.0

        # Low similarity results
        low_similarity = [
            {"similarity": 0.3},
            {"similarity": 0.4},
            {"similarity": 0.35},
        ]
        confidence = qa_tool_instance._calculate_confidence(low_similarity)
        assert confidence >= 0.3
        assert confidence <= 0.6

        # Empty results
        confidence = qa_tool_instance._calculate_confidence([])
        assert confidence == 0.0

    def test_extract_sources(self, qa_tool_instance):
        """Test source extraction from search results."""
        search_results = [
            {
                "metadata": {"source": "file1.txt", "chunk_id": "chunk_0"},
                "text": "Content 1",
            },
            {
                "metadata": {"source": "file2.txt", "chunk_id": "chunk_1"},
                "text": "Content 2",
            },
        ]

        sources = qa_tool_instance._extract_sources(search_results)
        expected_sources = ["file1.txt:chunk_0", "file2.txt:chunk_1"]
        assert sources == expected_sources

    @patch("app.tools.qa_tool.vector_db")
    @patch("app.tools.qa_tool.llm_client")
    def test_answer_question_success(self, mock_llm, mock_vector_db, qa_tool_instance):
        """Test successful question answering."""
        # Mock vector database search
        mock_vector_db.search.return_value = [
            {
                "metadata": {"source": "test.txt", "chunk_id": "chunk_0"},
                "text": "Test content about search functionality.",
                "similarity": 0.8,
                "id": "test_id",
                "distance": 0.2,
            }
        ]

        # Mock LLM response
        mock_llm.generate_structured_response.return_value = {
            "answer": "The search functionality has issues with pagination.",
            "sources": ["test.txt:chunk_0"],
            "confidence": 0.8,
        }

        result = qa_tool_instance.answer_question("What are the search issues?")

        assert isinstance(result, QAAnswer)
        assert result.query == "What are the search issues?"
        assert "search functionality" in result.answer
        assert result.confidence > 0
        assert len(result.sources) > 0

    @patch("app.tools.qa_tool.vector_db")
    def test_answer_question_no_results(self, mock_vector_db, qa_tool_instance):
        """Test question answering with no search results."""
        mock_vector_db.search.return_value = []

        result = qa_tool_instance.answer_question("What is this about?")

        assert isinstance(result, QAAnswer)
        assert result.answer == "ไม่พบข้อมูลเพียงพอ"
        assert result.confidence == 0.0
        assert len(result.sources) == 0

    @patch("app.tools.qa_tool.vector_db")
    @patch("app.tools.qa_tool.llm_client")
    def test_answer_question_llm_failure(
        self, mock_llm, mock_vector_db, qa_tool_instance
    ):
        """Test question answering when LLM fails."""
        mock_vector_db.search.return_value = [
            {
                "metadata": {"source": "test.txt", "chunk_id": "chunk_0"},
                "text": "Test content.",
                "similarity": 0.8,
                "id": "test_id",
                "distance": 0.2,
            }
        ]
        mock_llm.generate_structured_response.return_value = None

        result = qa_tool_instance.answer_question("Test question?")

        assert isinstance(result, QAAnswer)
        assert result.answer == "ไม่พบข้อมูลเพียงพอ"
        assert result.confidence == 0.1  # Low confidence but not zero


class TestIssueSummaryTool:
    """Test cases for issue summary tool functionality."""

    @pytest.fixture
    def issue_summary_tool_instance(self):
        """Create an IssueSummaryTool instance for testing."""
        return IssueSummaryTool()

    def test_load_prompt_success(self, issue_summary_tool_instance):
        """Test successful prompt loading."""
        assert issue_summary_tool_instance.prompt_template is not None
        assert "{{issue_text}}" in issue_summary_tool_instance.prompt_template

    @patch("app.tools.issue_summary_tool.llm_client")
    def test_summarize_issue_success(self, mock_llm, issue_summary_tool_instance):
        """Test successful issue summarization."""
        issue_text = "Users report that email notifications are not being sent when documents are shared."

        mock_llm.generate_structured_response.return_value = {
            "reported_issues": ["Email notifications not sent"],
            "affected_components": ["Email service", "Document sharing"],
            "severity": "High",
            "suggestions": ["Check email queue", "Verify SMTP settings"],
        }

        result = issue_summary_tool_instance.summarize_issue(issue_text)

        assert isinstance(result, IssueSummary)
        assert result.raw_text == issue_text
        assert "Email notifications not sent" in result.reported_issues
        assert "Email service" in result.affected_components
        assert result.severity == "High"
        assert len(result.suggestions) > 0

    @patch("app.tools.issue_summary_tool.llm_client")
    def test_summarize_issue_invalid_severity(
        self, mock_llm, issue_summary_tool_instance
    ):
        """Test handling of invalid severity from LLM."""
        issue_text = "Test issue"

        mock_llm.generate_structured_response.return_value = {
            "reported_issues": ["Test issue"],
            "affected_components": ["Test component"],
            "severity": "Invalid",  # Invalid severity
            "suggestions": [],
        }

        result = issue_summary_tool_instance.summarize_issue(issue_text)

        assert isinstance(result, IssueSummary)
        assert result.severity == "Low"  # Should default to Low

    @patch("app.tools.issue_summary_tool.llm_client")
    def test_summarize_issue_llm_failure(self, mock_llm, issue_summary_tool_instance):
        """Test issue summarization when LLM fails."""
        issue_text = "Test issue"
        mock_llm.generate_structured_response.return_value = None

        result = issue_summary_tool_instance.summarize_issue(issue_text)

        assert isinstance(result, IssueSummary)
        assert result.raw_text == issue_text
        assert len(result.reported_issues) == 0
        assert len(result.affected_components) == 0
        assert result.severity == "Low"
        assert len(result.suggestions) == 0


class TestRouterAgent:
    """Test cases for router agent functionality."""

    @pytest.fixture
    def router_agent_instance(self):
        """Create a RouterAgent instance for testing."""
        return RouterAgent()

    def test_load_prompt_success(self, router_agent_instance):
        """Test successful prompt loading."""
        assert router_agent_instance.prompt_template is not None
        assert "{{query}}" in router_agent_instance.prompt_template

    @patch("app.tools.router_agent.llm_client")
    @patch("app.tools.router_agent.qa_tool")
    @patch("app.tools.router_agent.issue_summary_tool")
    def test_route_to_qa_tool(
        self,
        mock_issue_tool,
        mock_qa_tool,
        mock_llm,
        router_agent_instance,
    ):
        """Test routing to QA tool."""
        query = "What are the issues with email notifications?"

        # Mock LLM routing decision
        mock_llm.generate_structured_response.return_value = {
            "tool": "qa",
            "rationale": "The question asks for factual information from documents.",
            "tool_input": {"query": query},
        }

        # Mock QA tool response
        mock_qa_tool.answer_question.return_value = QAAnswer(
            query=query,
            answer="Users report email notifications are not working.",
            sources=["bug_report.txt:chunk_1"],
            confidence=0.8,
        )

        decision = router_agent_instance._route_query(query)

        assert isinstance(decision, RouterDecision)
        assert decision.tool == "qa"
        assert "factual information" in decision.rationale
        assert decision.tool_input["query"] == query

    @patch("app.tools.router_agent.llm_client")
    @patch("app.tools.router_agent.qa_tool")
    @patch("app.tools.router_agent.issue_summary_tool")
    def test_route_to_issue_summary_tool(
        self,
        mock_issue_tool,
        mock_qa_tool,
        mock_llm,
        router_agent_instance,
    ):
        """Test routing to issue summary tool."""
        query = (
            "Users report that the upload progress gets stuck at 99% for large files."
        )

        # Mock LLM routing decision
        mock_llm.generate_structured_response.return_value = {
            "tool": "issue_summary",
            "rationale": "The query describes a specific issue that needs summarization.",
            "tool_input": {"issue_text": query},
        }

        decision = router_agent_instance._route_query(query)

        assert isinstance(decision, RouterDecision)
        assert decision.tool == "issue_summary"
        assert "specific issue" in decision.rationale
        assert decision.tool_input["issue_text"] == query

    @patch("app.tools.router_agent.llm_client")
    def test_route_query_llm_failure(self, mock_llm, router_agent_instance):
        """Test routing when LLM fails."""
        query = "Test query"
        mock_llm.generate_structured_response.return_value = None

        decision = router_agent_instance._route_query(query)

        assert isinstance(decision, RouterDecision)
        assert decision.tool == "qa"  # Should default to QA
        assert "defaulting to QA" in decision.rationale
        assert decision.tool_input["query"] == query

    @patch("app.tools.router_agent.llm_client")
    def test_route_query_invalid_tool(self, mock_llm, router_agent_instance):
        """Test routing when LLM returns invalid tool."""
        query = "Test query"
        mock_llm.generate_structured_response.return_value = {
            "tool": "invalid_tool",
            "rationale": "Invalid tool choice.",
            "tool_input": {"query": query},
        }

        decision = router_agent_instance._route_query(query)

        assert isinstance(decision, RouterDecision)
        assert decision.tool == "qa"  # Should default to QA
        assert decision.tool_input["query"] == query

    def test_execute_tool_qa(self, router_agent_instance):
        """Test executing QA tool."""
        decision = RouterDecision(
            tool="qa",
            rationale="Test rationale",
            tool_input={"query": "Test question"},
        )

        with patch("app.tools.router_agent.qa_tool") as mock_qa:
            mock_qa.answer_question.return_value = QAAnswer(
                query="Test question",
                answer="Test answer",
                sources=[],
                confidence=0.8,
            )

            result = router_agent_instance._execute_tool(decision)

            assert isinstance(result, QAAnswer)
            mock_qa.answer_question.assert_called_once_with("Test question")

    def test_execute_tool_issue_summary(self, router_agent_instance):
        """Test executing issue summary tool."""
        decision = RouterDecision(
            tool="issue_summary",
            rationale="Test rationale",
            tool_input={"issue_text": "Test issue"},
        )

        with patch("app.tools.router_agent.issue_summary_tool") as mock_issue:
            mock_issue.summarize_issue.return_value = IssueSummary(
                raw_text="Test issue",
                reported_issues=["Test problem"],
                affected_components=["Test component"],
                severity="Low",
                suggestions=[],
            )

            result = router_agent_instance._execute_tool(decision)

            assert isinstance(result, IssueSummary)
            mock_issue.summarize_issue.assert_called_once_with("Test issue")

    @patch("app.tools.router_agent.llm_client")
    @patch("app.tools.router_agent.qa_tool")
    @patch("app.tools.router_agent.issue_summary_tool")
    def test_process_query_end_to_end(
        self,
        mock_issue_tool,
        mock_qa_tool,
        mock_llm,
        router_agent_instance,
    ):
        """Test end-to-end query processing."""
        query = "What are the search issues?"

        # Mock routing decision
        mock_llm.generate_structured_response.return_value = {
            "tool": "qa",
            "rationale": "Question about documented issues.",
            "tool_input": {"query": query},
        }

        # Mock QA tool response
        mock_qa_tool.answer_question.return_value = QAAnswer(
            query=query,
            answer="Search has pagination issues.",
            sources=["feedback.txt:chunk_2"],
            confidence=0.75,
        )

        result = router_agent_instance.process_query(query)

        assert "decision" in result
        assert "result" in result
        assert result["decision"]["tool"] == "qa"
        assert result["result"]["answer"] == "Search has pagination issues."
