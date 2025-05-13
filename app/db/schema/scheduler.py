# app/db/schema/scheduler.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

from app.db.schema.content import Base

class ScheduledDigest(Base):
    """Schema for scheduled digests"""
    __tablename__ = "scheduled_digests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    time = Column(String(5), nullable=False)  # HH:MM format
    recipient = Column(String(255), nullable=False)
    delivery_method = Column(String(20), nullable=False)  # email, whatsapp
    digest_type = Column(String(20), default="daily")  # daily, weekly, monthly, custom
    content_types = Column(Text, nullable=True)  # Comma-separated list of content types
    tags = Column(Text, nullable=True)  # Comma-separated list of tags
    active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)