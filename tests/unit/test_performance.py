"""
Unit tests for performance optimization system
"""

import pytest
import sys
import os
import tempfile
import time
from unittest.mock import Mock, patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.performance import (
    PerformanceMonitor, CacheManager, cached, performance_timer,
    AsyncProcessor, perf_monitor, cache_manager
)

class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    def test_performance_monitor_init(self):
        """Test PerformanceMonitor initialization"""
        monitor = PerformanceMonitor()
        
        assert hasattr(monitor, 'metrics')
        assert hasattr(monitor, 'start_times')
        assert hasattr(monitor, 'request_counts')
        assert hasattr(monitor, 'response_times')
        
        assert isinstance(monitor.metrics, dict)
        assert isinstance(monitor.start_times, dict)
        assert isinstance(monitor.request_counts, dict)
        assert isinstance(monitor.response_times, list)
    
    def test_start_timer(self):
        """Test starting timer"""
        monitor = PerformanceMonitor()
        
        monitor.start_timer('test_operation')
        
        assert 'test_operation' in monitor.start_times
        assert isinstance(monitor.start_times['test_operation'], float)
    
    def test_end_timer(self):
        """Test ending timer"""
        monitor = PerformanceMonitor()
        
        # Start timer
        monitor.start_timer('test_operation')
        time.sleep(0.01)  # Small delay
        
        # End timer
        duration = monitor.end_timer('test_operation')
        
        assert duration > 0
        assert 'test_operation' not in monitor.start_times
        assert len(monitor.response_times) == 1
        assert len(monitor.metrics['test_operation']) == 1
    
    def test_end_timer_without_start(self):
        """Test ending timer without starting"""
        monitor = PerformanceMonitor()
        
        duration = monitor.end_timer('nonexistent_operation')
        
        assert duration == 0.0
    
    def test_increment_counter(self):
        """Test incrementing counter"""
        monitor = PerformanceMonitor()
        
        monitor.increment_counter('test_counter')
        monitor.increment_counter('test_counter', 5)
        
        assert monitor.request_counts['test_counter'] == 6
    
    def test_get_metrics(self):
        """Test getting metrics"""
        monitor = PerformanceMonitor()
        
        # Add some test data
        monitor.start_timer('test_op')
        time.sleep(0.01)
        monitor.end_timer('test_op')
        monitor.increment_counter('test_counter', 3)
        
        metrics = monitor.get_metrics()
        
        assert 'response_times' in metrics
        assert 'operation_metrics' in metrics
        assert 'counters' in metrics
        
        assert metrics['response_times']['count'] == 1
        assert metrics['response_times']['avg'] > 0
        assert metrics['counters']['test_counter'] == 3
        assert 'test_op' in metrics['operation_metrics']
    
    def test_percentile_calculation(self):
        """Test percentile calculation"""
        monitor = PerformanceMonitor()
        
        # Test with empty data
        assert monitor._percentile([], 95) == 0.0
        
        # Test with data
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert monitor._percentile(data, 50) == 5  # Median
        assert monitor._percentile(data, 95) == 10  # 95th percentile

class TestCacheManager:
    """Test cache management functionality"""
    
    def test_cache_manager_init(self, temp_dir):
        """Test CacheManager initialization"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        
        cache = CacheManager(db_path)
        
        assert cache.db_path == db_path
        assert os.path.exists(db_path)
    
    def test_serialize_deserialize(self, temp_dir):
        """Test data serialization and deserialization"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        cache = CacheManager(db_path)
        
        # Test data
        test_data = {"key": "value", "number": 123, "list": [1, 2, 3]}
        
        # Serialize
        serialized = cache._serialize(test_data)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = cache._deserialize(serialized)
        assert deserialized == test_data
    
    def test_cache_set_get(self, temp_dir):
        """Test cache set and get operations"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        cache = CacheManager(db_path)
        
        # Set value
        cache.set("test_key", "test_value", ttl=60)
        
        # Get value
        value = cache.get("test_key")
        assert value == "test_value"
    
    def test_cache_get_nonexistent(self, temp_dir):
        """Test getting non-existent cache key"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        cache = CacheManager(db_path)
        
        value = cache.get("nonexistent_key")
        assert value is None
    
    def test_cache_delete(self, temp_dir):
        """Test cache delete operation"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        cache = CacheManager(db_path)
        
        # Set and get value
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Delete value
        cache.delete("test_key")
        assert cache.get("test_key") is None
    
    def test_cache_ttl(self, temp_dir):
        """Test cache TTL functionality"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        cache = CacheManager(db_path)
        
        # Set value with short TTL
        cache.set("test_key", "test_value", ttl=1)
        
        # Should be available immediately
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("test_key") is None
    
    def test_clear_expired(self, temp_dir):
        """Test clearing expired cache entries"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        cache = CacheManager(db_path)
        
        # Set values with different TTLs
        cache.set("permanent", "value1", ttl=0)  # No expiration
        cache.set("expired", "value2", ttl=1)    # Will expire
        
        time.sleep(1.1)
        
        # Clear expired entries
        deleted_count = cache.clear_expired()
        
        assert deleted_count == 1
        assert cache.get("permanent") == "value1"
        assert cache.get("expired") is None
    
    def test_get_stats(self, temp_dir):
        """Test getting cache statistics"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        cache = CacheManager(db_path)
        
        # Add some test data
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")  # Access key1
        
        stats = cache.get_stats()
        
        assert stats['total_entries'] == 2
        assert stats['active_entries'] == 2
        assert stats['total_accesses'] >= 1

class TestCachingDecorator:
    """Test caching decorator functionality"""
    
    def test_cached_decorator(self, temp_dir):
        """Test @cached decorator"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        
        with patch('tools.performance.CACHE_DB_PATH', db_path):
            @cached(ttl=60)
            def expensive_function(x):
                time.sleep(0.01)  # Simulate expensive operation
                return x * 2
            
            # First call should be slow
            start_time = time.time()
            result1 = expensive_function(5)
            first_call_time = time.time() - start_time
            
            # Second call should be fast (cached)
            start_time = time.time()
            result2 = expensive_function(5)
            second_call_time = time.time() - start_time
            
            assert result1 == 10
            assert result2 == 10
            assert second_call_time < first_call_time
    
    def test_cached_with_different_args(self, temp_dir):
        """Test @cached decorator with different arguments"""
        db_path = os.path.join(temp_dir, "test_cache.db")
        
        with patch('tools.performance.CACHE_DB_PATH', db_path):
            @cached(ttl=60)
            def multiply(x, y):
                return x * y
            
            result1 = multiply(2, 3)
            result2 = multiply(2, 4)
            result3 = multiply(2, 3)  # Should be cached
            
            assert result1 == 6
            assert result2 == 8
            assert result3 == 6

class TestPerformanceTimer:
    """Test performance timer decorator"""
    
    def test_performance_timer_decorator(self):
        """Test @performance_timer decorator"""
        @performance_timer("test_operation")
        def test_function():
            time.sleep(0.01)
            return "test_result"
        
        result = test_function()
        
        assert result == "test_result"
        assert "test_operation" in perf_monitor.metrics
        assert len(perf_monitor.metrics["test_operation"]) == 1

class TestAsyncProcessor:
    """Test async processing functionality"""
    
    def test_async_processor_init(self):
        """Test AsyncProcessor initialization"""
        processor = AsyncProcessor()
        
        assert processor.session is None
        assert processor.loop is None
    
    @pytest.mark.asyncio
    async def test_init_session(self):
        """Test initializing aiohttp session"""
        processor = AsyncProcessor()
        
        await processor.init_session()
        
        assert processor.session is not None
        
        await processor.close_session()
        assert processor.session is None
    
    @pytest.mark.asyncio
    async def test_fetch_url_mock(self):
        """Test fetching URL with mocked response"""
        processor = AsyncProcessor()
        
        # Mock aiohttp session
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.content_type = "application/json"
        mock_response.headers = {"Content-Type": "application/json"}
        
        processor.session = Mock()
        processor.session.get.return_value.__aenter__.return_value = mock_response
        
        result = await processor.fetch_url("http://test.com")
        
        assert result["status"] == 200
        assert result["data"] == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_process_multiple_requests(self):
        """Test processing multiple requests"""
        processor = AsyncProcessor()
        
        # Mock session and responses
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.content_type = "application/json"
        mock_response.headers = {}
        
        processor.session = Mock()
        processor.session.get.return_value.__aenter__.return_value = mock_response
        
        requests = ["http://test1.com", "http://test2.com"]
        results = await processor.process_multiple_requests(requests)
        
        assert len(results) == 2
        assert all(result["status"] == 200 for result in results)

