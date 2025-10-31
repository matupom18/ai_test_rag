import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.api.main import app
from app.schemas import QAAnswer, IssueSummary, RouterDecision

client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Internal AI Assistant API" in data["message"]
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"

    @patch("app.api.routes.qa_tool")
    def test_qa_endpoint_success(self, mock_qa_tool):
        """Test successful QA endpoint."""
        # Mock QA tool response
        mock_qa_tool.answer_question.return_value = QAAnswer(
            query="What are the search issues?",
            answer="Users report pagination problems in search results.",
            sources=[
                "ai_test_user_feedback.txt:chunk_3",
                "ai_test_bug_report.txt:chunk_2",
            ],
            confidence=0.78,
        )

        response = client.post(
            "/api/v1/qa", json={"query": "What are the search issues?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What are the search issues?"
        assert "pagination problems" in data["answer"]
        assert len(data["sources"]) == 2
        assert data["confidence"] == 0.78
        mock_qa_tool.answer_question.assert_called_once_with(
            "What are the search issues?"
        )

    def test_qa_endpoint_missing_query(self):
        """Test QA endpoint with missing query."""
        response = client.post("/api/v1/qa", json={})
        assert response.status_code == 422  # Validation error

    @patch("app.api.routes.qa_tool")
    def test_qa_endpoint_error(self, mock_qa_tool):
        """Test QA endpoint when tool raises exception."""
        mock_qa_tool.answer_question.side_effect = Exception("Test error")

        response = client.post("/api/v1/qa", json={"query": "Test question"})

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    @patch("app.api.routes.issue_summary_tool")
    def test_summarize_endpoint_success(self, mock_issue_tool):
        """Test successful summarize endpoint."""
        # Mock issue summary tool response
        mock_issue_tool.summarize_issue.return_value = IssueSummary(
            raw_text="Upload gets stuck at 99% for large files.",
            reported_issues=["Upload progress stuck at 99%"],
            affected_components=["File upload", "Progress tracking"],
            severity="Medium",
            suggestions=[
                "Investigate upload finalization",
                "Check progress tracking logic",
            ],
        )

        response = client.post(
            "/api/v1/summarize",
            json={"issue_text": "Upload gets stuck at 99% for large files."},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["raw_text"] == "Upload gets stuck at 99% for large files."
        assert "Upload progress stuck at 99%" in data["reported_issues"]
        assert "File upload" in data["affected_components"]
        assert data["severity"] == "Medium"
        assert len(data["suggestions"]) == 2
        mock_issue_tool.summarize_issue.assert_called_once_with(
            "Upload gets stuck at 99% for large files."
        )

    def test_summarize_endpoint_missing_issue_text(self):
        """Test summarize endpoint with missing issue_text."""
        response = client.post("/api/v1/summarize", json={})
        assert response.status_code == 422 

    @patch("app.api.routes.issue_summary_tool")
    def test_summarize_endpoint_error(self, mock_issue_tool):
        """Test summarize endpoint when tool raises exception."""
        mock_issue_tool.summarize_issue.side_effect = Exception("Test error")

        response = client.post("/api/v1/summarize", json={"issue_text": "Test issue"})

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    @patch("app.api.routes.router_agent")
    def test_query_endpoint_success(self, mock_router_agent):
        """Test successful query endpoint."""
        # Mock router agent response
        mock_router_agent.process_query.return_value = {
            "decision": {
                "tool": "qa",
                "rationale": "The question asks for factual information from documents.",
                "tool_input": {"query": "What are email notification issues?"},
            },
            "result": {
                "query": "What are email notification issues?",
                "answer": "Users are not receiving email notifications when documents are shared.",
                "sources": ["ai_test_user_feedback.txt:chunk_7"],
                "confidence": 0.85,
            },
        }

        response = client.post(
            "/api/v1/query", json={"query": "What are email notification issues?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "decision" in data
        assert "result" in data
        assert data["decision"]["tool"] == "qa"
        assert "factual information" in data["decision"]["rationale"]
        assert (
            data["result"]["answer"]
            == "Users are not receiving email notifications when documents are shared."
        )
        assert data["result"]["confidence"] == 0.85
        mock_router_agent.process_query.assert_called_once_with(
            "What are email notification issues?"
        )

    def test_query_endpoint_missing_query(self):
        """Test query endpoint with missing query."""
        response = client.post("/api/v1/query", json={})
        assert response.status_code == 422  # Validation error

    @patch("app.api.routes.router_agent")
    def test_query_endpoint_error(self, mock_router_agent):
        """Test query endpoint when router agent raises exception."""
        mock_router_agent.process_query.side_effect = Exception("Test error")

        response = client.post("/api/v1/query", json={"query": "Test query"})

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    @patch("app.api.routes.DocumentIngestion")
    def test_ingest_endpoint_success(self, mock_ingestion_class):
        """Test successful ingest endpoint."""
        # Mock DocumentIngestion instance
        mock_ingestion = MagicMock()
        mock_ingestion_class.return_value = mock_ingestion
        mock_ingestion.process_documents.return_value = True

        response = client.post(
            "/api/v1/ingest",
            json={"docs": ["data/test_file.txt", "data/another_file.txt"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "Scheduled ingestion of 2 documents" in data["message"]

    def test_ingest_endpoint_missing_docs(self):
        """Test ingest endpoint with missing docs."""
        response = client.post("/api/v1/ingest", json={})
        assert response.status_code == 422  

    @patch("app.vectordb.vector_db")
    def test_stats_endpoint_success(self, mock_vector_db):
        """Test successful stats endpoint."""
        # Mock vector database stats
        mock_vector_db.get_collection_stats.return_value = {
            "total_documents": 156,
            "collection_name": "internal_docs",
            "embedding_model": "intfloat/multilingual-e5-base",
        }

        response = client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 156
        assert data["collection_name"] == "internal_docs"
        assert data["embedding_model"] == "intfloat/multilingual-e5-base"
        mock_vector_db.get_collection_stats.assert_called_once()

    @patch("app.vectordb.vector_db")
    def test_stats_endpoint_error(self, mock_vector_db):
        """Test stats endpoint when vector DB raises exception."""
        mock_vector_db.get_collection_stats.side_effect = Exception("Database error")

        response = client.get("/api/v1/stats")

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    def test_cors_headers(self):
        """Test that CORS headers are present."""
        response = client.options("/api/v1/healthz")
        # Check for CORS headers in the response
        assert response.status_code in [
            200,
            405,
        ] 
        get_response = client.get("/api/v1/healthz")
        assert "access-control-allow-origin" in get_response.headers

    @patch("app.api.routes.qa_tool")
    def test_qa_endpoint_thai_response(self, mock_qa_tool):
        """Test QA endpoint with Thai response."""
        mock_qa_tool.answer_question.return_value = QAAnswer(
            query="คำถามภาษาไทย",
            answer="ไม่พบข้อมูลเพียงพอ",
            sources=[],
            confidence=0.0,
        )

        response = client.post("/api/v1/qa", json={"query": "คำถามภาษาไทย"})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "ไม่พบข้อมูลเพียงพอ"

    @patch("app.api.routes.issue_summary_tool")
    def test_summarize_endpoint_thai_issue(self, mock_issue_tool):
        """Test summarize endpoint with Thai issue text."""
        mock_issue_tool.summarize_issue.return_value = IssueSummary(
            raw_text="ผู้ใช้รายงานว่าอัปโหลดไฟล์ไม่ได้",
            reported_issues=["อัปโหลดไฟล์ล้มเหลว"],
            affected_components=["ฟังก์ชันอัปโหลด"],
            severity="High",
            suggestions=["ตรวจสอบขนาดไฟล์สูงสุด", "ตรวจสอบสิทธิ์ผู้ใช้"],
        )

        response = client.post(
            "/api/v1/summarize", json={"issue_text": "ผู้ใช้รายงานว่าอัปโหลดไฟล์ไม่ได้"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["raw_text"] == "ผู้ใช้รายงานว่าอัปโหลดไฟล์ไม่ได้"
        assert "อัปโหลดไฟล์ล้มเหลว" in data["reported_issues"]
        assert data["severity"] == "High"

    @patch("app.api.routes.router_agent")
    def test_query_endpoint_issue_summary_routing(self, mock_router_agent):
        """Test query endpoint routing to issue summary tool."""
        mock_router_agent.process_query.return_value = {
            "decision": {
                "tool": "issue_summary",
                "rationale": "The query describes a specific issue that needs summarization.",
                "tool_input": {"issue_text": "Upload progress stuck at 99%"},
            },
            "result": {
                "raw_text": "Upload progress stuck at 99%",
                "reported_issues": ["Upload stuck at 99%"],
                "affected_components": ["File upload", "Progress bar"],
                "severity": "Medium",
                "suggestions": ["Check upload finalization logic"],
            },
        }

        response = client.post(
            "/api/v1/query", json={"query": "Upload progress stuck at 99%"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["decision"]["tool"] == "issue_summary"
        assert "specific issue" in data["decision"]["rationale"]
        assert data["result"]["severity"] == "Medium"

    def test_api_documentation_available(self):
        """Test that API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_available(self):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Internal AI Assistant"
