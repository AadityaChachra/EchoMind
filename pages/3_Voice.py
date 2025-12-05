import streamlit as st
import requests

from st_audiorec import st_audiorec

BACKEND_AUDIO_URL = "http://localhost:8000/analyze_audio"

st.set_page_config(page_title="EchoMind - Speech Emotion", layout="wide")

st.title("🎧 EchoMind - Speech Emotion Analysis")
st.markdown(
    "Record your voice and let EchoMind estimate your emotional tone. "
    "Results are approximate, based on vocal characteristics only, and **not** a diagnosis."
)

# Record section
st.markdown("### 🎤 Record a voice note")
col_rec, col_info = st.columns([2, 3])

with col_rec:
    st.markdown("Click below to record a short voice note (5–30 seconds).")
    audio_bytes = st_audiorec()

with col_info:
    if audio_bytes is not None:
        st.audio(audio_bytes, format="audio/wav")
        if st.button("🔍 Analyze Voice Emotions", key="analyze_voice_btn", width='stretch'):
            with st.spinner("Analyzing your voice emotions..."):
                try:
                    files = {"file": ("voice_recording.wav", audio_bytes, "audio/wav")}
                    resp = requests.post(BACKEND_AUDIO_URL, files=files, timeout=120)
                    if resp.status_code == 200:
                        data = resp.json()
                        analysis = data.get("analysis") or "No analysis available."
                        primary = data.get("primary_emotion", "unknown")
                        emotions = data.get("emotions", [])
                        gpt_summary = data.get("gpt_summary") or ""

                        # Show structured result
                        st.markdown("### 🧠 Detected Emotions")
                        st.metric("Primary Emotion", primary)

                        if emotions:
                            st.markdown("#### All detected emotions")
                            for e in emotions:
                                label = e.get("label", "unknown")
                                score = e.get("score", 0.0)
                                st.write(f"- {label}: {score:.2f}")

                        if gpt_summary:
                            st.markdown("### 💬 Summary")
                            st.info(gpt_summary)
                            st.write("Want to talk more about this? Go to the **Chat** page.")

                        st.markdown("### 🔎 Detailed Analysis")
                        st.write(analysis)

                        st.success(
                            "This analysis has been saved to your history, "
                            "so you can review it later in the **History** page."
                        )
                    else:
                        st.error(f"Failed to analyze audio (status {resp.status_code}).")
                except requests.exceptions.ConnectionError:
                    st.error(
                        "⚠️ Cannot connect to backend. Please make sure the backend server is running "
                        "(uv run backend/main.py)."
                    )
                except requests.exceptions.Timeout:
                    st.error("⏱️ Audio analysis timed out. Please try again with a shorter clip.")
                except Exception as e:
                    st.error(f"Error analyzing audio: {str(e)}")


