# app/db/schema/content.py
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# Association table for content-tag many-to-many relationship
content_tags = Table(
    'content_tags', 
    Base.metadata,
    Column('content_id', String(36), ForeignKey('content.id')),
    Column('tag_id', String(36), ForeignKey('tags.id'))
)

class Content(Base):
    """Main content item schema"""
    __tablename__ = "content"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # url, pdf, audio, text
    source = Column(String(1024))
    author = Column(String(255), nullable=True)
    published_date = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    full_text = Column(Text)
    content_metadata = Column(JSON, nullable=True)  # Stores type-specific metadata (page count, duration, etc.)
    vector_id = Column(String(255), nullable=True)  # ID for retrieval from vector database
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entities = relationship("Entity", back_populates="content", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=content_tags, back_populates="content_items")

class Tag(Base):
    """Content tag schema"""
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content_items = relationship("Content", secondary=content_tags, back_populates="tags")

class Entity(Base):
    """Named entity from content"""
    __tablename__ = "entities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String(36), ForeignKey('content.id'), nullable=False)
    entity_type = Column(String(50), nullable=False)  # person, organization, location, etc.
    name = Column(String(255), nullable=False)
    relevance = Column(Integer, default=1)  # 1-10 score of relevance
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content = relationship("Content", back_populates="entities")