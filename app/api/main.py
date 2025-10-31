import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Internal AI Assistant",
    description="AI assistant for product/engineering document Q&A and issue summarization",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["assistant"])


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Internal AI Assistant")
    logger.info(f"Embedding model: {config.EMBEDDING_MODEL}")
    logger.info(f"Vector directory: {config.VECTOR_DIR}")
    logger.info(f"OpenAI API base: {config.OPENAI_API_BASE}")
    logger.info(f"OpenAI model: {config.OPENAI_MODEL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Internal AI Assistant")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Internal AI Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
