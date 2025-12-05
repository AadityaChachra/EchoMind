# Enhanced Chat History Page with Analytics
import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

BACKEND_URL = "http://localhost:8000"
st.set_page_config(page_title="History", layout="wide")

st.title("📜 Chat History & Analytics")
st.markdown("View your conversations, track your mental health journey, and gain insights from your interactions with EchoMind")

# Initialize session state
if "page_number" not in st.session_state:
    st.session_state.page_number = 0
if "items_per_page" not in st.session_state:
    st.session_state.items_per_page = 10

# ==================== HELPER FUNCTIONS ====================

@st.cache_data(ttl=10)
def fetch_chat_history(skip=0, limit=1000, **filters):
    """Fetch chat history from backend API with filters"""
    try:
        params = {"skip": skip, "limit": limit}
        params.update(filters)
        response = requests.get(f"{BACKEND_URL}/chats/filtered", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        st.error(f"Error fetching chats: {str(e)}")
        return []

@st.cache_data(ttl=30)
def fetch_analytics_stats():
    """Fetch analytics statistics"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats/analytics/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

@st.cache_data(ttl=30)
def fetch_sentiment_trends(days=30):
    """Fetch sentiment trends"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats/analytics/trends", params={"days": days}, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

@st.cache_data(ttl=30)
def fetch_emotion_distribution():
    """Fetch emotion distribution"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats/analytics/emotions", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

@st.cache_data(ttl=30)
def fetch_weekly_report():
    """Fetch weekly report"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats/reports/weekly", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

@st.cache_data(ttl=30)
def fetch_monthly_report():
    """Fetch monthly report"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats/reports/monthly", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

@st.cache_data(ttl=30)
def fetch_warning_signs():
    """Fetch warning signs"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats/warning-signs", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def delete_chat(chat_id):
    """Delete a chat conversation"""
    try:
        response = requests.delete(f"{BACKEND_URL}/chats/{chat_id}", timeout=10)
        if response.status_code == 200:
            st.success(f"Conversation #{chat_id} deleted successfully")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"Failed to delete conversation: {response.status_code}")
    except Exception as e:
        st.error(f"Error deleting conversation: {str(e)}")

def export_to_csv(start_date=None, end_date=None):
    """Export chats to CSV"""
    try:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = requests.get(f"{BACKEND_URL}/chats/export/csv", params=params, timeout=30)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        st.error(f"Error exporting: {str(e)}")
        return None

# ==================== SIDEBAR FILTERS ====================

with st.sidebar:
    st.header("🔍 Filters & Options")
    
    # Date Range Filter
    st.subheader("📅 Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=None, key="start_date")
    with col2:
        end_date = st.date_input("To", value=None, key="end_date")
    
    # Tool/Type Filter
    st.subheader("🔧 Filter by Type")
    filter_type = st.selectbox(
        "Conversation Type",
        ["All", "Chat", "Speech Emotion", "Facial Emotion"],
        key="filter_type"
    )
    
    # Sort Options
    st.subheader("📊 Sort By")
    sort_by = st.selectbox(
        "Sort Order",
        ["Newest First", "Oldest First", "Longest", "Shortest", "Most Positive", "Most Negative"],
        key="sort_by"
    )
    
    # Items per page
    st.subheader("📄 Display Options")
    items_per_page = st.selectbox(
        "Items per page",
        [5, 10, 20, 50],
        index=1,
        key="items_per_page"
    )
    # Don't set session state here - the widget already handles it
    
    # Export button
    st.markdown("---")
    if st.button("📥 Export to CSV", width='stretch'):
        csv_data = export_to_csv(start_date, end_date)
        if csv_data:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"echomind_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width='stretch'
            )

# ==================== MAIN CONTENT ====================

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Conversations", "📊 Analytics", "📈 Trends", "📅 Reports", "⚠️ Insights"])

# ==================== TAB 1: CONVERSATIONS ====================
with tab1:
    # Prepare filters
    filters = {}
    if start_date:
        filters["start_date"] = start_date.isoformat()
    if end_date:
        filters["end_date"] = end_date.isoformat()
    
    if filter_type != "All":
        if filter_type == "Chat":
            filters["tool_called"] = "none"
        elif filter_type == "Speech Emotion":
            filters["tool_called"] = "speech_emotion"
        elif filter_type == "Facial Emotion":
            filters["tool_called"] = "facial_emotion"
    
    sort_map = {
        "Newest First": "newest",
        "Oldest First": "oldest",
        "Longest": "longest",
        "Shortest": "shortest",
        "Most Positive": "most_positive",
        "Most Negative": "most_negative"
    }
    filters["sort_by"] = sort_map.get(sort_by, "newest")
    
    # Fetch chats with filters
    items_per_page_value = st.session_state.get("items_per_page", 10)
    skip = st.session_state.page_number * items_per_page_value
    chats = fetch_chat_history(skip=skip, limit=items_per_page_value, **filters)
    
    if chats is None:
        st.error("⚠️ Cannot connect to backend. Please make sure the server is running (uv run backend/main.py)")
    elif len(chats) == 0:
        st.info("📭 No conversations found matching your filters.")
    else:
        st.success(f"📊 Showing {len(chats)} conversations")
        
        # Search box
        search_term = st.text_input("🔍 Search conversations", placeholder="Type to search in messages...", key="search")
        
        # Filter by search
        filtered_chats = chats
        if search_term:
            search_lower = search_term.lower()
            filtered_chats = [
                chat for chat in chats
                if search_lower in chat.get("user_message", "").lower() 
                or search_lower in chat.get("assistant_response", "").lower()
            ]
            st.caption(f"Found {len(filtered_chats)} matching conversations")
        
        # Display conversations
        for idx, chat in enumerate(filtered_chats):
            # Parse timestamp
            try:
                if isinstance(chat.get("timestamp"), str):
                    timestamp = datetime.fromisoformat(chat["timestamp"].replace("Z", "+00:00"))
                else:
                    timestamp = chat.get("timestamp", datetime.now())
                formatted_time = timestamp.strftime("%B %d, %Y at %I:%M %p")
            except:
                formatted_time = str(chat.get("timestamp", "Unknown time"))
            
            # Sentiment indicator
            sentiment_score = chat.get("sentiment_score")
            sentiment_label = "Neutral"
            sentiment_color = "gray"
            if sentiment_score:
                if sentiment_score > 0.05:
                    sentiment_label = "Positive"
                    sentiment_color = "green"
                elif sentiment_score < -0.05:
                    sentiment_label = "Negative"
                    sentiment_color = "red"
            
            # Create expandable container
            with st.expander(f"💬 Conversation #{chat['id']} - {formatted_time} | {sentiment_label}", expanded=False):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**🕐 Time:** {formatted_time}")
                    if sentiment_score is not None:
                        st.markdown(f"**😊 Sentiment:** {sentiment_label} ({sentiment_score:.3f})")
                    if chat.get("tool_called"):
                        tool = chat["tool_called"]
                        if tool == "speech_emotion":
                            st.markdown("**🔧 Tool:** 🎧 Speech Emotion Analysis")
                        elif tool == "facial_emotion":
                            st.markdown("**🔧 Tool:** 😊 Facial Emotion Analysis")
                        else:
                            st.markdown(f"**🔧 Tool:** {tool}")
                
                with col2:
                    st.caption(f"ID: {chat['id']}")
                    if chat.get("conversation_length"):
                        st.caption(f"Length: {chat['conversation_length']} chars")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{chat['id']}", width='stretch'):
                        delete_chat(chat['id'])
                
                # User message
                st.markdown("**👤 You:**")
                st.info(chat.get("user_message", ""))
                
                # Assistant response
                st.markdown("**🤖 EchoMind:**")
                st.success(chat.get("assistant_response", ""))
                
                # Emotion data if available
                emotion_data = chat.get("emotion_data")
                if emotion_data:
                    st.markdown("**🎭 Detected Emotions:**")
                    emotions = emotion_data.get("emotions", [])
                    if emotions:
                        for em in emotions[:5]:  # Show top 5
                            if isinstance(em, dict):
                                label = em.get("emotion") or em.get("label", "unknown")
                                score = em.get("score", 0.0)
                                st.write(f"- **{label}**: {score:.2%}")
                
                st.divider()
        
        # Pagination
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        with col2:
            if st.button("⬅️ Previous", disabled=st.session_state.page_number == 0):
                st.session_state.page_number -= 1
                st.rerun()
        with col4:
            items_per_page_value = st.session_state.get("items_per_page", 10)
            if st.button("Next ➡️", disabled=len(chats) < items_per_page_value):
                st.session_state.page_number += 1
                st.rerun()
        with col3:
            st.caption(f"Page {st.session_state.page_number + 1}")

# ==================== TAB 2: ANALYTICS ====================
with tab2:
    st.header("📊 Conversation Analytics")
    
    stats = fetch_analytics_stats()
    if stats:
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Conversations", stats.get("total_chats", 0))
        col2.metric("Avg Length", f"{stats.get('average_length', 0):.0f} chars")
        col3.metric("Avg Sentiment", f"{stats.get('average_sentiment', 0):.3f}")
        col4.metric("Recent (7 days)", stats.get("recent_activity_7days", 0))
        
        st.markdown("---")
        
        # Sentiment Distribution
        st.subheader("😊 Sentiment Distribution")
        sentiment_dist = stats.get("sentiment_distribution", {})
        if sentiment_dist:
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(
                    values=[sentiment_dist.get("positive", 0), sentiment_dist.get("neutral", 0), sentiment_dist.get("negative", 0)],
                    names=["Positive", "Neutral", "Negative"],
                    title="Sentiment Breakdown",
                    color_discrete_map={"Positive": "green", "Neutral": "gray", "Negative": "red"}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.metric("Positive", sentiment_dist.get("positive", 0))
                st.metric("Neutral", sentiment_dist.get("neutral", 0))
                st.metric("Negative", sentiment_dist.get("negative", 0))
        
        # Tool Usage
        st.subheader("🔧 Tool Usage")
        tool_usage = stats.get("tool_usage", {})
        if tool_usage:
            fig_bar = px.bar(
                x=list(tool_usage.keys()),
                y=list(tool_usage.values()),
                title="Conversations by Tool",
                labels={"x": "Tool", "y": "Count"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Emotion Distribution
        st.subheader("🎭 Emotion Distribution")
        emotion_dist = fetch_emotion_distribution()
        if emotion_dist and emotion_dist.get("emotion_distribution"):
            emotions = emotion_dist["emotion_distribution"]
            if emotions:
                fig_emotions = px.bar(
                    x=list(emotions.keys()),
                    y=list(emotions.values()),
                    title="Detected Emotions (Speech & Facial)",
                    labels={"x": "Emotion", "y": "Frequency"}
                )
                st.plotly_chart(fig_emotions, use_container_width=True)

# ==================== TAB 3: TRENDS ====================
with tab3:
    st.header("📈 Sentiment Trends Over Time")
    
    days_option = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2, key="trend_days")
    trends = fetch_sentiment_trends(days=days_option)
    
    if trends:
        df = pd.DataFrame(trends)
        df['date'] = pd.to_datetime(df['date'])
        
        # Line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['avg_sentiment'],
            mode='lines+markers',
            name='Average Sentiment',
            line=dict(color='#667eea', width=2),
            fill='tonexty',
            fillcolor='rgba(102, 126, 234, 0.1)'
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
        fig.update_layout(
            title=f"Sentiment Trend (Last {days_option} Days)",
            xaxis_title="Date",
            yaxis_title="Sentiment Score (-1 to +1)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Calendar Heatmap (simplified)
        st.subheader("📅 Activity Heatmap")
        df['day_of_week'] = df['date'].dt.day_name()
        df['week'] = df['date'].dt.isocalendar().week
        
        heatmap_data = df.pivot_table(
            values='count',
            index='day_of_week',
            columns='week',
            aggfunc='sum',
            fill_value=0
        )
        
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Week", y="Day of Week", color="Conversations"),
            title="Conversation Activity Heatmap",
            aspect="auto"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Sentiment", f"{df['avg_sentiment'].mean():.3f}")
        col2.metric("Total Conversations", int(df['count'].sum()))
        col3.metric("Trend", "📈 Improving" if df['avg_sentiment'].iloc[-1] > df['avg_sentiment'].iloc[0] else "📉 Declining")

# ==================== TAB 4: REPORTS ====================
with tab4:
    st.header("📅 Weekly & Monthly Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Weekly Report")
        weekly = fetch_weekly_report()
        if weekly:
            st.metric("Total Conversations", weekly.get("total_conversations", 0))
            st.metric("Average Sentiment", f"{weekly.get('average_sentiment', 0):.3f}")
            breakdown = weekly.get("breakdown", {})
            if breakdown:
                st.write("**Breakdown:**")
                for key, value in breakdown.items():
                    st.write(f"- {key}: {value}")
            st.info(weekly.get("summary", ""))
    
    with col2:
        st.subheader("📅 Monthly Report")
        monthly = fetch_monthly_report()
        if monthly:
            st.metric("Total Conversations", monthly.get("total_conversations", 0))
            st.metric("Average Sentiment", f"{monthly.get('average_sentiment', 0):.3f}")
            trend = monthly.get("sentiment_trend", "stable")
            st.metric("Trend", trend.title())
            st.write(f"**First Half Avg:** {monthly.get('first_half_avg', 0):.3f}")
            st.write(f"**Second Half Avg:** {monthly.get('second_half_avg', 0):.3f}")

# ==================== TAB 5: INSIGHTS & WARNINGS ====================
with tab5:
    st.header("⚠️ Mental Health Insights")
    
    warnings = fetch_warning_signs()
    if warnings and warnings.get("warnings"):
        warning_list = warnings["warnings"]
        if warning_list:
            for warning in warning_list:
                severity = warning.get("severity", "low")
                if severity == "high":
                    st.error(f"🔴 **{warning.get('type', 'Warning')}**: {warning.get('message', '')}")
                elif severity == "medium":
                    st.warning(f"🟡 **{warning.get('type', 'Warning')}**: {warning.get('message', '')}")
                else:
                    st.info(f"🔵 **{warning.get('type', 'Info')}**: {warning.get('message', '')}")
        else:
            st.success("✅ No concerning patterns detected in recent conversations.")
    else:
        st.info("No warning data available.")
    
    st.markdown("---")
    st.subheader("💡 Progress Indicators")
    
    # Get recent sentiment trend
    recent_trends = fetch_sentiment_trends(days=14)
    if recent_trends and len(recent_trends) >= 2:
        recent_avg = sum(t['avg_sentiment'] for t in recent_trends[:7]) / 7
        older_avg = sum(t['avg_sentiment'] for t in recent_trends[7:14]) / 7 if len(recent_trends) >= 14 else recent_avg
        
        if recent_avg > older_avg + 0.1:
            st.success("📈 **Positive Progress**: Your recent sentiment shows improvement compared to the previous week!")
        elif recent_avg < older_avg - 0.1:
            st.warning("📉 **Attention Needed**: Your recent sentiment has declined. Consider reaching out for support.")
        else:
            st.info("➡️ **Stable**: Your sentiment has remained relatively stable.")

# ==================== SUMMARY FEATURE (Existing) ====================
st.markdown("---")
if st.button("📊 Generate AI Summary", width='stretch', type="primary"):
    chats = fetch_chat_history(limit=100)
    if chats:
        try:
            chat_data = [{"id": c["id"], "user_message": c.get("user_message", ""), 
                         "assistant_response": c.get("assistant_response", ""), 
                         "tool_called": c.get("tool_called"), "timestamp": c.get("timestamp")} 
                        for c in chats]
            response = requests.post(f"{BACKEND_URL}/summarize", json={"chats": chat_data}, timeout=120)
            if response.status_code == 200:
                summary = response.json().get("summary", "")
                st.info(summary)
            else:
                st.error("Failed to generate summary")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Navigation
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("💬 Back to Chat", width='stretch'):
        st.switch_page("pages/1_Chat.py")
