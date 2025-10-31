"""
Test cases for document ingestion functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.ingestion import DocumentIngestion
from app.vectordb import vector_db


class TestDocumentIngestion:
    """Test cases for document ingestion functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_document(self, temp_dir):
        """Create a sample document for testing."""
        doc_path = Path(temp_dir) / "test_document.txt"
        content = """This is a test document.

It contains multiple paragraphs.

This paragraph is quite long and should be split into chunks because it exceeds the maximum chunk size limit that we have configured for the document ingestion system. This paragraph is deliberately long to test the chunking functionality and ensure that documents with long paragraphs are handled correctly by the ingestion process.

Another paragraph here."""

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(doc_path)

    @pytest.fixture
    def ingestion_instance(self):
        """Create a DocumentIngestion instance for testing."""
        return DocumentIngestion()

    def test_read_file_success(self, ingestion_instance, sample_document):
        """Test successful file reading."""
        content = ingestion_instance.read_file(sample_document)
        assert content is not None
        assert "This is a test document" in content
        assert "multiple paragraphs" in content

    def test_read_file_not_found(self, ingestion_instance):
        """Test reading a non-existent file."""
        content = ingestion_instance.read_file("non_existent_file.txt")
        assert content is None

    def test_chunk_text_paragraphs(self, ingestion_instance):
        """Test text chunking by paragraphs."""
        text = """First paragraph.

Second paragraph.

Third paragraph with some more content."""

        chunks = ingestion_instance.chunk_text(text, "test_source")

        assert len(chunks) > 0
        assert all(isinstance(chunk.text, str) for chunk in chunks)
        assert all(chunk.source == "test_source" for chunk in chunks)
        assert all(chunk.chunk_id.startswith("test_source_chunk_") for chunk in chunks)

    def test_chunk_text_long_paragraph(self, ingestion_instance):
        """Test chunking of very long paragraphs."""
        # Create a very long paragraph
        long_text = "Word " * 2000  # Much longer than chunk size

        chunks = ingestion_instance.chunk_text(long_text, "test_source")

        assert len(chunks) > 1
        assert all(
            len(chunk.text) <= ingestion_instance.chunk_size + 100 for chunk in chunks
        )

    def test_process_documents_success(self, ingestion_instance, sample_document):
        """Test successful document processing."""
        with patch.object(vector_db, "add_documents", return_value=True) as mock_add:
            result = ingestion_instance.process_documents([sample_document])

            assert result is True
            mock_add.assert_called_once()

            # Check that chunks were created
            call_args = mock_add.call_args[0][0]
            assert len(call_args) > 0
            assert all("text" in chunk for chunk in call_args)
            assert all("metadata" in chunk for chunk in call_args)
            assert all("id" in chunk for chunk in call_args)

    def test_process_documents_empty_list(self, ingestion_instance):
        """Test processing with empty document list."""
        result = ingestion_instance.process_documents([])
        assert result is False

    def test_process_documents_file_not_found(self, ingestion_instance):
        """Test processing non-existent documents."""
        result = ingestion_instance.process_documents(["non_existent.txt"])
        assert result is False

    @patch("app.ingestion.vector_db")
    def test_ingest_default_documents(self, mock_vector_db, ingestion_instance):
        """Test ingesting default documents."""
        mock_vector_db.add_documents.return_value = True

        with patch.object(ingestion_instance, "data_dir") as mock_data_dir:
            with patch.object(ingestion_instance, "read_file") as mock_read_file:
                mock_read_file.side_effect = [
                    "Bug report content here...",
                    "User feedback content here...",
                ]

                result = ingestion_instance.ingest_default_documents()

                assert result is True
                assert mock_read_file.call_count == 2
                mock_vector_db.add_documents.assert_called_once()

    @patch("app.ingestion.vector_db")
    def test_ingest_default_documents_missing_files(
        self, mock_vector_db, ingestion_instance
    ):
        """Test ingesting default documents when some are missing."""
        mock_vector_db.add_documents.return_value = True

        with patch.object(ingestion_instance, "data_dir") as mock_data_dir:
            with patch.object(ingestion_instance, "read_file") as mock_read_file:
                mock_read_file.side_effect = [
                    "Bug report content here...",
                    None, 
                ]

                result = ingestion_instance.ingest_default_documents()

                assert result is True
                assert mock_read_file.call_count == 2
                mock_vector_db.add_documents.assert_called_once()

    @patch("app.ingestion.vector_db")
    def test_process_documents_vector_db_failure(
        self, mock_vector_db, ingestion_instance, sample_document
    ):
        """Test handling of vector database failure."""
        mock_vector_db.add_documents.return_value = False

        result = ingestion_instance.process_documents([sample_document])
        assert result is False
        mock_vector_db.add_documents.assert_called_once()

    def test_chunk_metadata_structure(self, ingestion_instance):
        """Test that chunk metadata has the correct structure."""
        text = "Simple paragraph for testing."
        chunks = ingestion_instance.chunk_text(text, "test_source")

        for chunk in chunks:
            metadata = chunk.metadata
            assert isinstance(metadata, dict)
            assert "source" in metadata
            assert "chunk_id" in metadata
            assert metadata["source"] == "test_source"
            assert isinstance(metadata["chunk_id"], int)

    def test_chunk_id_generation(self, ingestion_instance):
        """Test that chunk IDs are generated correctly."""
        text = """Paragraph 1.

Paragraph 2.

Paragraph 3."""

        chunks = ingestion_instance.chunk_text(text, "test_source")
        chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks]

        assert chunk_ids == list(range(len(chunks)))
