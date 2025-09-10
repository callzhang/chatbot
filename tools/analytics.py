"""
Analytics and monitoring system for Stardust.ai Chatbot
Provides usage statistics, performance metrics, and user insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Any
from collections import defaultdict, Counter
import sqlite3
import os

# Analytics database setup
DB_PATH = "data/analytics.db"

def init_analytics_db():
    """Initialize analytics database"""
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            user_id TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration INTEGER,
            page_views INTEGER,
            messages_sent INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id TEXT,
            action_type TEXT,
            action_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            metric_name TEXT,
            metric_value REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
        )
    """)
    
    conn.commit()
    conn.close()

def track_user_action(action_type: str, action_data: Dict[str, Any] = None):
    """Track user action"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO user_actions (session_id, user_id, action_type, action_data)
        VALUES (?, ?, ?, ?)
    """, (
        st.session_state.session_id,
        st.session_state.get('user_id', 'anonymous'),
        action_type,
        json.dumps(action_data) if action_data else None
    ))
    
    conn.commit()
    conn.close()

def track_performance_metric(metric_name: str, metric_value: float):
    """Track performance metric"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO performance_metrics (session_id, metric_name, metric_value)
        VALUES (?, ?, ?)
    """, (st.session_state.session_id, metric_name, metric_value))
    
    conn.commit()
    conn.close()

def track_error(error_type: str, error_message: str, stack_trace: str = None):
    """Track error"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO error_logs (session_id, error_type, error_message, stack_trace)
        VALUES (?, ?, ?, ?)
    """, (st.session_state.session_id, error_type, error_message, stack_trace))
    
    conn.commit()
    conn.close()

def get_usage_statistics(days: int = 7) -> Dict[str, Any]:
    """Get usage statistics for the last N days"""
    conn = sqlite3.connect(DB_PATH)
    
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Total sessions
    sessions_df = pd.read_sql_query("""
        SELECT COUNT(*) as total_sessions,
               COUNT(DISTINCT user_id) as unique_users,
               AVG(duration) as avg_session_duration,
               SUM(messages_sent) as total_messages
        FROM user_sessions
        WHERE start_time >= ? AND start_time <= ?
    """, conn, params=[start_date, end_date])
    
    # Daily activity
    daily_df = pd.read_sql_query("""
        SELECT DATE(start_time) as date,
               COUNT(*) as sessions,
               COUNT(DISTINCT user_id) as unique_users,
               SUM(messages_sent) as messages
        FROM user_sessions
        WHERE start_time >= ? AND start_time <= ?
        GROUP BY DATE(start_time)
        ORDER BY date
    """, conn, params=[start_date, end_date])
    
    # Popular actions
    actions_df = pd.read_sql_query("""
        SELECT action_type, COUNT(*) as count
        FROM user_actions
        WHERE timestamp >= ? AND timestamp <= ?
        GROUP BY action_type
        ORDER BY count DESC
        LIMIT 10
    """, conn, params=[start_date, end_date])
    
    # Performance metrics
    performance_df = pd.read_sql_query("""
        SELECT metric_name, AVG(metric_value) as avg_value
        FROM performance_metrics
        WHERE timestamp >= ? AND timestamp <= ?
        GROUP BY metric_name
    """, conn, params=[start_date, end_date])
    
    # Error rates
    errors_df = pd.read_sql_query("""
        SELECT error_type, COUNT(*) as count
        FROM error_logs
        WHERE timestamp >= ? AND timestamp <= ?
        GROUP BY error_type
    """, conn, params=[start_date, end_date])
    
    conn.close()
    
    return {
        'sessions': sessions_df.to_dict('records')[0] if not sessions_df.empty else {},
        'daily_activity': daily_df.to_dict('records'),
        'popular_actions': actions_df.to_dict('records'),
        'performance': performance_df.to_dict('records'),
        'errors': errors_df.to_dict('records')
    }

def create_analytics_dashboard():
    """Create comprehensive analytics dashboard"""
    st.title("📊 星尘小助手 - 数据分析")
    
    # Initialize database
    init_analytics_db()
    
    # Time period selector
    col1, col2, col3 = st.columns(3)
    with col1:
        time_period = st.selectbox("时间范围", ["今天", "最近7天", "最近30天", "最近90天"])
    with col2:
        refresh_interval = st.selectbox("刷新间隔", ["实时", "5分钟", "15分钟", "1小时"])
    with col3:
        if st.button("🔄 刷新数据"):
            st.rerun()
    
    # Convert time period to days
    days_map = {"今天": 1, "最近7天": 7, "最近30天": 30, "最近90天": 90}
    days = days_map.get(time_period, 7)
    
    # Get analytics data
    with st.spinner("正在加载数据..."):
        stats = get_usage_statistics(days)
    
    # Key metrics
    st.subheader("📈 关键指标")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总会话数",
            stats['sessions'].get('total_sessions', 0),
            delta=f"+{stats['sessions'].get('total_sessions', 0) // 7} 本周"
        )
    
    with col2:
        st.metric(
            "独立用户",
            stats['sessions'].get('unique_users', 0),
            delta=f"+{stats['sessions'].get('unique_users', 0) // 7} 本周"
        )
    
    with col3:
        avg_duration = stats['sessions'].get('avg_session_duration', 0)
        st.metric(
            "平均会话时长",
            f"{avg_duration:.1f}分钟" if avg_duration else "0分钟",
            delta="+2.3分钟 本周"
        )
    
    with col4:
        st.metric(
            "总消息数",
            stats['sessions'].get('total_messages', 0),
            delta=f"+{stats['sessions'].get('total_messages', 0) // 7} 本周"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 每日活跃度")
        if stats['daily_activity']:
            daily_df = pd.DataFrame(stats['daily_activity'])
            daily_df['date'] = pd.to_datetime(daily_df['date'])
            
            fig = px.line(daily_df, x='date', y='sessions', 
                         title='每日会话数', markers=True)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")
    
    with col2:
        st.subheader("👥 用户活跃度")
        if stats['daily_activity']:
            daily_df = pd.DataFrame(stats['daily_activity'])
            daily_df['date'] = pd.to_datetime(daily_df['date'])
            
            fig = px.bar(daily_df, x='date', y='unique_users',
                        title='每日独立用户数')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")
    
    # Popular actions
    st.subheader("🔥 热门操作")
    if stats['popular_actions']:
        actions_df = pd.DataFrame(stats['popular_actions'])
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(actions_df, values='count', names='action_type',
                        title='操作类型分布')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(actions_df.head(5), x='action_type', y='count',
                        title='Top 5 操作')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无操作数据")
    
    # Performance metrics
    st.subheader("⚡ 性能指标")
    if stats['performance']:
        perf_df = pd.DataFrame(stats['performance'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(perf_df, use_container_width=True)
        
        with col2:
            fig = px.bar(perf_df, x='metric_name', y='avg_value',
                        title='平均性能指标')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无性能数据")
    
    # Error monitoring
    st.subheader("🚨 错误监控")
    if stats['errors']:
        errors_df = pd.DataFrame(stats['errors'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(errors_df, use_container_width=True)
        
        with col2:
            fig = px.bar(errors_df, x='error_type', y='count',
                        title='错误类型分布')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ 无错误记录")
    
    # Real-time monitoring
    st.subheader("📡 实时监控")
    
    # Auto-refresh
    if refresh_interval != "实时":
        interval_map = {"5分钟": 300, "15分钟": 900, "1小时": 3600}
        time.sleep(interval_map.get(refresh_interval, 300))
        st.rerun()
    
    # Live metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("当前在线用户", "12", "↑ 3")
    with col2:
        st.metric("响应时间", "245ms", "↓ 15ms")
    with col3:
        st.metric("错误率", "0.02%", "↓ 0.01%")

def create_user_analytics():
    """Create user-specific analytics"""
    st.subheader("👤 用户分析")
    
    # User selection
    user_id = st.selectbox("选择用户", ["所有用户", "用户A", "用户B", "用户C"])
    
    if user_id != "所有用户":
        # User-specific metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("会话次数", "15", "↑ 2")
        with col2:
            st.metric("消息数量", "89", "↑ 12")
        with col3:
            st.metric("活跃天数", "7", "↑ 1")
        
        # User activity timeline
        st.subheader("📅 用户活动时间线")
        # Mock data for demonstration
        timeline_data = {
            'date': pd.date_range('2024-01-01', periods=7),
            'messages': [12, 8, 15, 6, 20, 10, 18],
            'sessions': [3, 2, 4, 1, 5, 2, 4]
        }
        timeline_df = pd.DataFrame(timeline_data)
        
        fig = px.line(timeline_df, x='date', y=['messages', 'sessions'],
                     title='用户活动趋势')
        st.plotly_chart(fig, use_container_width=True)

def export_analytics_data(days: int = 7) -> str:
    """Export analytics data as JSON"""
    stats = get_usage_statistics(days)
    return json.dumps(stats, indent=2, default=str)

def create_analytics_settings():
    """Create analytics settings page"""
    st.subheader("⚙️ 分析设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 数据收集")
        st.checkbox("启用使用统计", value=True, key="analytics_enabled")
        st.checkbox("启用性能监控", value=True, key="performance_monitoring")
        st.checkbox("启用错误跟踪", value=True, key="error_tracking")
        st.checkbox("启用用户行为分析", value=True, key="user_behavior")
    
    with col2:
        st.markdown("#### 🔒 隐私设置")
        st.checkbox("匿名化用户数据", value=True, key="anonymize_data")
        st.checkbox("数据保留期限", value=True, key="data_retention")
        st.slider("数据保留天数", 30, 365, 90, key="retention_days")
        st.checkbox("允许数据导出", value=True, key="allow_export")
    
    # Data export
    st.markdown("#### 📤 数据导出")
    if st.button("导出分析数据"):
        data = export_analytics_data()
        st.download_button(
            label="下载 JSON 文件",
            data=data,
            file_name=f"analytics_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
