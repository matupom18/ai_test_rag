import os
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import config
from app.ingestion import DocumentIngestion
from app.vectordb import vector_db
from chromadb.api.types import IncludeEnum


def test_document_ingestion():
    """Test document ingestion with the available data files."""
    print(" Testing Document Ingestion...")

    # Initialize ingestion
    ingestion = DocumentIngestion()

    # Get available document files
    data_dir = Path(config.DATA_DIR)
    available_docs = []

    for doc_name in config.DOCUMENT_SOURCES:
        doc_path = data_dir / doc_name
        if doc_path.exists():
            available_docs.append(str(doc_path))
            print(f" Found document: {doc_name}")
        else:
            print(f" Missing document: {doc_name}")

    if not available_docs:
        print(" No documents found to ingest!")
        return False

    # Reset vector database for clean test
    print(" Resetting vector database...")
    vector_db.reset_collection()

    # Ingest documents
    print(f" Ingesting {len(available_docs)} documents...")
    success = ingestion.process_documents(available_docs)

    if success:
        # Get collection stats
        stats = vector_db.get_collection_stats()
        print(f" Ingestion completed successfully!")
        print(f" Vector database stats: {json.dumps(stats, indent=2)}")
        return True
    else:
        print(" Ingestion failed!")
        return False


def test_vector_search():
    """Test vector search functionality."""
    print("\n Testing Vector Search...")

    # Test queries based on the document content
    test_queries = [
        "What are the issues with email notifications?",
        "What problems do users report about search functionality?",
        "What are the UI/UX issues mentioned?",
        "What bugs affect document upload?",
        "What are the pagination issues?",
    ]

    for query in test_queries:
        print(f"\n Query: {query}")
        results = vector_db.search(query, top_k=3)

        if results:
            print(f" Found {len(results)} relevant chunks:")
            for i, result in enumerate(results, 1):
                source = result["metadata"].get("source", "unknown")
                similarity = result["similarity"]
                text_preview = (
                    result["text"][:100] + "..."
                    if len(result["text"]) > 100
                    else result["text"]
                )
                print(f"      {i}. [{source}] (similarity: {similarity:.3f})")
                print(f"         {text_preview}")
        else:
            print(" No results found")

    return True


def test_document_analysis():
    """Analyze the ingested documents and provide insights."""
    print("\n Analyzing Document Content...")

    # Get all documents from the vector database
    try:
        # Get collection info
        collection = vector_db.collection
        count = collection.count()

        print(f" Total document chunks: {count}")

        # Get a sample of documents to analyze
        sample_results = collection.get(
            limit=min(10, count), include=[IncludeEnum.documents, IncludeEnum.metadatas]
        )

        if sample_results and sample_results.get("documents"):
            sources = {}
            total_chars = 0

            documents = sample_results.get("documents") or []
            metadatas = sample_results.get("metadatas") or []
            
            for doc, metadata in zip(documents, metadatas):
                source = metadata.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
                total_chars += len(doc)

            print(f" Document sources:")
            for source, count in sources.items():
                print(f"      - {source}: {count} chunks")

            print(f" Total characters in sample: {total_chars:,}")

        return True

    except Exception as e:
        print(f" Error analyzing documents: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n Generating Test Report...")

    report = {
        "test_timestamp": str(Path(__file__).stat().st_mtime),
        "system_info": {
            "embedding_model": config.EMBEDDING_MODEL,
            "vector_directory": config.VECTOR_DIR,
            "max_chunk_chars": config.MAX_CHUNK_CHARS,
            "top_k_results": config.TOP_K,
        },
        "documents": config.DOCUMENT_SOURCES,
        "test_results": {},
    }

    # Test document ingestion
    ingestion_success = test_document_ingestion()
    report["test_results"]["ingestion"] = {
        "success": ingestion_success,
        "message": "Document ingestion completed successfully"
        if ingestion_success
        else "Document ingestion failed",
    }

    if ingestion_success:
        # Test vector search
        search_success = test_vector_search()
        report["test_results"]["search"] = {
            "success": search_success,
            "message": "Vector search working correctly"
            if search_success
            else "Vector search failed",
        }

        # Test document analysis
        analysis_success = test_document_analysis()
        report["test_results"]["analysis"] = {
            "success": analysis_success,
            "message": "Document analysis completed"
            if analysis_success
            else "Document analysis failed",
        }

    # Save report
    report_path = Path("test_output/rag_test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n Test report saved to: {report_path}")

    # Summary
    print("\n Test Summary:")
    all_tests_passed = all(
        result["success"] for result in report["test_results"].values()
    )
    if all_tests_passed:
        print(" All tests passed! RAG system is working correctly.")
    else:
        print("  Some tests failed. Check the report above for details.")

    return all_tests_passed


def main():
    """Main test function."""
    print(" RAG System Test Suite")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("data").exists():
        print(
            " Error: 'data' directory not found. Please run this from the ai-inter directory."
        )
        return False

    # Run comprehensive test
    success = generate_test_report()

    print("\n" + "=" * 50)
    if success:
        print(" RAG system test completed successfully!")
        print("\n Next Steps:")
        print("   1. Set up your OpenRouter or OpenAI API key in .env file")
        print("   2. Run the API server: python -m app.api.main")
        print("   3. Test the API endpoints at http://localhost:8000/docs")
    else:
        print(" RAG system test failed. Please check the errors above.")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
