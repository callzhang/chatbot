"""
Unit tests for RAG (Retrieval Augmented Generation) system
"""

import pytest
import sys
import os
import tempfile
import sqlite3
from unittest.mock import Mock, patch, mock_open
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.rag import (
    init_rag_database, DocumentProcessor, RAGRetriever
)

class TestRAGSystem:
    """Test RAG functionality"""
    
    def test_init_rag_database(self, temp_dir):
        """Test RAG database initialization"""
        db_path = os.path.join(temp_dir, "test_rag.db")
        
        with patch('tools.rag.RAG_DB_PATH', db_path):
            init_rag_database()
            
            # Verify database was created
            assert os.path.exists(db_path)
            
            # Verify tables were created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'documents' in tables
            assert 'document_chunks' in tables
            assert 'rag_conversations' in tables
            
            conn.close()
    
    def test_document_processor_init(self):
        """Test DocumentProcessor initialization"""
        processor = DocumentProcessor()
        
        assert hasattr(processor, 'supported_formats')
        assert hasattr(processor, '_get_file_hash')
        assert hasattr(processor, '_chunk_text')
        
        # Check supported formats
        assert '.pdf' in processor.supported_formats
        assert '.txt' in processor.supported_formats
        assert '.md' in processor.supported_formats
        assert '.docx' in processor.supported_formats
        assert '.xlsx' in processor.supported_formats
        assert '.csv' in processor.supported_formats
        assert '.html' in processor.supported_formats
        assert '.json' in processor.supported_formats
    
    def test_get_file_hash(self):
        """Test file hash generation"""
        processor = DocumentProcessor()
        
        # Create a mock file
        mock_file = Mock()
        mock_file.read.return_value = b"test content"
        mock_file.seek = Mock()
        
        hash1 = processor._get_file_hash(mock_file)
        hash2 = processor._get_file_hash(mock_file)
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length
    
    def test_chunk_text(self):
        """Test text chunking functionality"""
        processor = DocumentProcessor()
        
        # Test with short text
        short_text = "This is a short text."
        chunks = processor._chunk_text(short_text, chunk_size=10, overlap=2)
        
        assert len(chunks) == 1
        assert chunks[0]['text'] == short_text
        assert chunks[0]['start'] == 0
        assert chunks[0]['end'] == len(short_text)
        
        # Test with longer text
        long_text = "This is a much longer text that should be split into multiple chunks. " * 10
        chunks = processor._chunk_text(long_text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert 'text' in chunk
            assert 'start' in chunk
            assert 'end' in chunk
            assert 'metadata' in chunk
            assert len(chunk['text']) <= 100
    
    def test_process_txt_document(self):
        """Test processing text documents"""
        processor = DocumentProcessor()
        
        # Create mock text file
        mock_file = Mock()
        mock_file.read.return_value = b"Hello, this is a test document."
        mock_file.seek = Mock()
        
        content = processor._process_txt(mock_file)
        assert content == "Hello, this is a test document."
    
    def test_process_markdown_document(self):
        """Test processing markdown documents"""
        processor = DocumentProcessor()
        
        # Create mock markdown file
        mock_file = Mock()
        mock_file.read.return_value = b"# Title\n\nThis is **bold** text."
        mock_file.seek = Mock()
        
        content = processor._process_markdown(mock_file)
        assert "Title" in content
        assert "bold" in content
    
    def test_process_json_document(self):
        """Test processing JSON documents"""
        processor = DocumentProcessor()
        
        # Create mock JSON file
        json_content = '{"name": "test", "value": 123}'
        mock_file = Mock()
        mock_file.read.return_value = json_content.encode('utf-8')
        mock_file.seek = Mock()
        
        content = processor._process_json(mock_file)
        assert "name" in content
        assert "test" in content
        assert "value" in content
        assert "123" in content
    
    def test_is_document_processed(self, temp_dir):
        """Test checking if document is already processed"""
        db_path = os.path.join(temp_dir, "test_rag.db")
        
        with patch('tools.rag.RAG_DB_PATH', db_path):
            init_rag_database()
            processor = DocumentProcessor()
            
            # Test with non-existent hash
            result = processor._is_document_processed("nonexistent_hash")
            assert result is False
            
            # Insert a document
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO documents (filename, file_hash) VALUES (?, ?)", 
                         ("test.pdf", "test_hash"))
            conn.commit()
            conn.close()
            
            # Test with existing hash
            result = processor._is_document_processed("test_hash")
            assert result is True
    
    def test_save_document(self, temp_dir):
        """Test saving document metadata"""
        db_path = os.path.join(temp_dir, "test_rag.db")
        
        with patch('tools.rag.RAG_DB_PATH', db_path):
            init_rag_database()
            processor = DocumentProcessor()
            
            doc_id = processor._save_document("test.pdf", "test_hash", ".pdf", 1024)
            
            assert isinstance(doc_id, int)
            assert doc_id > 0
            
            # Verify document was saved
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            doc = cursor.fetchone()
            
            assert doc is not None
            assert doc[1] == "test.pdf"  # filename
            assert doc[2] == "test_hash"  # file_hash
            assert doc[3] == ".pdf"       # file_type
            assert doc[4] == 1024         # file_size
            
            conn.close()
    
    def test_save_chunks(self, temp_dir):
        """Test saving document chunks"""
        db_path = os.path.join(temp_dir, "test_rag.db")
        
        with patch('tools.rag.RAG_DB_PATH', db_path):
            init_rag_database()
            processor = DocumentProcessor()
            
            # First save a document
            doc_id = processor._save_document("test.pdf", "test_hash", ".pdf", 1024)
            
            # Create test chunks
            chunks = [
                {"text": "This is chunk 1", "start": 0, "end": 15, "metadata": {"chunk_size": 15}},
                {"text": "This is chunk 2", "start": 15, "end": 30, "metadata": {"chunk_size": 15}}
            ]
            
            processor._save_chunks(doc_id, chunks)
            
            # Verify chunks were saved
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_chunks WHERE document_id = ?", (doc_id,))
            saved_chunks = cursor.fetchall()
            
            assert len(saved_chunks) == 2
            assert saved_chunks[0][3] == "This is chunk 1"  # chunk_text
            assert saved_chunks[1][3] == "This is chunk 2"  # chunk_text
            
            conn.close()
    
    def test_rag_retriever_init(self):
        """Test RAGRetriever initialization"""
        retriever = RAGRetriever()
        
        assert hasattr(retriever, 'model')
        assert hasattr(retriever, 'index')
        assert hasattr(retriever, 'chunk_embeddings')
        assert hasattr(retriever, 'chunk_texts')
    
    def test_unsupported_file_format(self):
        """Test handling of unsupported file formats"""
        processor = DocumentProcessor()
        
        # Create mock file with unsupported format
        mock_file = Mock()
        mock_file.name = "test.xyz"
        
        with pytest.raises(ValueError, match="不支持的文件格式"):
            processor.process_document(mock_file, "test.xyz")
    
    def test_document_processing_error_handling(self):
        """Test error handling in document processing"""
        processor = DocumentProcessor()
        
        # Create mock file that raises an exception
        mock_file = Mock()
        mock_file.read.side_effect = Exception("Read error")
        mock_file.seek = Mock()
        
        result = processor.process_document(mock_file, "test.txt")
        
        assert result["status"] == "error"
        assert "error" in result
        assert "Read error" in result["error"]

