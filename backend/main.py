# Step1: Setup FastAPI backend
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
import uvicorn
import io
import wave
import json
import csv
from fastapi.responses import StreamingResponse, Response

from ai_agent import graph, SYSTEM_PROMPT, parse_response
from database import init_db, get_db, ChatConversation
from audio_emotion import analyze_emotion_from_wav_bytes
from facial_emotion import analyze_emotion_from_image_bytes, extract_frame_from_video
from sentiment_analysis import analyze_sentiment, calculate_conversation_length

app = FastAPI()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Step2: Receive and validate request from Frontend
class Query(BaseModel):
    message: str

class ChatResponse(BaseModel):
    id: int
    user_message: str
    assistant_response: str
    tool_called: Optional[str]
    timestamp: datetime
    sentiment_score: Optional[float] = None
    conversation_length: Optional[int] = None
    emotion_data: Optional[dict] = None

    class Config:
        from_attributes = True

@app.post("/ask")
async def ask(query: Query, db: Session = Depends(get_db)):
    inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", query.message)]}
    #inputs = {"messages": [("user", query.message)]}
    stream = graph.stream(inputs, stream_mode="updates")
    tool_called_name, final_response = parse_response(stream)

    # Calculate sentiment and length
    user_sentiment = analyze_sentiment(query.message)
    conversation_len = calculate_conversation_length(query.message, final_response or "")
    
    # Save conversation to database
    chat_record = ChatConversation(
        user_message=query.message,
        assistant_response=final_response or "",
        tool_called=tool_called_name if tool_called_name != "None" else None,
        timestamp=datetime.utcnow(),
        sentiment_score=user_sentiment.get("compound", 0.0),
        conversation_length=conversation_len
    )
    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    # Step3: Send response to the frontend
    return {"response": final_response,
            "tool_called": tool_called_name}


@app.get("/chats", response_model=List[ChatResponse])
async def get_chats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve chat conversations from the database.
    Useful for sentiment analysis and historical data review.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of chat conversations with timestamps
    """
    chats = db.query(ChatConversation).order_by(ChatConversation.timestamp.desc()).offset(skip).limit(limit).all()
    return chats


@app.get("/chats/count")
async def get_chat_count(db: Session = Depends(get_db)):
    """
    Get the total count of stored chat conversations.
    """
    count = db.query(ChatConversation).count()
    return {"total_chats": count}


class SummaryRequest(BaseModel):
    chats: List[dict]  # Accept dicts directly from frontend


@app.post("/summarize")
async def summarize_chats(request: SummaryRequest):
    """
    Generate a comprehensive summary of all chat conversations.
    """
    try:
        if not request.chats or len(request.chats) == 0:
            return {"summary": "No conversations available to summarize."}
        
        # Prepare conversation history for summarization
        conversation_text = "Here are all the past conversations:\n\n"
        # Process chats in reverse order (most recent first) and limit to 20
        chats_to_process = request.chats[:20] if len(request.chats) > 20 else request.chats
        
        for idx, chat in enumerate(chats_to_process, 1):
            try:
                # Extract data from dict
                timestamp = chat.get("timestamp")
                user_msg = chat.get("user_message", "")
                assistant_msg = chat.get("assistant_response", "")
                tool_called = chat.get("tool_called")
                
                # Format timestamp
                try:
                    if timestamp:
                        if isinstance(timestamp, str):
                            # Handle ISO format strings
                            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
                    else:
                        formatted_time = "Unknown time"
                except Exception:
                    formatted_time = "Unknown time"
                
                conversation_text += f"Conversation {idx} ({formatted_time}):\n"
                conversation_text += f"User: {user_msg}\n"
                conversation_text += f"Assistant: {assistant_msg}\n"
                if tool_called:
                    conversation_text += f"Tool Used: {tool_called}\n"
                conversation_text += "\n---\n\n"
                    
            except Exception as e:
                # Skip problematic chats and continue
                print(f"Skipping chat {idx} due to error: {str(e)}")
                continue
        
        # Truncate if too long (roughly 8000 characters to leave room for prompt)
        if len(conversation_text) > 8000:
            conversation_text = conversation_text[:8000] + "\n\n[... truncated for length ...]"
        
        # Create a summarization prompt
        summary_prompt = f"""Please provide a comprehensive, to-the-point and precise (Maximum 100 words) summary of the following mental health conversations. 
Analyze the patterns, key themes, emotional states, concerns raised, and overall progress. 
Provide insights in a structured format covering:
1. Overall emotional journey and patterns
2. Main concerns and topics discussed
3. Tools or resources utilized
4. Progress indicators (if any)
5. Key insights and recommendations

Conversations:
{conversation_text}

Please provide a detailed, empathetic summary that helps understand the user's mental health journey."""
        
        # Use the AI agent to generate summary
        try:
            inputs = {"messages": [("system", "You are a mental health analyst. Provide comprehensive, to-the-point, precise (Maximum 100 words), empathetic summaries of mental health conversations."), ("user", summary_prompt)]}
            stream = graph.stream(inputs, stream_mode="updates")
            tool_called_name, summary_response = parse_response(stream)
            
            if summary_response:
                return {"summary": summary_response}
            else:
                return {"summary": "Unable to generate summary at this time. Please try again."}
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in AI summary generation: {error_details}")
            # Return 200 with error message instead of raising exception
            return {"summary": f"Error generating summary: {str(e)}. Please check the backend logs for details."}
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in summarize endpoint: {error_details}")
        # Return 200 with error message instead of raising exception
        return {"summary": f"Error processing request: {str(e)}. Please check the backend logs for details."}


@app.post("/analyze_audio")
async def analyze_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Analyze emotions from a recorded audio clip using a pretrained SER model.

    Expects a WAV file upload from the frontend.
    """
    try:
        if file.content_type not in ("audio/wav", "audio/x-wav", "audio/wave"):
            raise HTTPException(status_code=400, detail="Only WAV audio is supported for now.")

        audio_bytes = await file.read()

        # Basic validation: ensure it's a readable WAV
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                n_frames = wf.getnframes()
                framerate = wf.getframerate()
                duration_sec = n_frames / float(framerate) if framerate else 0.0
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid WAV file.")

        # Run emotion classifier. top_k=None -> return all emotion labels from the model.
        preds = analyze_emotion_from_wav_bytes(audio_bytes, top_k=None)

        # Build a human-readable summary from raw model output
        if preds:
            top_labels = ", ".join([f"{p['label']} ({p['score']:.2f})" for p in preds])
            primary = preds[0]["label"]
        else:
            top_labels = "No emotions detected."
            primary = "unknown"

        base_analysis = (
            f"Primary detected emotion in your voice: {primary}. "
            f"Full emotion distribution: {top_labels}."
        )

        # Ask the LLM to generate a short, 2-line supportive summary
        llm_prompt = (
            "You are a compassionate mental health assistant. "
            "Given the following acoustic emotion analysis of a user's voice, "
            "write a friendly, empathetic TWO-LINE summary (no more than 2 sentences total). "
            "Use plain language, no bullet points, no markdown formatting.\n\n"
            f"Analysis details: {base_analysis}\n\n"
            "Now respond with only the two-line summary:"
        )

        try:
            inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", llm_prompt)]}
            stream = graph.stream(inputs, stream_mode="updates")
            _, llm_summary = parse_response(stream)
        except Exception:
            llm_summary = (
                "I can hear that this moment carries some emotional weight for you. "
                "Thank you for sharing your voice—it's okay to feel what you're feeling."
            )

        # Persist this analysis in the same conversations table so it appears in History
        try:
            record_text = (
                f"[Voice emotion analysis]\n"
                f"Primary emotion: {primary}.\n"
                f"All detected emotions: {top_labels}.\n"
                f"Summary: {llm_summary}"
            )
            # Calculate sentiment from the summary
            sentiment = analyze_sentiment(llm_summary)
            conversation_len = calculate_conversation_length("[Voice note]", record_text)
            
            chat_record = ChatConversation(
                user_message="[Voice note]",
                assistant_response=record_text,
                tool_called="speech_emotion",
                timestamp=datetime.utcnow(),
                sentiment_score=sentiment.get("compound", 0.0),
                conversation_length=conversation_len,
                emotion_data={"emotions": preds, "primary": primary} if preds else None
            )
            db.add(chat_record)
            db.commit()
        except Exception:
            # Don't break the API if saving fails
            db.rollback()

        analysis = (
            f"Primary detected emotion in your voice: {primary}. "
            f"All detected emotions and scores: {top_labels}."
        )

        return {
            "primary_emotion": primary,
            "emotions": preds,
            "duration_seconds": round(duration_sec, 1),
            "analysis": analysis,
            "gpt_summary": llm_summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log and return a safe message
        return {
            "primary_emotion": "unknown",
            "emotions": [],
            "duration_seconds": 0.0,
            "analysis": f"Error analyzing audio: {str(e)}",
        }


@app.post("/analyze_face")
async def analyze_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Analyze emotions from a captured photo or video frame using facial emotion recognition.

    Accepts image files (JPEG, PNG) or video files (MP4, AVI, etc.).
    For videos, extracts the middle frame for analysis.
    """
    try:
        # Determine if it's an image or video
        # Safely get content_type (may not always be available)
        content_type = getattr(file, 'content_type', None) or ""
        
        # Check by content_type first, then by filename extension
        is_video = content_type.startswith("video/") or (
            file.filename and any(
                file.filename.lower().endswith(ext) 
                for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
            )
        )
        is_image = content_type.startswith("image/") or (
            file.filename and any(
                file.filename.lower().endswith(ext) 
                for ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]
            )
        )

        if not is_image and not is_video:
            raise HTTPException(
                status_code=400,
                detail="Only image (JPEG, PNG) or video (MP4, AVI) files are supported."
            )

        file_bytes = await file.read()

        # For videos, extract a frame first
        if is_video:
            try:
                file_bytes = extract_frame_from_video(file_bytes)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to process video: {str(e)}"
                )

        # Analyze emotions from image
        try:
            emotion_preds = analyze_emotion_from_image_bytes(file_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing facial emotions: {str(e)}"
            )

        if not emotion_preds:
            # No face detected
            return {
                "primary_emotion": "no_face_detected",
                "emotions": [],
                "analysis": "No face detected in the image. Please ensure your face is clearly visible.",
                "gpt_summary": "I couldn't detect a face in the image. Please try again with a clearer photo where your face is visible.",
            }

        # Build analysis string
        primary_emotion = emotion_preds[0]["emotion"]
        emotion_labels = ", ".join([
            f"{p['emotion']} ({p['score']:.2f})" for p in emotion_preds
        ])

        base_analysis = (
            f"Primary detected emotion in your face: {primary_emotion}. "
            f"Full emotion distribution: {emotion_labels}."
        )

        # Ask the LLM to generate a short, 2-3 line supportive summary
        llm_prompt = (
            "You are a compassionate mental health assistant. "
            "Given the following facial emotion analysis of a user's expression, "
            "write a friendly, empathetic TWO-TO-THREE-LINE summary (2-3 sentences total). "
            "Use plain language, no bullet points, no markdown formatting.\n\n"
            f"Analysis details: {base_analysis}\n\n"
            "Now respond with only the 2-3 line summary:"
        )

        try:
            inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", llm_prompt)]}
            stream = graph.stream(inputs, stream_mode="updates")
            _, llm_summary = parse_response(stream)
        except Exception:
            llm_summary = (
                "I can see the emotions reflected in your expression. "
                "Thank you for sharing this with me—your feelings are valid and important."
            )

        # Persist this analysis in the same conversations table so it appears in History
        try:
            record_text = (
                f"[Facial emotion analysis]\n"
                f"Primary emotion: {primary_emotion}.\n"
                f"All detected emotions: {emotion_labels}.\n"
                f"Summary: {llm_summary}"
            )
            # Calculate sentiment from the summary
            sentiment = analyze_sentiment(llm_summary)
            conversation_len = calculate_conversation_length("[Photo/Video capture]", record_text)
            
            chat_record = ChatConversation(
                user_message="[Photo/Video capture]",
                assistant_response=record_text,
                tool_called="facial_emotion",
                timestamp=datetime.utcnow(),
                sentiment_score=sentiment.get("compound", 0.0),
                conversation_length=conversation_len,
                emotion_data={"emotions": emotion_preds, "primary": primary_emotion} if emotion_preds else None
            )
            db.add(chat_record)
            db.commit()
        except Exception:
            # Don't break the API if saving fails
            db.rollback()

        analysis = (
            f"Primary detected emotion in your face: {primary_emotion}. "
            f"All detected emotions and scores: {emotion_labels}."
        )

        return {
            "primary_emotion": primary_emotion,
            "emotions": emotion_preds,
            "analysis": analysis,
            "gpt_summary": llm_summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log and return a safe message
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in analyze_face endpoint: {error_details}")
        return {
            "primary_emotion": "unknown",
            "emotions": [],
            "analysis": f"Error analyzing facial emotions: {str(e)}",
            "gpt_summary": "I encountered an issue analyzing your image. Please try again with a clearer photo.",
        }


# ==================== NEW ANALYTICS & MANAGEMENT ENDPOINTS ====================

@app.get("/chats/filtered")
async def get_filtered_chats(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tool_called: Optional[str] = None,
    sentiment_min: Optional[float] = None,
    sentiment_max: Optional[float] = None,
    sort_by: str = "newest",
    db: Session = Depends(get_db)
):
    """
    Get filtered and sorted chat conversations.
    """
    query = db.query(ChatConversation)
    
    # Date filter
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(ChatConversation.timestamp >= start_dt)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(ChatConversation.timestamp <= end_dt)
        except:
            pass
    
    # Tool filter
    if tool_called:
        if tool_called.lower() == "none" or tool_called.lower() == "chat":
            query = query.filter(ChatConversation.tool_called.is_(None))
        else:
            query = query.filter(ChatConversation.tool_called == tool_called)
    
    # Sentiment filter
    if sentiment_min is not None:
        query = query.filter(ChatConversation.sentiment_score >= sentiment_min)
    if sentiment_max is not None:
        query = query.filter(ChatConversation.sentiment_score <= sentiment_max)
    
    # Sort
    if sort_by == "newest":
        query = query.order_by(ChatConversation.timestamp.desc())
    elif sort_by == "oldest":
        query = query.order_by(ChatConversation.timestamp.asc())
    elif sort_by == "longest":
        query = query.order_by(ChatConversation.conversation_length.desc().nulls_last())
    elif sort_by == "shortest":
        query = query.order_by(ChatConversation.conversation_length.asc().nulls_last())
    elif sort_by == "most_positive":
        query = query.order_by(ChatConversation.sentiment_score.desc().nulls_last())
    elif sort_by == "most_negative":
        query = query.order_by(ChatConversation.sentiment_score.asc().nulls_last())
    else:
        query = query.order_by(ChatConversation.timestamp.desc())
    
    chats = query.offset(skip).limit(limit).all()
    return chats


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    """Delete a specific chat conversation."""
    chat = db.query(ChatConversation).filter(ChatConversation.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully", "id": chat_id}


@app.get("/chats/analytics/stats")
async def get_analytics_stats(db: Session = Depends(get_db)):
    """Get comprehensive analytics statistics."""
    from sqlalchemy import extract
    
    total_chats = db.query(ChatConversation).count()
    
    # Average conversation length
    avg_length = db.query(func.avg(ChatConversation.conversation_length)).scalar() or 0
    
    # Sentiment statistics
    avg_sentiment = db.query(func.avg(ChatConversation.sentiment_score)).scalar() or 0
    positive_count = db.query(ChatConversation).filter(ChatConversation.sentiment_score > 0.05).count()
    negative_count = db.query(ChatConversation).filter(ChatConversation.sentiment_score < -0.05).count()
    neutral_count = total_chats - positive_count - negative_count
    
    # Tool usage
    tool_counts = {}
    tools = db.query(ChatConversation.tool_called).distinct().all()
    for tool in tools:
        if tool[0]:
            tool_counts[tool[0]] = db.query(ChatConversation).filter(ChatConversation.tool_called == tool[0]).count()
    
    # Most active day
    day_counts = db.query(
        extract('dow', ChatConversation.timestamp).label('day'),
        func.count(ChatConversation.id).label('count')
    ).group_by('day').all()
    most_active_day = max(day_counts, key=lambda x: x[1])[0] if day_counts else None
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = db.query(ChatConversation).filter(ChatConversation.timestamp >= week_ago).count()
    
    return {
        "total_chats": total_chats,
        "average_length": round(avg_length, 0),
        "average_sentiment": round(avg_sentiment, 3),
        "sentiment_distribution": {
            "positive": positive_count,
            "neutral": neutral_count,
            "negative": negative_count
        },
        "tool_usage": tool_counts,
        "most_active_day": most_active_day,
        "recent_activity_7days": recent_count
    }


@app.get("/chats/analytics/trends")
async def get_sentiment_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get sentiment trends over time."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # For SQLite, use func.date() instead of cast to Date
    # Get all chats in the date range first, then group by date in Python
    chats = db.query(ChatConversation).filter(
        ChatConversation.timestamp >= start_date
    ).all()
    
    # Group by date and calculate averages
    from collections import defaultdict
    date_stats = defaultdict(lambda: {"sentiments": [], "count": 0})
    
    for chat in chats:
        # Extract date part (YYYY-MM-DD)
        date_str = chat.timestamp.date().isoformat()
        if chat.sentiment_score is not None:
            date_stats[date_str]["sentiments"].append(chat.sentiment_score)
        date_stats[date_str]["count"] += 1
    
    # Convert to list format
    trends = []
    for date_str in sorted(date_stats.keys()):
        stats = date_stats[date_str]
        avg_sentiment = sum(stats["sentiments"]) / len(stats["sentiments"]) if stats["sentiments"] else 0.0
        trends.append({
            "date": date_str,
            "avg_sentiment": round(float(avg_sentiment), 3),
            "count": stats["count"]
        })
    
    return trends


@app.get("/chats/analytics/emotions")
async def get_emotion_distribution(db: Session = Depends(get_db)):
    """Get emotion distribution from speech/facial emotion analyses."""
    emotion_entries = db.query(ChatConversation).filter(
        ChatConversation.emotion_data.isnot(None)
    ).all()
    
    emotion_counts = {}
    for entry in emotion_entries:
        if entry.emotion_data:
            emotions = entry.emotion_data.get("emotions", [])
            for emotion in emotions:
                if isinstance(emotion, dict):
                    label = emotion.get("emotion") or emotion.get("label")
                    if label:
                        emotion_counts[label] = emotion_counts.get(label, 0) + 1
    
    return {"emotion_distribution": emotion_counts}


@app.get("/chats/reports/weekly")
async def get_weekly_report(db: Session = Depends(get_db)):
    """Generate weekly mental health report."""
    week_ago = datetime.utcnow() - timedelta(days=7)
    chats = db.query(ChatConversation).filter(
        ChatConversation.timestamp >= week_ago
    ).order_by(ChatConversation.timestamp.desc()).all()
    
    if not chats:
        return {"report": "No conversations in the past week."}
    
    total = len(chats)
    avg_sentiment = sum(c.sentiment_score or 0 for c in chats) / total if total > 0 else 0
    
    # Count by type
    # Chat = all conversations that are NOT speech_emotion or facial_emotion
    speech_count = sum(1 for c in chats if c.tool_called == "speech_emotion")
    facial_count = sum(1 for c in chats if c.tool_called == "facial_emotion")
    # Everything else (None, other tools, etc.) counts as chat
    chat_count = total - speech_count - facial_count
    
    return {
        "period": "Last 7 days",
        "total_conversations": total,
        "average_sentiment": round(avg_sentiment, 3),
        "breakdown": {
            "chat": chat_count,
            "speech_emotion": speech_count,
            "facial_emotion": facial_count
        },
        "summary": f"In the past week, you had {total} conversations with an average sentiment of {round(avg_sentiment, 3)}."
    }


@app.get("/chats/reports/monthly")
async def get_monthly_report(db: Session = Depends(get_db)):
    """Generate monthly mental health report."""
    month_ago = datetime.utcnow() - timedelta(days=30)
    chats = db.query(ChatConversation).filter(
        ChatConversation.timestamp >= month_ago
    ).order_by(ChatConversation.timestamp.desc()).all()
    
    if not chats:
        return {"report": "No conversations in the past month."}
    
    total = len(chats)
    avg_sentiment = sum(c.sentiment_score or 0 for c in chats) / total if total > 0 else 0
    
    # Sentiment trend
    first_half = [c for c in chats if c.timestamp >= month_ago + timedelta(days=15)]
    second_half = [c for c in chats if c.timestamp < month_ago + timedelta(days=15)]
    
    first_avg = sum(c.sentiment_score or 0 for c in first_half) / len(first_half) if first_half else 0
    second_avg = sum(c.sentiment_score or 0 for c in second_half) / len(second_half) if second_half else 0
    
    trend = "improving" if second_avg > first_avg else "declining" if second_avg < first_avg else "stable"
    
    return {
        "period": "Last 30 days",
        "total_conversations": total,
        "average_sentiment": round(avg_sentiment, 3),
        "sentiment_trend": trend,
        "first_half_avg": round(first_avg, 3),
        "second_half_avg": round(second_avg, 3)
    }


@app.get("/chats/export/csv")
async def export_chats_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Export chats to CSV format."""
    query = db.query(ChatConversation)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(ChatConversation.timestamp >= start_dt)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(ChatConversation.timestamp <= end_dt)
        except:
            pass
    
    chats = query.order_by(ChatConversation.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "User Message", "Assistant Response", "Tool", "Sentiment", "Length"])
    
    for chat in chats:
        writer.writerow([
            chat.id,
            chat.timestamp.isoformat(),
            chat.user_message,
            chat.assistant_response,
            chat.tool_called or "",
            chat.sentiment_score or 0,
            chat.conversation_length or 0
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=echomind_history.csv"}
    )


@app.get("/chats/warning-signs")
async def detect_warning_signs(db: Session = Depends(get_db)):
    """Detect potential warning signs in recent conversations."""
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_chats = db.query(ChatConversation).filter(
        ChatConversation.timestamp >= week_ago
    ).all()
    
    warnings = []
    
    # Check for consistently negative sentiment
    negative_chats = [c for c in recent_chats if c.sentiment_score and c.sentiment_score < -0.3]
    if len(negative_chats) >= 5:
        warnings.append({
            "type": "consistently_negative",
            "severity": "medium",
            "message": f"Detected {len(negative_chats)} conversations with negative sentiment in the past week."
        })
    
    # Check for sudden drop in sentiment
    if len(recent_chats) >= 3:
        recent_sentiment = [c.sentiment_score or 0 for c in recent_chats[:3]]
        older_sentiment = [c.sentiment_score or 0 for c in recent_chats[3:6]] if len(recent_chats) >= 6 else []
        if older_sentiment:
            recent_avg = sum(recent_sentiment) / len(recent_sentiment)
            older_avg = sum(older_sentiment) / len(older_sentiment)
            if recent_avg < older_avg - 0.3:
                warnings.append({
                    "type": "sentiment_drop",
                    "severity": "low",
                    "message": "Noticed a recent drop in sentiment compared to earlier conversations."
                })
    
    # Check for high frequency of conversations (possible crisis)
    if len(recent_chats) > 20:
        warnings.append({
            "type": "high_frequency",
            "severity": "low",
            "message": f"High frequency of conversations ({len(recent_chats)} in past week). Consider reaching out for support."
        })
    
    return {
        "warnings": warnings,
        "checked_period": "Last 7 days",
        "total_checked": len(recent_chats)
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)