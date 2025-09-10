"""
Performance optimization utilities for Stardust.ai Chatbot
Provides caching, async processing, and performance monitoring
"""

import streamlit as st
import asyncio
import aiohttp
import time
import functools
import threading
from typing import Dict, Any, Optional, Callable
import json
import sqlite3
import os
from datetime import datetime, timedelta
import hashlib
import pickle
import gzip

# Cache configuration
CACHE_DB_PATH = "data/cache.db"
CACHE_TTL = 3600  # 1 hour default TTL

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        self.request_counts = {}
        self.response_times = []
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing and record the duration"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.response_times.append(duration)
            
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(duration)
            
            del self.start_times[operation]
            return duration
        return 0.0
    
    def increment_counter(self, counter: str, value: int = 1):
        """Increment a counter metric"""
        if counter not in self.request_counts:
            self.request_counts[counter] = 0
        self.request_counts[counter] += value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "response_times": {
                "avg": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                "min": min(self.response_times) if self.response_times else 0,
                "max": max(self.response_times) if self.response_times else 0,
                "p95": self._percentile(self.response_times, 95) if self.response_times else 0,
                "count": len(self.response_times)
            },
            "operation_metrics": {
                op: {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
                for op, times in self.metrics.items()
            },
            "counters": self.request_counts.copy()
        }
    
    def _percentile(self, data: list, percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

# Global performance monitor
perf_monitor = PerformanceMonitor()

class CacheManager:
    """Advanced caching system with TTL and compression"""
    
    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize cache database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
        """)
        
        conn.commit()
        conn.close()
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data with compression"""
        serialized = pickle.dumps(data)
        return gzip.compress(serialized)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize compressed data"""
        decompressed = gzip.decompress(data)
        return pickle.loads(decompressed)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value, expires_at FROM cache 
            WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
        """, (key, datetime.now()))
        
        result = cursor.fetchone()
        
        if result:
            # Update access statistics
            cursor.execute("""
                UPDATE cache 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE key = ?
            """, (datetime.now(), key))
            conn.commit()
            
            conn.close()
            return self._deserialize(result[0])
        
        conn.close()
        return None
    
    def set(self, key: str, value: Any, ttl: int = CACHE_TTL):
        """Set value in cache with TTL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        serialized_value = self._serialize(value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, expires_at)
            VALUES (?, ?, ?)
        """, (key, serialized_value, expires_at))
        
        conn.commit()
        conn.close()
    
    def delete(self, key: str):
        """Delete key from cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        conn.close()
    
    def clear_expired(self):
        """Clear expired cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE expires_at < ?", (datetime.now(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cache")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cache WHERE expires_at > ?", (datetime.now(),))
        active_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(access_count) FROM cache")
        total_accesses = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(access_count) FROM cache")
        avg_accesses = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": total_entries - active_entries,
            "total_accesses": total_accesses,
            "avg_accesses_per_entry": avg_accesses
        }

# Global cache manager
cache_manager = CacheManager()

def cached(ttl: int = CACHE_TTL, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                perf_monitor.increment_counter("cache_hits")
                return cached_result
            
            # Execute function and cache result
            perf_monitor.increment_counter("cache_misses")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

class AsyncProcessor:
    """Async processing utilities"""
    
    def __init__(self):
        self.session = None
        self.loop = None
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch URL asynchronously"""
        await self.init_session()
        
        try:
            async with self.session.get(url, **kwargs) as response:
                return {
                    "status": response.status,
                    "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {"error": str(e), "status": 500}
    
    async def process_multiple_requests(self, requests: list) -> list:
        """Process multiple requests concurrently"""
        await self.init_session()
        
        tasks = []
        for req in requests:
            if isinstance(req, str):
                task = self.fetch_url(req)
            else:
                task = self.fetch_url(req["url"], **req.get("kwargs", {}))
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)

# Global async processor
async_processor = AsyncProcessor()

def performance_timer(operation: str):
    """Decorator for timing function execution"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            perf_monitor.start_timer(operation)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                perf_monitor.end_timer(operation)
        
        return wrapper
    return decorator

def create_performance_dashboard():
    """Create performance monitoring dashboard"""
    st.title("⚡ 性能监控")
    
    # Performance metrics
    metrics = perf_monitor.get_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_response_time = metrics["response_times"]["avg"]
        st.metric("平均响应时间", f"{avg_response_time:.2f}s")
    
    with col2:
        p95_response_time = metrics["response_times"]["p95"]
        st.metric("P95响应时间", f"{p95_response_time:.2f}s")
    
    with col3:
        total_requests = metrics["response_times"]["count"]
        st.metric("总请求数", total_requests)
    
    with col4:
        cache_hits = metrics["counters"].get("cache_hits", 0)
        cache_misses = metrics["counters"].get("cache_misses", 0)
        hit_rate = cache_hits / (cache_hits + cache_misses) * 100 if (cache_hits + cache_misses) > 0 else 0
        st.metric("缓存命中率", f"{hit_rate:.1f}%")
    
    # Response time distribution
    st.subheader("📊 响应时间分布")
    if metrics["response_times"]["count"] > 0:
        response_times = perf_monitor.response_times[-100:]  # Last 100 requests
        
        import plotly.express as px
        import pandas as pd
        
        df = pd.DataFrame({"response_time": response_times})
        fig = px.histogram(df, x="response_time", nbins=20, title="响应时间分布")
        st.plotly_chart(fig, use_container_width=True)
    
    # Operation metrics
    st.subheader("🔧 操作性能")
    if metrics["operation_metrics"]:
        op_data = []
        for op, data in metrics["operation_metrics"].items():
            op_data.append({
                "operation": op,
                "avg_time": data["avg"],
                "count": data["count"]
            })
        
        if op_data:
            import pandas as pd
            df = pd.DataFrame(op_data)
            st.dataframe(df, use_container_width=True)
    
    # Cache statistics
    st.subheader("💾 缓存统计")
    cache_stats = cache_manager.get_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("缓存条目", cache_stats["total_entries"])
    
    with col2:
        st.metric("活跃条目", cache_stats["active_entries"])
    
    with col3:
        st.metric("总访问次数", cache_stats["total_accesses"])
    
    # Cache management
    st.subheader("🗑️ 缓存管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("清理过期缓存"):
            deleted = cache_manager.clear_expired()
            st.success(f"已清理 {deleted} 个过期条目")
    
    with col2:
        if st.button("清空所有缓存"):
            # This would need to be implemented
            st.warning("清空缓存功能需要实现")
    
    with col3:
        if st.button("刷新统计"):
            st.rerun()

def optimize_streamlit_performance():
    """Apply Streamlit performance optimizations"""
    
    # Set Streamlit configuration for better performance
    st.set_page_config(
        page_title="星尘小助手",
        page_icon="🌟",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add performance CSS
    st.markdown("""
    <style>
    /* Performance optimizations */
    .stApp {
        background-attachment: fixed;
    }
    
    /* Reduce animations for better performance */
    * {
        animation-duration: 0.1s !important;
        transition-duration: 0.1s !important;
    }
    
    /* Optimize scrolling */
    .main .block-container {
        scroll-behavior: smooth;
    }
    
    /* Reduce shadow effects */
    .stChatMessage {
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def create_async_chat_interface():
    """Create async chat interface for better performance"""
    
    st.subheader("🚀 异步聊天界面")
    
    # Chat input
    user_input = st.chat_input("输入消息...")
    
    if user_input:
        # Process asynchronously
        with st.spinner("正在处理..."):
            # This would integrate with your existing chat logic
            # but process requests asynchronously
            st.info("异步处理功能需要与现有聊天逻辑集成")
    
    # Performance tips
    with st.expander("💡 性能优化建议"):
        st.markdown("""
        ### 性能优化建议
        
        1. **启用缓存**: 使用 `@cached` 装饰器缓存重复请求
        2. **异步处理**: 使用异步函数处理多个请求
        3. **批量操作**: 合并多个小请求为一个大请求
        4. **懒加载**: 延迟加载非关键内容
        5. **压缩数据**: 使用 gzip 压缩传输数据
        6. **CDN加速**: 使用 CDN 加速静态资源
        7. **数据库优化**: 使用索引和查询优化
        8. **监控性能**: 定期检查性能指标
        """)

# Initialize performance monitoring
def init_performance_monitoring():
    """Initialize performance monitoring"""
    # Clear expired cache entries on startup
    cache_manager.clear_expired()
    
    # Set up performance monitoring
    perf_monitor.increment_counter("app_startup")
    
    # Apply Streamlit optimizations
    optimize_streamlit_performance()

# Example usage functions
@cached(ttl=300)  # Cache for 5 minutes
def expensive_calculation(data: str) -> str:
    """Example expensive calculation with caching"""
    time.sleep(1)  # Simulate expensive operation
    return f"Processed: {data}"

@performance_timer("api_call")
def api_call(url: str) -> Dict[str, Any]:
    """Example API call with performance timing"""
    # Simulate API call
    time.sleep(0.5)
    return {"status": "success", "data": "example"}

# Initialize on import
init_performance_monitoring()
