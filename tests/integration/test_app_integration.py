"""
Integration tests for the main application
"""

import pytest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestAppIntegration:
    """Test application integration"""
    
    def test_app_imports(self):
        """Test that all modules can be imported without errors"""
        try:
            from tools import theme, mobile, analytics, rag, performance
            from tools import openai, model, dialog, utils
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import modules: {e}")
    
    def test_theme_mobile_integration(self, mock_streamlit_session):
        """Test integration between theme and mobile systems"""
        from tools.theme import initialize_theme, set_theme
        from tools.mobile import export_mobile_config, import_mobile_config
        
        # Initialize theme
        initialize_theme()
        set_theme('dark')
        
        # Set mobile config
        mock_streamlit_session.update({
            'haptic_feedback': True,
            'font_size': 16
        })
        
        # Export mobile config
        mobile_config = export_mobile_config()
        
        # Verify integration
        assert 'haptic_feedback' in mobile_config
        assert mobile_config['haptic_feedback'] is True
    
    def test_analytics_rag_integration(self, temp_dir):
        """Test integration between analytics and RAG systems"""
        from tools.analytics import init_analytics_db, track_user_action
        from tools.rag import init_rag_database, DocumentProcessor
        
        # Initialize both databases
        with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
            with patch('tools.rag.RAG_DB_PATH', os.path.join(temp_dir, "rag.db")):
                init_analytics_db()
                init_rag_database()
                
                # Track document upload action
                track_user_action('document_upload', {'filename': 'test.pdf'})
                
                # Verify both systems work together
                assert True  # If we get here, integration works
    
    def test_performance_analytics_integration(self, temp_dir):
        """Test integration between performance and analytics systems"""
        from tools.performance import PerformanceMonitor, CacheManager
        from tools.analytics import init_analytics_db, track_performance_metric
        
        # Initialize systems
        with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
            init_analytics_db()
            
            # Use performance monitoring
            monitor = PerformanceMonitor()
            monitor.start_timer('test_operation')
            monitor.end_timer('test_operation')
            
            # Track performance metric
            track_performance_metric('response_time', 1.5)
            
            # Verify integration
            assert len(monitor.response_times) == 1
            assert monitor.response_times[0] > 0
    
    def test_theme_performance_integration(self):
        """Test integration between theme and performance systems"""
        from tools.theme import apply_theme_css
        from tools.performance import performance_timer
        
        @performance_timer("theme_application")
        def apply_theme():
            apply_theme_css('light')
            return True
        
        result = apply_theme()
        
        assert result is True
        assert "theme_application" in perf_monitor.metrics
    
    def test_mobile_analytics_integration(self, mock_streamlit_session):
        """Test integration between mobile and analytics systems"""
        from tools.mobile import detect_mobile_device, export_mobile_config
        from tools.analytics import track_user_action
        
        # Set up session
        mock_streamlit_session['session_id'] = 'test_session'
        mock_streamlit_session['user_id'] = 'test_user'
        
        # Detect mobile device
        is_mobile = detect_mobile_device()
        
        # Track mobile usage
        track_user_action('mobile_access', {'is_mobile': is_mobile})
        
        # Export mobile config
        config = export_mobile_config()
        
        # Verify integration
        assert isinstance(is_mobile, bool)
        assert isinstance(config, dict)
    
    def test_rag_performance_integration(self, temp_dir):
        """Test integration between RAG and performance systems"""
        from tools.rag import DocumentProcessor
        from tools.performance import cached, performance_timer
        
        @cached(ttl=300)
        @performance_timer("document_processing")
        def process_document_mock(filename):
            # Mock document processing
            return {"status": "success", "chunks": 5}
        
        # Process document
        result = process_document_mock("test.pdf")
        
        # Verify integration
        assert result["status"] == "success"
        assert "document_processing" in perf_monitor.metrics
    
    def test_full_workflow_integration(self, temp_dir, mock_streamlit_session):
        """Test complete workflow integration"""
        from tools.theme import initialize_theme, set_theme
        from tools.mobile import detect_mobile_device
        from tools.analytics import init_analytics_db, track_user_action
        from tools.performance import performance_timer
        
        # Set up session
        mock_streamlit_session['session_id'] = 'workflow_test'
        mock_streamlit_session['user_id'] = 'test_user'
        
        # Initialize theme
        initialize_theme()
        set_theme('stardust')
        
        # Detect device
        is_mobile = detect_mobile_device()
        
        # Initialize analytics
        with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
            init_analytics_db()
            
            @performance_timer("full_workflow")
            def execute_workflow():
                # Track user action
                track_user_action('workflow_start', {
                    'theme': 'stardust',
                    'is_mobile': is_mobile
                })
                return True
            
            result = execute_workflow()
            
            # Verify complete integration
            assert result is True
            assert "full_workflow" in perf_monitor.metrics
            assert mock_streamlit_session['theme'] == 'stardust'
    
    def test_error_handling_integration(self):
        """Test error handling across integrated systems"""
        from tools.theme import set_theme
        from tools.performance import performance_timer
        
        @performance_timer("error_test")
        def function_with_error():
            # Set invalid theme (should not crash)
            result = set_theme('invalid_theme')
            assert result is False
            
            # This should not raise an exception
            return True
        
        result = function_with_error()
        
        # Verify error handling works
        assert result is True
        assert "error_test" in perf_monitor.metrics
    
    def test_configuration_integration(self, temp_dir):
        """Test configuration integration across systems"""
        from tools.theme import THEMES
        from tools.mobile import MOBILE_NAV_ITEMS
        from tools.performance import CACHE_TTL
        
        # Verify all systems have proper configurations
        assert len(THEMES) > 0
        assert len(MOBILE_NAV_ITEMS) > 0
        assert CACHE_TTL > 0
        
        # Verify theme configurations are valid
        for theme_name, config in THEMES.items():
            assert 'primaryColor' in config
            assert 'backgroundColor' in config
            assert config['primaryColor'].startswith('#')
            assert config['backgroundColor'].startswith('#')
        
        # Verify mobile navigation items are valid
        for item in MOBILE_NAV_ITEMS:
            assert 'icon' in item
            assert 'label' in item
            assert 'page' in item

