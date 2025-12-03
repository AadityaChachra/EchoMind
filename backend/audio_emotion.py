"""
Utilities for Speech Emotion Recognition (SER) using a pretrained Hugging Face model.

This module loads the model once at startup and exposes a simple
`analyze_emotion_from_wav_bytes` function that takes WAV bytes and
returns the top emotion labels.
"""

from typing import List, Dict, Optional
from pathlib import Path
import tempfile

from transformers import pipeline


_audio_classifier = None


def _get_audio_classifier():
    """
    Lazily load the Hugging Face audio classification pipeline.
    Uses a model trained for emotion recognition on speech.
    """
    global _audio_classifier
    if _audio_classifier is None:
        # This model is relatively lightweight but still powerful for SER.
        # It may download on first run.
        _audio_classifier = pipeline(
            "audio-classification",
            model="superb/hubert-large-superb-er",
        )
    return _audio_classifier


def analyze_emotion_from_wav_bytes(wav_bytes: bytes, top_k: Optional[int] = None) -> List[Dict]:
    """
    Analyze emotions from raw WAV bytes.

    Args:
        wav_bytes: Raw WAV audio data.
        top_k: Number of top emotions to return.

    Returns:
        List of dicts with 'label' and 'score' keys.
    """
    clf = _get_audio_classifier()

    # On Windows, avoid NamedTemporaryFile(delete=True) while still open.
    tmp_dir = tempfile.gettempdir()
    tmp_path = Path(tmp_dir) / "echomind_audio_tmp.wav"

    # Write bytes and close file before passing path to pipeline
    with open(tmp_path, "wb") as f:
        f.write(wav_bytes)

    try:
        preds = clf(str(tmp_path), top_k=top_k)
    finally:
        # Best-effort cleanup; ignore errors if file is in use
        try:
            tmp_path.unlink()
        except OSError:
            pass

    return preds


