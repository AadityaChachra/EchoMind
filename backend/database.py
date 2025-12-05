"""
Database setup and models for storing chat conversations.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database file path
DATABASE_URL = "sqlite:///./echomind_chats.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class ChatConversation(Base):
    """
    Model for storing chat conversations with timestamps and analytics.
    """
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    tool_called = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Analytics fields
    sentiment_score = Column(Float, nullable=True)  # -1 to 1 (negative to positive)
    conversation_length = Column(Integer, nullable=True)  # Total character count
    emotion_data = Column(JSON, nullable=True)  # For speech/facial emotion entries

    def __repr__(self):
        return f"<ChatConversation(id={self.id}, timestamp={self.timestamp})>"


def init_db():
    """
    Initialize the database by creating all tables.
    """
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def get_db():
    """
    Dependency function to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


