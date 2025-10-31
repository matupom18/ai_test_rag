import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.schemas import QAAnswer, IssueSummary, RouterDecision
from app.tools.qa_tool import qa_tool
from app.tools.issue_summary_tool import issue_summary_tool
from app.tools.router_agent import router_agent
from app.ingestion import DocumentIngestion

logger = logging.getLogger(__name__)

router = APIRouter()


class QARequest(BaseModel):
    query: str = Field(..., description="Question to answer from documents")


class SummaryRequest(BaseModel):
    issue_text: str = Field(..., description="Issue text to summarize")


class QueryRequest(BaseModel):
    query: str = Field(..., description="Query to route and process")


class IngestRequest(BaseModel):
    docs: List[str] = Field(..., description="List of document paths or text to ingest")


@router.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/qa")
async def qa_endpoint(request: QARequest):
    """Answer a question using document search."""
    try:
        logger.info(f"QA request: {request.query}")
        result = qa_tool.answer_question(request.query)
        return result.dict()
    except Exception as e:
        logger.error(f"Error in QA endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/summarize")
async def summarize_endpoint(request: SummaryRequest):
    """Summarize an issue text."""
    try:
        logger.info(f"Summary request: {request.issue_text[:100]}...")
        result = issue_summary_tool.summarize_issue(request.issue_text)
        return result.dict()
    except Exception as e:
        logger.error(f"Error in summarize endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/query")
async def query_endpoint(request: QueryRequest):
    """Process a query through routing and tool execution."""
    try:
        logger.info(f"Query request: {request.query}")
        result = router_agent.process_query(request.query)
        return result
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ingest")
async def ingest_endpoint(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest documents into vector store."""
    try:
        logger.info(f"Ingest request with {len(request.docs)} documents")

        def run_ingestion():
            ingestion = DocumentIngestion()
            success = ingestion.process_documents(request.docs)
            if success:
                logger.info(f"Successfully ingested {len(request.docs)} documents")
            else:
                logger.error("Failed to ingest documents")

        background_tasks.add_task(run_ingestion)

        return {"message": f"Scheduled ingestion of {len(request.docs)} documents"}
    except Exception as e:
        logger.error(f"Error in ingest endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_stats():
    """Get vector database statistics."""
    try:
        from app.vectordb import vector_db

        stats = vector_db.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
