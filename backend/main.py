# Step1: Setup FastAPI backend
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import uvicorn
import io
import wave

from ai_agent import graph, SYSTEM_PROMPT, parse_response
from database import init_db, get_db, ChatConversation
from audio_emotion import analyze_emotion_from_wav_bytes

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

    class Config:
        from_attributes = True

@app.post("/ask")
async def ask(query: Query, db: Session = Depends(get_db)):
    inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", query.message)]}
    #inputs = {"messages": [("user", query.message)]}
    stream = graph.stream(inputs, stream_mode="updates")
    tool_called_name, final_response = parse_response(stream)

    # Save conversation to database
    chat_record = ChatConversation(
        user_message=query.message,
        assistant_response=final_response or "",
        tool_called=tool_called_name if tool_called_name != "None" else None,
        timestamp=datetime.utcnow()
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
            chat_record = ChatConversation(
                user_message="[Voice note]",
                assistant_response=record_text,
                tool_called="speech_emotion",
                timestamp=datetime.utcnow(),
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)