import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.api.types import IncludeEnum
from sentence_transformers import SentenceTransformer
from app.config import config

logger = logging.getLogger(__name__)


class VectorDB:
    def __init__(self):
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.vector_dir = Path(config.VECTOR_DIR)
        self.vector_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.vector_dir), settings=Settings(allow_reset=True)
        )

        self.collection = self.client.get_or_create_collection(
            name="internal_docs",
            metadata={"description": "Internal documents for QA assistant"},
        )

    def add_documents(self, chunks: List[Dict[str, Any]]) -> bool:
        """Add document chunks to the vector database."""
        try:
            if not chunks:
                logger.warning("No chunks provided to add_documents")
                return False

            texts = [chunk["text"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            ids = [chunk["id"] for chunk in chunks]

            logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)

            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Successfully added {len(chunks)} chunks to vector database")
            return True

        except Exception as e:
            logger.error(f"Error adding documents to vector database: {e}")
            return False

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            top_k = top_k or config.TOP_K

            query_embedding = self.embedding_model.encode(
                [query], convert_to_numpy=True
            )

            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k,
                include=[IncludeEnum.documents, IncludeEnum.metadatas, IncludeEnum.distances],
            )

            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    text = results["documents"][0][i] if results["documents"] and results["documents"][0] else ""
                    metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                    distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else 0.0
                    
                    formatted_results.append(
                        {
                            "id": results["ids"][0][i],
                            "text": text,
                            "metadata": metadata,
                            "distance": distance,
                            "similarity": 1 - distance,
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching vector database: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": "internal_docs",
                "embedding_model": config.EMBEDDING_MODEL,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}

    def reset_collection(self) -> bool:
        """Reset the entire collection."""
        try:
            self.client.delete_collection("internal_docs")
            self.collection = self.client.get_or_create_collection(
                name="internal_docs",
                metadata={"description": "Internal documents for QA assistant"},
            )
            logger.info("Successfully reset vector database collection")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False

vector_db = VectorDB()
