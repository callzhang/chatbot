"""
RAG (Retrieval Augmented Generation) system for Stardust.ai Chatbot
Provides document upload, processing, and intelligent retrieval capabilities
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import json
import os
import sqlite3
from datetime import datetime
import hashlib
import re

# Document processing imports
import PyPDF2
import docx
import openpyxl
from bs4 import BeautifulSoup
import markdown
from io import BytesIO
import base64

# Vector database and embeddings
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import faiss
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    st.warning("⚠️ 需要安装 sentence-transformers 和 faiss 来使用 RAG 功能")

# RAG database setup
RAG_DB_PATH = "data/rag_documents.db"

def init_rag_database():
    """Initialize RAG database"""
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(RAG_DB_PATH)
    cursor = conn.cursor()
    
    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            file_hash TEXT UNIQUE,
            file_type TEXT,
            file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            metadata TEXT
        )
    """)
    
    # Document chunks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            chunk_index INTEGER,
            chunk_text TEXT,
            chunk_embedding BLOB,
            metadata TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    """)
    
    # Conversations with RAG
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rag_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_query TEXT,
            retrieved_chunks TEXT,
            ai_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

class DocumentProcessor:
    """Document processing class"""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._process_pdf,
            '.txt': self._process_txt,
            '.md': self._process_markdown,
            '.docx': self._process_docx,
            '.xlsx': self._process_excel,
            '.csv': self._process_csv,
            '.html': self._process_html,
            '.json': self._process_json
        }
    
    def process_document(self, file, filename: str) -> Dict[str, Any]:
        """Process uploaded document"""
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # Get file hash
        file_hash = self._get_file_hash(file)
        
        # Check if already processed
        if self._is_document_processed(file_hash):
            return {"status": "already_processed", "file_hash": file_hash}
        
        # Process document
        try:
            content = self.supported_formats[file_ext](file)
            chunks = self._chunk_text(content)
            
            # Save to database
            doc_id = self._save_document(filename, file_hash, file_ext, len(content))
            self._save_chunks(doc_id, chunks)
            
            return {
                "status": "success",
                "document_id": doc_id,
                "chunks_count": len(chunks),
                "content_length": len(content)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_file_hash(self, file) -> str:
        """Get file hash"""
        file.seek(0)
        content = file.read()
        file.seek(0)
        return hashlib.md5(content).hexdigest()
    
    def _is_document_processed(self, file_hash: str) -> bool:
        """Check if document is already processed"""
        conn = sqlite3.connect(RAG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def _process_pdf(self, file) -> str:
        """Process PDF file"""
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def _process_txt(self, file) -> str:
        """Process text file"""
        return file.read().decode('utf-8')
    
    def _process_markdown(self, file) -> str:
        """Process markdown file"""
        content = file.read().decode('utf-8')
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    def _process_docx(self, file) -> str:
        """Process Word document"""
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _process_excel(self, file) -> str:
        """Process Excel file"""
        workbook = openpyxl.load_workbook(file)
        text = ""
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text += f"Sheet: {sheet_name}\n"
            for row in sheet.iter_rows(values_only=True):
                text += "\t".join([str(cell) if cell else "" for cell in row]) + "\n"
        return text
    
    def _process_csv(self, file) -> str:
        """Process CSV file"""
        df = pd.read_csv(file)
        return df.to_string()
    
    def _process_html(self, file) -> str:
        """Process HTML file"""
        content = file.read().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text()
    
    def _process_json(self, file) -> str:
        """Process JSON file"""
        content = file.read().decode('utf-8')
        data = json.loads(content)
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Split text into chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > start + chunk_size // 2:
                    end = start + break_point + 1
                    chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text.strip(),
                "start": start,
                "end": end,
                "metadata": {
                    "chunk_size": len(chunk_text),
                    "position": len(chunks)
                }
            })
            
            start = end - overlap
        
        return chunks
    
    def _save_document(self, filename: str, file_hash: str, file_type: str, file_size: int) -> int:
        """Save document metadata to database"""
        conn = sqlite3.connect(RAG_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (filename, file_hash, file_type, file_size, processed)
            VALUES (?, ?, ?, ?, ?)
        """, (filename, file_hash, file_type, file_size, True))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    
    def _save_chunks(self, doc_id: int, chunks: List[Dict[str, Any]]):
        """Save document chunks to database"""
        conn = sqlite3.connect(RAG_DB_PATH)
        cursor = conn.cursor()
        
        for i, chunk in enumerate(chunks):
            cursor.execute("""
                INSERT INTO document_chunks (document_id, chunk_index, chunk_text, metadata)
                VALUES (?, ?, ?, ?)
            """, (doc_id, i, chunk["text"], json.dumps(chunk["metadata"])))
        
        conn.commit()
        conn.close()

class RAGRetriever:
    """RAG retrieval system"""
    
    def __init__(self):
        self.model = None
        self.index = None
        self.chunk_embeddings = []
        self.chunk_texts = []
        
        if HAS_EMBEDDINGS:
            self._load_model()
            self._build_index()
    
    def _load_model(self):
        """Load sentence transformer model"""
        try:
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            st.error(f"无法加载嵌入模型: {e}")
            self.model = None
    
    def _build_index(self):
        """Build FAISS index from document chunks"""
        if not self.model:
            return
        
        conn = sqlite3.connect(RAG_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT chunk_text FROM document_chunks")
        chunks = cursor.fetchall()
        conn.close()
        
        if not chunks:
            return
        
        # Generate embeddings
        texts = [chunk[0] for chunk in chunks]
        embeddings = self.model.encode(texts)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        self.chunk_texts = texts
        self.chunk_embeddings = embeddings
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query"""
        if not self.model or not self.index:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Get relevant chunks
        relevant_chunks = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunk_texts):
                relevant_chunks.append({
                    "text": self.chunk_texts[idx],
                    "score": float(score),
                    "index": int(idx)
                })
        
        return relevant_chunks
    
    def get_context_for_query(self, query: str, max_chunks: int = 3) -> str:
        """Get context for a query"""
        chunks = self.retrieve_relevant_chunks(query, max_chunks)
        
        if not chunks:
            return "没有找到相关的文档内容。"
        
        context = "相关文档内容：\n\n"
        for i, chunk in enumerate(chunks, 1):
            context += f"{i}. {chunk['text']}\n\n"
        
        return context

def create_rag_interface():
    """Create RAG interface"""
    st.title("📚 智能文档问答")
    st.markdown("上传文档，然后与AI进行智能对话")
    
    # Initialize database
    init_rag_database()
    
    # Document upload section
    st.subheader("📤 文档上传")
    
    uploaded_files = st.file_uploader(
        "选择文档",
        type=['pdf', 'txt', 'md', 'docx', 'xlsx', 'csv', 'html', 'json'],
        accept_multiple_files=True,
        help="支持 PDF、Word、Excel、文本等格式"
    )
    
    if uploaded_files:
        processor = DocumentProcessor()
        
        for uploaded_file in uploaded_files:
            with st.spinner(f"正在处理 {uploaded_file.name}..."):
                result = processor.process_document(uploaded_file, uploaded_file.name)
                
                if result["status"] == "success":
                    st.success(f"✅ {uploaded_file.name} 处理成功！")
                    st.info(f"文档ID: {result['document_id']}, 分块数: {result['chunks_count']}")
                elif result["status"] == "already_processed":
                    st.warning(f"⚠️ {uploaded_file.name} 已经处理过了")
                else:
                    st.error(f"❌ {uploaded_file.name} 处理失败: {result['error']}")
    
    # Document management
    st.subheader("📋 文档管理")
    
    conn = sqlite3.connect(RAG_DB_PATH)
    documents_df = pd.read_sql_query("""
        SELECT id, filename, file_type, file_size, upload_date, processed
        FROM documents
        ORDER BY upload_date DESC
    """, conn)
    conn.close()
    
    if not documents_df.empty:
        st.dataframe(documents_df, use_container_width=True)
        
        # Delete document option
        if st.button("🗑️ 删除所有文档"):
            conn = sqlite3.connect(RAG_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM document_chunks")
            conn.commit()
            conn.close()
            st.success("所有文档已删除")
            st.rerun()
    else:
        st.info("还没有上传任何文档")
    
    # RAG Chat interface
    st.subheader("💬 智能问答")
    
    if not documents_df.empty:
        retriever = RAGRetriever()
        
        # Chat input
        user_query = st.chat_input("基于文档内容提问...")
        
        if user_query:
            # Retrieve relevant chunks
            with st.spinner("正在搜索相关文档内容..."):
                context = retriever.get_context_for_query(user_query)
            
            # Display context
            with st.expander("📖 相关文档内容"):
                st.markdown(context)
            
            # Generate response (this would integrate with your existing OpenAI integration)
            st.info("💡 这里会显示基于文档内容的AI回答")
            
            # Save conversation
            conn = sqlite3.connect(RAG_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rag_conversations (session_id, user_query, retrieved_chunks, ai_response)
                VALUES (?, ?, ?, ?)
            """, (
                st.session_state.get('session_id', 'default'),
                user_query,
                context,
                "AI response would go here"
            ))
            conn.commit()
            conn.close()
    else:
        st.warning("请先上传文档才能使用智能问答功能")

def create_rag_analytics():
    """Create RAG analytics dashboard"""
    st.subheader("📊 RAG 使用统计")
    
    conn = sqlite3.connect(RAG_DB_PATH)
    
    # Document statistics
    doc_stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_documents,
            SUM(file_size) as total_size,
            COUNT(DISTINCT file_type) as file_types
        FROM documents
    """, conn)
    
    # Chunk statistics
    chunk_stats = pd.read_sql_query("""
        SELECT COUNT(*) as total_chunks
        FROM document_chunks
    """, conn)
    
    # Query statistics
    query_stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_queries,
            COUNT(DISTINCT session_id) as unique_sessions
        FROM rag_conversations
    """, conn)
    
    conn.close()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("文档数量", doc_stats['total_documents'].iloc[0])
    
    with col2:
        total_size = doc_stats['total_size'].iloc[0]
        st.metric("总大小", f"{total_size / 1024 / 1024:.1f} MB")
    
    with col3:
        st.metric("文档块数", chunk_stats['total_chunks'].iloc[0])
    
    with col4:
        st.metric("查询次数", query_stats['total_queries'].iloc[0])
    
    # Recent queries
    st.subheader("🔍 最近查询")
    conn = sqlite3.connect(RAG_DB_PATH)
    recent_queries = pd.read_sql_query("""
        SELECT user_query, timestamp
        FROM rag_conversations
        ORDER BY timestamp DESC
        LIMIT 10
    """, conn)
    conn.close()
    
    if not recent_queries.empty:
        st.dataframe(recent_queries, use_container_width=True)
    else:
        st.info("还没有查询记录")

def export_rag_data():
    """Export RAG data"""
    conn = sqlite3.connect(RAG_DB_PATH)
    
    # Export documents
    documents_df = pd.read_sql_query("SELECT * FROM documents", conn)
    
    # Export chunks
    chunks_df = pd.read_sql_query("SELECT * FROM document_chunks", conn)
    
    # Export conversations
    conversations_df = pd.read_sql_query("SELECT * FROM rag_conversations", conn)
    
    conn.close()
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('rag_data_export.xlsx', engine='openpyxl') as writer:
        documents_df.to_excel(writer, sheet_name='Documents', index=False)
        chunks_df.to_excel(writer, sheet_name='Chunks', index=False)
        conversations_df.to_excel(writer, sheet_name='Conversations', index=False)
    
    return 'rag_data_export.xlsx'
