"""
Sentiment analysis utilities for chat conversations.
"""

from typing import Dict, Optional
import re

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

_sentiment_analyzer = None


def _get_sentiment_analyzer():
    """Lazily load sentiment analyzer."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        if not VADER_AVAILABLE:
            raise ImportError(
                "vaderSentiment not installed. Install with: pip install vaderSentiment"
            )
        _sentiment_analyzer = SentimentIntensityAnalyzer()
    return _sentiment_analyzer


def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of a text string.
    
    Args:
        text: Text to analyze.
    
    Returns:
        Dictionary with 'compound', 'pos', 'neu', 'neg' scores.
        Compound score ranges from -1 (most negative) to +1 (most positive).
    """
    if not text or not text.strip():
        return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}
    
    try:
        analyzer = _get_sentiment_analyzer()
        scores = analyzer.polarity_scores(text)
        return scores
    except Exception:
        # Fallback: simple heuristic
        return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}


def get_sentiment_label(compound_score: float) -> str:
    """
    Convert compound sentiment score to label.
    
    Args:
        compound_score: Sentiment compound score (-1 to 1).
    
    Returns:
        Sentiment label: "Positive", "Neutral", or "Negative".
    """
    if compound_score >= 0.05:
        return "Positive"
    elif compound_score <= -0.05:
        return "Negative"
    else:
        return "Neutral"


def calculate_conversation_length(user_message: str, assistant_response: str) -> int:
    """
    Calculate total conversation length in characters.
    
    Args:
        user_message: User's message.
        assistant_response: Assistant's response.
    
    Returns:
        Total character count.
    """
    return len(user_message or "") + len(assistant_response or "")

