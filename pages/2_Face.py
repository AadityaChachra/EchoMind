import streamlit as st
import requests

BACKEND_FACE_URL = "http://localhost:8000/analyze_face"

st.set_page_config(page_title="EchoMind - Facial Emotion", layout="wide")

st.title("😊 EchoMind - Facial Emotion Analysis")
st.markdown(
    "Capture a photo or record a video of yourself, and let EchoMind analyze your facial emotions. "
    "Results are approximate, based on facial expressions only, and **not** a diagnosis."
)

# Tabs for photo vs video
tab_photo, tab_video = st.tabs(["📷 Capture Photo", "🎥 Record Video"])

with tab_photo:
    st.markdown("### 📸 Upload or Capture a Photo")
    st.markdown("Upload an image file or use your camera to capture a photo.")
    
    col_upload, col_camera = st.columns(2)
    
    with col_upload:
        st.markdown("#### Upload Image")
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png", "bmp"],
            help="Upload a photo containing your face",
            key="photo_upload"
        )
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Image", width='stretch')
    
    with col_camera:
        st.markdown("#### Camera Capture")
        camera_photo = st.camera_input(
            "Take a photo",
            help="Allow camera access and take a photo",
            key="camera_capture"
        )
        
        if camera_photo is not None:
            st.image(camera_photo, caption="Captured Photo", width='stretch')
    
    # Analyze button for photo
    photo_to_analyze = uploaded_file or camera_photo
    if photo_to_analyze is not None:
        if st.button("🔍 Analyze Facial Emotions", key="analyze_photo_btn", width='stretch'):
            with st.spinner("Analyzing facial emotions..."):
                try:
                    # Reset file pointer
                    photo_to_analyze.seek(0)
                    # Use content_type if available, otherwise infer from filename
                    content_type = getattr(photo_to_analyze, 'content_type', None) or getattr(photo_to_analyze, 'type', None) or 'image/jpeg'
                    files = {"file": (photo_to_analyze.name, photo_to_analyze.read(), content_type)}
                    resp = requests.post(BACKEND_FACE_URL, files=files, timeout=120)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        primary = data.get("primary_emotion", "unknown")
                        emotions = data.get("emotions", [])
                        gpt_summary = data.get("gpt_summary") or ""
                        analysis = data.get("analysis") or "No analysis available."
                        
                        # Show structured result
                        st.markdown("### 🧠 Detected Emotions")
                        
                        if primary == "no_face_detected":
                            st.warning("⚠️ No face detected in the image. Please ensure your face is clearly visible.")
                        else:
                            st.metric("Primary Emotion", primary)
                            
                            if emotions:
                                st.markdown("#### All detected emotions")
                                for e in emotions:
                                    emotion_name = e.get("emotion", "unknown")
                                    score = e.get("score", 0.0)
                                    st.write(f"- **{emotion_name}**: {score:.2%}")
                            
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
                        error_msg = resp.json().get("detail", f"Status {resp.status_code}")
                        st.error(f"Failed to analyze image: {error_msg}")
                        
                except requests.exceptions.ConnectionError:
                    st.error(
                        "⚠️ Cannot connect to backend. Please make sure the backend server is running "
                        "(uv run backend/main.py)."
                    )
                except requests.exceptions.Timeout:
                    st.error("⏱️ Facial emotion analysis timed out. Please try again.")
                except Exception as e:
                    st.error(f"Error analyzing image: {str(e)}")

with tab_video:
    st.markdown("### 🎥 Record or Upload a Video")
    st.markdown("Record a short video or upload a video file. The middle frame will be analyzed.")
    
    col_record, col_upload_vid = st.columns(2)
    
    with col_record:
        st.markdown("#### Record Video")
        st.info("💡 Video recording is available via file upload. Use the upload option below.")
    
    with col_upload_vid:
        st.markdown("#### Upload Video")
        uploaded_video = st.file_uploader(
            "Choose a video file",
            type=["mp4", "avi", "mov", "mkv"],
            help="Upload a video containing your face. The middle frame will be analyzed.",
            key="video_upload"
        )
        
        if uploaded_video is not None:
            st.video(uploaded_video)
            st.caption("The middle frame of this video will be analyzed for emotions.")
    
    # Analyze button for video
    if uploaded_video is not None:
        if st.button("🔍 Analyze Facial Emotions from Video", key="analyze_video_btn", width='stretch'):
            with st.spinner("Extracting frame and analyzing facial emotions..."):
                try:
                    # Reset file pointer
                    uploaded_video.seek(0)
                    # Use content_type if available, otherwise infer from filename
                    content_type = getattr(uploaded_video, 'content_type', None) or getattr(uploaded_video, 'type', None) or 'video/mp4'
                    files = {"file": (uploaded_video.name, uploaded_video.read(), content_type)}
                    resp = requests.post(BACKEND_FACE_URL, files=files, timeout=120)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        primary = data.get("primary_emotion", "unknown")
                        emotions = data.get("emotions", [])
                        gpt_summary = data.get("gpt_summary") or ""
                        analysis = data.get("analysis") or "No analysis available."
                        
                        # Show structured result
                        st.markdown("### 🧠 Detected Emotions")
                        
                        if primary == "no_face_detected":
                            st.warning("⚠️ No face detected in the video frame. Please ensure your face is clearly visible.")
                        else:
                            st.metric("Primary Emotion", primary)
                            
                            if emotions:
                                st.markdown("#### All detected emotions")
                                for e in emotions:
                                    emotion_name = e.get("emotion", "unknown")
                                    score = e.get("score", 0.0)
                                    st.write(f"- **{emotion_name}**: {score:.2%}")
                            
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
                        error_msg = resp.json().get("detail", f"Status {resp.status_code}")
                        st.error(f"Failed to analyze video: {error_msg}")
                        
                except requests.exceptions.ConnectionError:
                    st.error(
                        "⚠️ Cannot connect to backend. Please make sure the backend server is running "
                        "(uv run backend/main.py)."
                    )
                except requests.exceptions.Timeout:
                    st.error("⏱️ Facial emotion analysis timed out. Please try again with a shorter video.")
                except Exception as e:
                    st.error(f"Error analyzing video: {str(e)}")



