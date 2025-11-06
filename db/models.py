from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

    history = relationship("ContentHistory", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")


class ContentHistory(Base):
    __tablename__ = "content_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    prompt = Column(Text)
    output = Column(Text)
    user_type = Column(String)
    topic = Column(String)
    student_level = Column(String)
    content_type = Column(String)
    filename = Column(String)
    pdf_base64 = Column(Text)
    feedback_given = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_model = Column(String, default="groq")  # ← ADD THIS LINE

    user = relationship("User", back_populates="history")
    feedback = relationship("Feedback", back_populates="content", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content_id = Column(UUID(as_uuid=True), ForeignKey("content_history.id"))
    clarity = Column(Integer)
    depth = Column(Integer)
    complexity = Column(String)
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # NEW FIELDS for regenerated content tracking
    is_regenerated_feedback = Column(Boolean, default=False)
    regeneration_count = Column(Integer, default=0)
    regeneration_type = Column(String)  # 'model_switch', 'feedback_adjustment', 'manual'

    user = relationship("User", back_populates="feedbacks")
    content = relationship("ContentHistory", back_populates="feedback")