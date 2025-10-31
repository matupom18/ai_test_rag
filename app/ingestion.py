import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.config import config
from app.vectordb import vector_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of document text with metadata."""

    text: str
    source: str
    chunk_id: str
    metadata: Dict[str, Any]


class DocumentIngestion:
    def __init__(self):
        self.chunk_size = config.MAX_CHUNK_CHARS
        self.data_dir = Path(config.DATA_DIR)

    def read_file(self, file_path: str) -> Optional[str]:
        """Read file content safely, handling special characters in paths."""
        try:
            path = Path(file_path)
            if not path.exists():
                path = self.data_dir / path.name
                if not path.exists():
                    logger.error(f"File not found: {file_path}")
                    return None

            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            logger.info(f"Successfully read file: {path}")
            return content

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def chunk_text(self, text: str, source: str) -> List[DocumentChunk]:
        """Chunk text by paragraphs or character limit."""
        chunks = []

        paragraphs = text.split("\n\n")

        current_chunk = ""
        chunk_counter = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(
                        DocumentChunk(
                            text=current_chunk.strip(),
                            source=source,
                            chunk_id=f"{source}_chunk_{chunk_counter}",
                            metadata={"source": source, "chunk_id": chunk_counter},
                        )
                    )
                    chunk_counter += 1
                    current_chunk = ""

                for i in range(0, len(paragraph), self.chunk_size):
                    chunk_text = paragraph[i : i + self.chunk_size]
                    chunks.append(
                        DocumentChunk(
                            text=chunk_text,
                            source=source,
                            chunk_id=f"{source}_chunk_{chunk_counter}",
                            metadata={"source": source, "chunk_id": chunk_counter},
                        )
                    )
                    chunk_counter += 1
            else:
                if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                    if current_chunk:
                        chunks.append(
                            DocumentChunk(
                                text=current_chunk.strip(),
                                source=source,
                                chunk_id=f"{source}_chunk_{chunk_counter}",
                                metadata={"source": source, "chunk_id": chunk_counter},
                            )
                        )
                        chunk_counter += 1

                    current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph

        if current_chunk:
            chunks.append(
                DocumentChunk(
                    text=current_chunk.strip(),
                    source=source,
                    chunk_id=f"{source}_chunk_{chunk_counter}",
                    metadata={"source": source, "chunk_id": chunk_counter},
                )
            )

        logger.info(f"Created {len(chunks)} chunks from {source}")
        return chunks

    def process_documents(self, doc_paths: List[str]) -> bool:
        """Process multiple documents and add them to vector store."""
        all_chunks = []

        for doc_path in doc_paths:
            logger.info(f"Processing document: {doc_path}")

            if os.path.isabs(doc_path):
                source = Path(doc_path).name
            else:
                source = Path(doc_path).name

            content = self.read_file(doc_path)
            if not content:
                logger.error(f"Failed to read document: {doc_path}")
                continue

            chunks = self.chunk_text(content, source)
            if not chunks:
                logger.error(f"No chunks created from document: {doc_path}")
                continue

            for chunk in chunks:
                all_chunks.append(
                    {
                        "id": chunk.chunk_id,
                        "text": chunk.text,
                        "metadata": chunk.metadata,
                    }
                )

        if not all_chunks:
            logger.error("No chunks to process")
            return False

        success = vector_db.add_documents(all_chunks)
        if success:
            logger.info(
                f"Successfully ingested {len(all_chunks)} chunks from {len(doc_paths)} documents"
            )
        else:
            logger.error("Failed to add chunks to vector database")

        return success

    def ingest_default_documents(self) -> bool:
        """Ingest all default documents from the data directory."""
        doc_paths = []
        for doc_name in config.DOCUMENT_SOURCES:
            doc_path = self.data_dir / doc_name
            if doc_path.exists():
                doc_paths.append(str(doc_path))
            else:
                logger.warning(f"Default document not found: {doc_path}")

        if not doc_paths:
            logger.error("No default documents found")
            return False

        return self.process_documents(doc_paths)


def main():
    """CLI entry point for ingestion."""
    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument(
        "--docs", nargs="+", help="List of document paths to ingest", default=[]
    )
    parser.add_argument(
        "--default",
        action="store_true",
        help="Ingest all default documents from data directory",
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset vector database before ingestion"
    )

    args = parser.parse_args()

    ingestion = DocumentIngestion()

    if args.reset:
        logger.info("Resetting vector database...")
        vector_db.reset_collection()

    if args.default:
        logger.info("Ingesting default documents...")
        success = ingestion.ingest_default_documents()
    elif args.docs:
        logger.info(f"Ingesting specified documents: {args.docs}")
        success = ingestion.process_documents(args.docs)
    else:
        logger.error("No documents specified. Use --docs or --default")
        sys.exit(1)

    if success:
        logger.info("Ingestion completed successfully")

        stats = vector_db.get_collection_stats()
        logger.info(f"Vector database stats: {stats}")
    else:
        logger.error("Ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
