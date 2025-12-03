import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/ask"

st.set_page_config(page_title="EchoMind - Chat", layout="wide")

st.title("💬 EchoMind - Mental Health ChatBot")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown("Talk to EchoMind using text. For voice-based emotion analysis, use the **Voice** page in the sidebar.")
st.markdown("---")

# Text chat input
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

# Show conversation
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


