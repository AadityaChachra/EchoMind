# Chat History Page
import streamlit as st
import requests
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
st.set_page_config(page_title="EchoMind - History", layout="wide")

st.title("📜 Chat History")
st.markdown("View all your past conversations with EchoMind")

# Fetch chat history from backend
@st.cache_data(ttl=10)  # Cache for 10 seconds
def fetch_chat_history(skip=0, limit=1000):
    """Fetch chat history from backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats", params={"skip": skip, "limit": limit})
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None

# Fetch total count
def fetch_chat_count():
    """Fetch total chat count"""
    try:
        response = requests.get(f"{BACKEND_URL}/chats/count")
        if response.status_code == 200:
            return response.json().get("total_chats", 0)
        return 0
    except requests.exceptions.ConnectionError:
        return 0

# Display stats
col1, col2, col3 = st.columns(3)
total_chats = fetch_chat_count()
col1.metric("Total Conversations", total_chats)

# Fetch and display chats
chats = fetch_chat_history()

# Initialize summarize state
if "summarize_clicked" not in st.session_state:
    st.session_state["summarize_clicked"] = False
if "summary_generated" not in st.session_state:
    st.session_state["summary_generated"] = False
if "summary_text" not in st.session_state:
    st.session_state["summary_text"] = ""

# Summarize button - placed prominently
if chats and len(chats) > 0:
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("📊 Generate Summary", key="generate_summary", use_container_width=True, type="primary"):
            st.session_state["summarize_clicked"] = True
            st.session_state["summary_generated"] = False
            st.session_state["summary_text"] = ""
            st.rerun()

# Generate summary if button was clicked and not yet generated
if st.session_state.get("summarize_clicked", False) and not st.session_state.get("summary_generated", False) and chats and len(chats) > 0:
    with st.spinner("🤖 Generating comprehensive summary of your conversations..."):
        try:
            # Prepare chat data for summarization
            chat_data = []
            for chat in chats:
                chat_data.append({
                    "id": chat["id"],
                    "user_message": chat["user_message"],
                    "assistant_response": chat["assistant_response"],
                    "tool_called": chat.get("tool_called"),
                    "timestamp": chat["timestamp"]
                })
            
            # Call backend summarize endpoint
            response = requests.post(
                f"{BACKEND_URL}/summarize",
                json={"chats": chat_data},
                timeout=120  # Longer timeout for AI processing
            )
            
            if response.status_code == 200:
                summary_data = response.json()
                summary = summary_data.get("summary", "No summary available.")
                st.session_state["summary_text"] = summary
                st.session_state["summary_generated"] = True
                st.rerun()
            else:
                st.error(f"Failed to generate summary. Status code: {response.status_code}")
        except requests.exceptions.Timeout:
            st.error("⏱️ Summary generation timed out. Please try again with fewer conversations.")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend. Please make sure the server is running.")
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")

# Display summary if it has been generated
if st.session_state.get("summary_generated", False) and st.session_state.get("summary_text"):
    st.markdown("---")
    st.markdown("### 📊 Conversation Summary")
    
    # Display summary in a styled info box
    st.info(st.session_state["summary_text"])
    
    # Option to close/hide summary
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("✖️ Close Summary", key="close_summary", use_container_width=True):
            st.session_state["summarize_clicked"] = False
            st.session_state["summary_generated"] = False
            st.session_state["summary_text"] = ""
            st.rerun()

if chats is None:
    st.error("⚠️ Cannot connect to backend. Please make sure the server is running (uv run backend/main.py)")
elif len(chats) == 0:
    st.info("📭 No chat history found. Start chatting to see your conversations here!")
else:
    st.success(f"📊 Found {len(chats)} conversations")
    
    # Search/filter option
    search_term = st.text_input("🔍 Search conversations", placeholder="Type to search in messages...")
    
    # Filter chats based on search
    filtered_chats = chats
    if search_term:
        search_lower = search_term.lower()
        filtered_chats = [
            chat for chat in chats
            if search_lower in chat["user_message"].lower() 
            or search_lower in chat["assistant_response"].lower()
        ]
        st.caption(f"Showing {len(filtered_chats)} of {len(chats)} conversations")
    
    # Display each chat
    for idx, chat in enumerate(filtered_chats):
        # Parse timestamp
        try:
            if isinstance(chat["timestamp"], str):
                timestamp = datetime.fromisoformat(chat["timestamp"].replace("Z", "+00:00"))
            else:
                timestamp = chat["timestamp"]
            formatted_time = timestamp.strftime("%B %d, %Y at %I:%M %p")
        except:
            formatted_time = str(chat.get("timestamp", "Unknown time"))
        
        # Create expandable container for each chat
        with st.expander(f"💬 Conversation #{chat['id']} - {formatted_time}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**🕐 Time:** {formatted_time}")
                if chat.get("tool_called"):
                    st.markdown(f"**🔧 Tool Used:** `{chat['tool_called']}`")
            
            with col2:
                st.caption(f"ID: {chat['id']}")
            
            # User message
            st.markdown("**👤 You:**")
            st.info(chat["user_message"])
            
            # Assistant response
            st.markdown("**🤖 EchoMind:**")
            st.success(chat["assistant_response"])
            
            st.divider()

# Create floating button that navigates back to Chat
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("💬 Back to Chat", key="chat_btn", use_container_width=True):
        st.switch_page("pages/1_Chat.py")
