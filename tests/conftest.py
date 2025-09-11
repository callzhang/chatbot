"""
Pytest configuration and fixtures for Stardust.ai Chatbot tests
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch
import streamlit as st

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_streamlit_session():
    """Mock Streamlit session state"""
    with patch.object(st, 'session_state', {}):
        yield st.session_state

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 100
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def sample_document():
    """Sample document for testing"""
    return {
        "filename": "test.pdf",
        "content": "This is a test document content for RAG testing.",
        "file_type": "pdf",
        "file_size": 1024
    }

@pytest.fixture
def sample_chat_history():
    """Sample chat history for testing"""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "What is AI?"},
        {"role": "assistant", "content": "AI is artificial intelligence..."}
    ]

@pytest.fixture
def mock_analytics_data():
    """Mock analytics data"""
    return {
        "sessions": {
            "total_sessions": 100,
            "unique_users": 50,
            "avg_session_duration": 5.5,
            "total_messages": 500
        },
        "daily_activity": [
            {"date": "2024-01-01", "sessions": 10, "users": 8, "messages": 50}
        ],
        "popular_actions": [
            {"action_type": "chat", "count": 300},
            {"action_type": "document_upload", "count": 50}
        ]
    }

