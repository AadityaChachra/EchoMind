# Main Chat Page
import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/ask"

st.set_page_config(page_title="EchoMind - Chat", layout="wide")


st.title("💬 EchoMind - Mental Health ChatBot")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Step2: User is able to ask question
# Chat input
user_input = st.chat_input("What's on your mind today?")
if user_input:
    # Append user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # AI Agent exists here
    try:
        response = requests.post(BACKEND_URL, json={"message": user_input})
        if response.status_code == 200:
            response_data = response.json()
            tool_info = f' WITH TOOL: [{response_data["tool_called"]}]' if response_data.get("tool_called") and response_data["tool_called"] != "None" else ""
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f'{response_data["response"]}{tool_info}'
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "Sorry, I'm having trouble connecting to the backend. Please make sure the server is running."
            })
    except requests.exceptions.ConnectionError:
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": "⚠️ Cannot connect to backend. Please start the backend server first (uv run backend/main.py)"
        })

# Step3: Show response from backend
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Create floating button that navigates to History page
# Using Streamlit button with st.switch_page for reliability
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("📜 History", key="history_btn", use_container_width=True):
        st.switch_page("pages/2_History.py")

