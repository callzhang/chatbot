"""
Unit tests for analytics and monitoring system
"""

import pytest
import sys
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.analytics import (
    init_analytics_db, track_user_action, track_performance_metric,
    track_error, get_usage_statistics
)

class TestAnalytics:
    """Test analytics functionality"""
    
    def test_init_analytics_db(self, temp_dir):
        """Test analytics database initialization"""
        db_path = os.path.join(temp_dir, "test_analytics.db")
        
        # Mock the global DB_PATH
        with patch('tools.analytics.DB_PATH', db_path):
            init_analytics_db()
            
            # Verify database was created
            assert os.path.exists(db_path)
            
            # Verify tables were created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'user_sessions' in tables
            assert 'user_actions' in tables
            assert 'performance_metrics' in tables
            assert 'error_logs' in tables
            
            conn.close()
    
    def test_track_user_action(self, temp_dir, mock_streamlit_session):
        """Test tracking user actions"""
        db_path = os.path.join(temp_dir, "test_analytics.db")
        mock_streamlit_session['session_id'] = 'test_session_123'
        mock_streamlit_session['user_id'] = 'test_user_456'
        
        with patch('tools.analytics.DB_PATH', db_path):
            init_analytics_db()
            
            # Track an action
            track_user_action('chat_message', {'message': 'Hello'})
            
            # Verify action was recorded
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM user_actions WHERE session_id = ?", ('test_session_123',))
            actions = cursor.fetchall()
            
            assert len(actions) == 1
            assert actions[0][2] == 'test_user_456'  # user_id
            assert actions[0][3] == 'chat_message'   # action_type
            
            conn.close()
    
    def test_track_performance_metric(self, temp_dir, mock_streamlit_session):
        """Test tracking performance metrics"""
        db_path = os.path.join(temp_dir, "test_analytics.db")
        mock_streamlit_session['session_id'] = 'test_session_123'
        
        with patch('tools.analytics.DB_PATH', db_path):
            init_analytics_db()
            
            # Track a performance metric
            track_performance_metric('response_time', 1.5)
            
            # Verify metric was recorded
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM performance_metrics WHERE session_id = ?", ('test_session_123',))
            metrics = cursor.fetchall()
            
            assert len(metrics) == 1
            assert metrics[0][2] == 'response_time'  # metric_name
            assert metrics[0][3] == 1.5             # metric_value
            
            conn.close()
    
    def test_track_error(self, temp_dir, mock_streamlit_session):
        """Test tracking errors"""
        db_path = os.path.join(temp_dir, "test_analytics.db")
        mock_streamlit_session['session_id'] = 'test_session_123'
        
        with patch('tools.analytics.DB_PATH', db_path):
            init_analytics_db()
            
            # Track an error
            track_error('API_ERROR', 'Connection timeout', 'Traceback...')
            
            # Verify error was recorded
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM error_logs WHERE session_id = ?", ('test_session_123',))
            errors = cursor.fetchall()
            
            assert len(errors) == 1
            assert errors[0][2] == 'API_ERROR'      # error_type
            assert errors[0][3] == 'Connection timeout'  # error_message
            assert errors[0][4] == 'Traceback...'   # stack_trace
            
            conn.close()
    
    def test_get_usage_statistics(self, temp_dir, mock_analytics_data):
        """Test getting usage statistics"""
        db_path = os.path.join(temp_dir, "test_analytics.db")
        
        with patch('tools.analytics.DB_PATH', db_path):
            init_analytics_db()
            
            # Insert test data
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insert test session
            cursor.execute("""
                INSERT INTO user_sessions (session_id, user_id, start_time, end_time, duration, page_views, messages_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('session_1', 'user_1', datetime.now() - timedelta(days=1), datetime.now(), 300, 5, 10))
            
            # Insert test actions
            cursor.execute("""
                INSERT INTO user_actions (session_id, user_id, action_type, action_data)
                VALUES (?, ?, ?, ?)
            """, ('session_1', 'user_1', 'chat', '{"message": "Hello"}'))
            
            # Insert test performance metrics
            cursor.execute("""
                INSERT INTO performance_metrics (session_id, metric_name, metric_value)
                VALUES (?, ?, ?)
            """, ('session_1', 'response_time', 1.5))
            
            conn.commit()
            conn.close()
            
            # Get statistics
            stats = get_usage_statistics(days=7)
            
            # Verify statistics structure
            assert 'sessions' in stats
            assert 'daily_activity' in stats
            assert 'popular_actions' in stats
            assert 'performance' in stats
            assert 'errors' in stats
            
            # Verify sessions data
            assert stats['sessions']['total_sessions'] == 1
            assert stats['sessions']['unique_users'] == 1
            assert stats['sessions']['total_messages'] == 10
    
    def test_analytics_data_validation(self):
        """Test analytics data validation"""
        # Test that analytics functions handle invalid data gracefully
        try:
            track_user_action('', None)
            track_performance_metric('', -1)
            track_error('', '', '')
            assert True
        except Exception as e:
            pytest.fail(f"Analytics functions should handle invalid data gracefully: {e}")
    
    def test_database_connection_handling(self, temp_dir):
        """Test database connection error handling"""
        # Test with invalid database path
        invalid_db_path = "/invalid/path/analytics.db"
        
        with patch('tools.analytics.DB_PATH', invalid_db_path):
            # These should not raise exceptions
            try:
                track_user_action('test', {})
                track_performance_metric('test', 1.0)
                track_error('test', 'test', 'test')
                assert True
            except Exception as e:
                pytest.fail(f"Analytics functions should handle database errors gracefully: {e}")

