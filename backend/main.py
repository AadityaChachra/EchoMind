# Step1: Setup FastAPI backend
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import uvicorn

from ai_agent import graph, SYSTEM_PROMPT, parse_response
from database import init_db, get_db, ChatConversation

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


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)