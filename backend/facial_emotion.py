"""
Utilities for Facial Emotion Recognition (FER) using a hybrid approach.

This module combines face detection (MTCNN or Haar Cascade) with the high-accuracy
dima806/facial_emotions_image_detection model for emotion classification.

The hybrid approach:
1. Detects faces in the image using MTCNN (preferred) or Haar Cascade (fallback)
2. Crops the largest detected face with padding
3. Classifies emotions on the cropped face using the dima806 model
"""

from typing import List, Dict, Optional
from pathlib import Path
import tempfile
import io
import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from mtcnn_opencv import MTCNN
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


# Global caches for lazy loading
_face_detector = None
_image_classifier = None


def _get_face_detector():
    """
    Lazily load face detector. Prefers MTCNN, falls back to Haar Cascade.
    
    Returns:
        Face detector object (MTCNN or Haar Cascade).
    """
    global _face_detector
    if _face_detector is None:
        if MTCNN_AVAILABLE:
            # Use MTCNN for better accuracy
            _face_detector = MTCNN()
        elif cv2 is not None:
            # Fallback to Haar Cascade (built into OpenCV)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            _face_detector = cv2.CascadeClassifier(cascade_path)
            if _face_detector.empty():
                raise RuntimeError("Failed to load Haar Cascade classifier")
        else:
            raise ImportError(
                "No face detector available. Install either:\n"
                "  - mtcnn-opencv: pip install mtcnn-opencv (recommended)\n"
                "  - opencv-python: pip install opencv-python (fallback)"
            )
    return _face_detector


def _get_image_classifier():
    """
    Lazily load the dima806 facial emotion classification model.
    
    Returns:
        Hugging Face pipeline for image classification.
    """
    global _image_classifier
    if _image_classifier is None:
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers library not installed. Install with: pip install transformers"
            )
        # Load the dima806 facial emotion detection model
        _image_classifier = pipeline(
            "image-classification",
            model="dima806/facial_emotions_image_detection"
        )
    return _image_classifier


def _detect_and_crop_face(image_array: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect the largest face in the image and crop it with padding.
    
    Args:
        image_array: RGB image as numpy array (H, W, 3).
    
    Returns:
        Cropped face image as numpy array, or None if no face detected.
    """
    detector = _get_face_detector()
    
    if MTCNN_AVAILABLE:
        # MTCNN returns list of dicts with 'box' key: [x, y, width, height]
        faces = detector.detect_faces(image_array)
        if not faces:
            return None
        
        # Get the largest face (by bounding box area)
        largest_face = max(faces, key=lambda f: f['box'][2] * f['box'][3])
        x, y, w, h = largest_face['box']
        
    else:
        # Haar Cascade returns list of (x, y, w, h) tuples
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        if len(faces) == 0:
            return None
        
        # Get the largest face (by area)
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face
    
    # Add padding (20% on each side)
    padding = int(max(w, h) * 0.2)
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(image_array.shape[1] - x, w + 2 * padding)
    h = min(image_array.shape[0] - y, h + 2 * padding)
    
    # Crop the face
    cropped_face = image_array[y:y+h, x:x+w]
    
    return cropped_face


def analyze_emotion_from_image_bytes(image_bytes: bytes) -> List[Dict]:
    """
    Analyze emotions from raw image bytes (JPEG, PNG, etc.) using hybrid approach.
    
    Process:
    1. Load image from bytes
    2. Detect and crop the largest face
    3. Classify emotions on the cropped face using dima806 model
    
    Args:
        image_bytes: Raw image data (JPEG, PNG, etc.).
    
    Returns:
        List of dicts with 'emotion' and 'score' keys, sorted by score (highest first).
        Returns empty list if no face is detected.
    """
    if cv2 is None:
        raise ImportError("OpenCV (cv2) is required. Install with: pip install opencv-python")
    
    # Load image from bytes
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Convert PIL Image to numpy array (RGB)
        image_array = np.array(image.convert("RGB"))
    except Exception as e:
        raise ValueError(f"Failed to load image: {str(e)}")
    
    # Step 1: Detect and crop face
    try:
        cropped_face = _detect_and_crop_face(image_array)
        if cropped_face is None:
            return []
    except Exception as e:
        raise ValueError(f"Failed to detect face: {str(e)}")
    
    # Step 2: Classify emotions on cropped face
    try:
        classifier = _get_image_classifier()
        
        # Convert cropped face back to PIL Image for the classifier
        face_image = Image.fromarray(cropped_face)
        
        # Get emotion predictions
        predictions = classifier(face_image)
        
        # Convert to list of dicts with 'emotion' and 'score' keys
        emotion_list = [
            {"emotion": pred["label"], "score": float(pred["score"])}
            for pred in predictions
        ]
        
        # Sort by score (highest first)
        emotion_list.sort(key=lambda x: x["score"], reverse=True)
        
        return emotion_list
        
    except Exception as e:
        raise ValueError(f"Failed to analyze emotions: {str(e)}")


def extract_frame_from_video(video_bytes: bytes) -> bytes:
    """
    Extract a single frame from video bytes for emotion analysis.
    Uses the middle frame of the video.

    Args:
        video_bytes: Raw video data.

    Returns:
        Image bytes (JPEG) of the extracted frame.
    """
    if cv2 is None:
        raise ImportError("OpenCV (cv2) is required for video processing. Install with: pip install opencv-python")
    
    try:
        # Write video bytes to temporary file
        tmp_dir = tempfile.gettempdir()
        tmp_video_path = Path(tmp_dir) / "echomind_video_tmp.mp4"
        
        with open(tmp_video_path, "wb") as f:
            f.write(video_bytes)
        
        try:
            # Read video
            cap = cv2.VideoCapture(str(tmp_video_path))
            
            if not cap.isOpened():
                raise ValueError("Could not open video file")
            
            # Get total frames
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                raise ValueError("Video has no frames")
            
            # Extract middle frame
            middle_frame = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                raise ValueError("Could not read frame from video")
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image and then to JPEG bytes
            image = Image.fromarray(frame_rgb)
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
            
            return img_bytes.read()
            
        finally:
            # Cleanup
            try:
                tmp_video_path.unlink()
            except OSError:
                pass
                
    except Exception as e:
        raise ValueError(f"Failed to extract frame from video: {str(e)}")
