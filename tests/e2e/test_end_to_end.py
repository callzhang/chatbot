"""
End-to-end tests for Stardust.ai Chatbot
Tests complete user workflows and scenarios
"""

import pytest
import sys
import os
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    def test_user_onboarding_workflow(self, temp_dir, mock_streamlit_session):
        """Test complete user onboarding workflow"""
        from tools.theme import initialize_theme, set_theme
        from tools.mobile import detect_mobile_device, export_mobile_config
        from tools.analytics import init_analytics_db, track_user_action
        from tools.performance import performance_timer
        
        # Set up session
        mock_streamlit_session['session_id'] = 'onboarding_test'
        mock_streamlit_session['user_id'] = 'new_user'
        
        # Initialize systems
        with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
            init_analytics_db()
            
            @performance_timer("user_onboarding")
            def complete_onboarding():
                # Step 1: Initialize theme
                initialize_theme()
                set_theme('stardust')
                
                # Step 2: Detect device
                is_mobile = detect_mobile_device()
                
                # Step 3: Configure mobile settings
                mock_streamlit_session.update({
                    'haptic_feedback': True,
                    'font_size': 16,
                    'mobile_theme': '自动'
                })
                
                # Step 4: Track onboarding completion
                track_user_action('onboarding_complete', {
                    'theme': 'stardust',
                    'is_mobile': is_mobile,
                    'haptic_feedback': True
                })
                
                return True
            
            result = complete_onboarding()
            
            # Verify onboarding completed successfully
            assert result is True
            assert mock_streamlit_session['theme'] == 'stardust'
            assert "user_onboarding" in perf_monitor.metrics
    
    def test_document_upload_and_query_workflow(self, temp_dir):
        """Test complete document upload and query workflow"""
        from tools.rag import init_rag_database, DocumentProcessor, RAGRetriever
        from tools.analytics import init_analytics_db, track_user_action
        from tools.performance import cached, performance_timer
        
        # Initialize databases
        with patch('tools.rag.RAG_DB_PATH', os.path.join(temp_dir, "rag.db")):
            with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
                init_rag_database()
                init_analytics_db()
                
                @performance_timer("document_workflow")
                @cached(ttl=300)
                def process_document_workflow():
                    # Step 1: Create mock document
                    mock_file = Mock()
                    mock_file.name = "test_document.txt"
                    mock_file.read.return_value = b"This is a test document about artificial intelligence and machine learning."
                    mock_file.seek = Mock()
                    
                    # Step 2: Process document
                    processor = DocumentProcessor()
                    result = processor.process_document(mock_file, "test_document.txt")
                    
                    # Step 3: Track document upload
                    track_user_action('document_upload', {
                        'filename': 'test_document.txt',
                        'status': result['status']
                    })
                    
                    return result
                
                result = process_document_workflow()
                
                # Verify document processing
                assert result['status'] == 'success'
                assert result['chunks_count'] > 0
                assert "document_workflow" in perf_monitor.metrics
    
    def test_theme_customization_workflow(self, mock_streamlit_session):
        """Test complete theme customization workflow"""
        from tools.theme import initialize_theme, set_theme, export_theme_config, import_theme_config
        
        @performance_timer("theme_customization")
        def customize_theme():
            # Step 1: Initialize theme
            initialize_theme()
            
            # Step 2: Try different themes
            themes_to_test = ['light', 'dark', 'stardust', 'ocean']
            for theme in themes_to_test:
                set_theme(theme)
                assert mock_streamlit_session['theme'] == theme
            
            # Step 3: Export current theme
            theme_config = export_theme_config('stardust')
            assert 'primaryColor' in theme_config
            
            # Step 4: Import custom theme
            custom_config = '{"primaryColor": "#FF0000", "backgroundColor": "#FFFFFF", "secondaryBackgroundColor": "#F0F0F0", "textColor": "#000000"}'
            import_result = import_theme_config(custom_config)
            assert import_result is True
            
            return True
        
        result = customize_theme()
        assert result is True
        assert "theme_customization" in perf_monitor.metrics
    
    def test_mobile_optimization_workflow(self, mock_streamlit_session):
        """Test complete mobile optimization workflow"""
        from tools.mobile import (
            detect_mobile_device, export_mobile_config, import_mobile_config,
            apply_mobile_optimizations
        )
        
        @performance_timer("mobile_optimization")
        def optimize_mobile():
            # Step 1: Detect device
            is_mobile = detect_mobile_device()
            
            # Step 2: Apply mobile optimizations
            apply_mobile_optimizations()
            
            # Step 3: Configure mobile settings
            mock_streamlit_session.update({
                'haptic_feedback': True,
                'auto_scroll': True,
                'voice_input': False,
                'font_size': 16,
                'mobile_theme': '深色',
                'mobile_power_save': True
            })
            
            # Step 4: Export configuration
            config = export_mobile_config()
            assert config['haptic_feedback'] is True
            assert config['font_size'] == 16
            
            # Step 5: Import configuration
            new_config = {
                'haptic_feedback': False,
                'font_size': 18,
                'mobile_theme': '浅色'
            }
            import_mobile_config(new_config)
            
            # Verify configuration was applied
            assert mock_streamlit_session['haptic_feedback'] is False
            assert mock_streamlit_session['font_size'] == 18
            
            return True
        
        result = optimize_mobile()
        assert result is True
        assert "mobile_optimization" in perf_monitor.metrics
    
    def test_analytics_monitoring_workflow(self, temp_dir, mock_streamlit_session):
        """Test complete analytics monitoring workflow"""
        from tools.analytics import (
            init_analytics_db, track_user_action, track_performance_metric,
            track_error, get_usage_statistics
        )
        from tools.performance import PerformanceMonitor
        
        # Set up session
        mock_streamlit_session['session_id'] = 'analytics_test'
        mock_streamlit_session['user_id'] = 'test_user'
        
        with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
            @performance_timer("analytics_workflow")
            def monitor_analytics():
                # Step 1: Initialize analytics
                init_analytics_db()
                
                # Step 2: Track various user actions
                track_user_action('page_view', {'page': 'home'})
                track_user_action('chat_message', {'message': 'Hello'})
                track_user_action('document_upload', {'filename': 'test.pdf'})
                
                # Step 3: Track performance metrics
                track_performance_metric('response_time', 1.2)
                track_performance_metric('memory_usage', 512)
                
                # Step 4: Track errors
                track_error('API_ERROR', 'Connection timeout', 'Traceback...')
                
                # Step 5: Get usage statistics
                stats = get_usage_statistics(days=7)
                
                # Verify statistics structure
                assert 'sessions' in stats
                assert 'daily_activity' in stats
                assert 'popular_actions' in stats
                assert 'performance' in stats
                assert 'errors' in stats
                
                return stats
            
            stats = monitor_analytics()
            assert "analytics_workflow" in perf_monitor.metrics
            assert stats is not None
    
    def test_performance_optimization_workflow(self, temp_dir):
        """Test complete performance optimization workflow"""
        from tools.performance import (
            PerformanceMonitor, CacheManager, cached, performance_timer,
            AsyncProcessor
        )
        
        @performance_timer("performance_optimization")
        def optimize_performance():
            # Step 1: Initialize performance monitoring
            monitor = PerformanceMonitor()
            
            # Step 2: Test caching
            db_path = os.path.join(temp_dir, "cache.db")
            cache = CacheManager(db_path)
            
            @cached(ttl=60)
            def expensive_operation(x):
                time.sleep(0.01)
                return x * 2
            
            # First call (cache miss)
            result1 = expensive_operation(5)
            
            # Second call (cache hit)
            result2 = expensive_operation(5)
            
            assert result1 == 10
            assert result2 == 10
            
            # Step 3: Test performance monitoring
            monitor.start_timer('test_operation')
            time.sleep(0.01)
            monitor.end_timer('test_operation')
            
            monitor.increment_counter('test_counter', 5)
            
            # Step 4: Get performance metrics
            metrics = monitor.get_metrics()
            assert 'response_times' in metrics
            assert 'operation_metrics' in metrics
            assert 'counters' in metrics
            
            # Step 5: Test cache statistics
            cache.set('test_key', 'test_value')
            cache.get('test_key')
            stats = cache.get_stats()
            
            assert stats['total_entries'] >= 1
            assert stats['total_accesses'] >= 1
            
            return True
        
        result = optimize_performance()
        assert result is True
        assert "performance_optimization" in perf_monitor.metrics
    
    def test_error_recovery_workflow(self):
        """Test error recovery and resilience workflow"""
        from tools.theme import set_theme
        from tools.performance import performance_timer
        
        @performance_timer("error_recovery")
        def test_error_recovery():
            # Step 1: Test invalid theme (should not crash)
            result = set_theme('invalid_theme')
            assert result is False
            
            # Step 2: Test with valid theme
            result = set_theme('light')
            assert result is True
            
            # Step 3: Test performance monitoring with errors
            try:
                # Simulate an error
                raise ValueError("Test error")
            except ValueError:
                # Should handle error gracefully
                pass
            
            return True
        
        result = test_error_recovery()
        assert result is True
        assert "error_recovery" in perf_monitor.metrics
    
    def test_multi_user_workflow(self, temp_dir):
        """Test multi-user workflow simulation"""
        from tools.analytics import init_analytics_db, track_user_action
        from tools.performance import performance_timer
        
        with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
            init_analytics_db()
            
            @performance_timer("multi_user_workflow")
            def simulate_multiple_users():
                # Simulate multiple users
                users = ['user1', 'user2', 'user3']
                sessions = ['session1', 'session2', 'session3']
                
                for i, (user, session) in enumerate(zip(users, sessions)):
                    # Mock session state for each user
                    with patch('tools.analytics.st.session_state', {
                        'user_id': user,
                        'session_id': session
                    }):
                        # Track actions for each user
                        track_user_action('login', {'user_id': user})
                        track_user_action('chat_message', {'message': f'Hello from {user}'})
                        track_user_action('logout', {'user_id': user})
                
                return True
            
            result = simulate_multiple_users()
            assert result is True
            assert "multi_user_workflow" in perf_monitor.metrics
    
    def test_data_persistence_workflow(self, temp_dir):
        """Test data persistence across sessions workflow"""
        from tools.analytics import init_analytics_db, track_user_action, get_usage_statistics
        from tools.rag import init_rag_database, DocumentProcessor
        from tools.performance import CacheManager
        
        @performance_timer("data_persistence")
        def test_persistence():
            # Step 1: Initialize databases
            with patch('tools.analytics.DB_PATH', os.path.join(temp_dir, "analytics.db")):
                with patch('tools.rag.RAG_DB_PATH', os.path.join(temp_dir, "rag.db")):
                    init_analytics_db()
                    init_rag_database()
                    
                    # Step 2: Add data
                    with patch('tools.analytics.st.session_state', {
                        'user_id': 'persistence_user',
                        'session_id': 'persistence_session'
                    }):
                        track_user_action('data_creation', {'test': 'data'})
                    
                    # Step 3: Initialize cache
                    cache = CacheManager(os.path.join(temp_dir, "cache.db"))
                    cache.set('persistent_key', 'persistent_value', ttl=0)  # No expiration
                    
                    # Step 4: Verify data persistence
                    stats = get_usage_statistics(days=7)
                    cached_value = cache.get('persistent_key')
                    
                    assert stats is not None
                    assert cached_value == 'persistent_value'
                    
                    return True
        
        result = test_persistence()
        assert result is True
        assert "data_persistence" in perf_monitor.metrics
