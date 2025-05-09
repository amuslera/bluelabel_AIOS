# app/db/repositories/content_repository.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json

from app.db.schema.content import Content, Tag, Entity

logger = logging.getLogger(__name__)

class ContentRepository:
    """Repository for content storage operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_content(self, 
                      title: str,
                      content_type: str,
                      full_text: str,
                      source: Optional[str] = None,
                      author: Optional[str] = None,
                      published_date: Optional[datetime] = None,
                      summary: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      vector_id: Optional[str] = None) -> Content:
        """Create a new content item in the database
        
        Args:
            title: Content title
            content_type: Type of content (url, pdf, audio, text)
            full_text: Full text content
            source: Source of the content (URL, file path, etc.)
            author: Author name
            published_date: Publication date
            summary: Content summary
            metadata: Additional metadata
            vector_id: ID in the vector database
            
        Returns:
            Created Content object
        """
        try:
            new_content = Content(
                title=title,
                content_type=content_type,
                full_text=full_text,
                source=source,
                author=author,
                published_date=published_date,
                summary=summary,
                content_metadata=metadata,
                vector_id=vector_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_content)
            self.db.commit()
            self.db.refresh(new_content)
            
            logger.info(f"Created content: {new_content.id} - {title}")
            return new_content
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating content: {str(e)}")
            raise
    
    async def get_content_by_id(self, content_id: str) -> Optional[Content]:
        """Get content by ID
        
        Args:
            content_id: Content ID
            
        Returns:
            Content object or None if not found
        """
        return self.db.query(Content).filter(Content.id == content_id).first()
    
    async def update_content(self, content_id: str, data: Dict[str, Any]) -> Optional[Content]:
        """Update content with new data
        
        Args:
            content_id: Content ID
            data: Dictionary of fields to update
            
        Returns:
            Updated Content object or None if not found
        """
        try:
            content = await self.get_content_by_id(content_id)
            if not content:
                return None
            
            # Update fields
            for key, value in data.items():
                if hasattr(content, key):
                    setattr(content, key, value)
            
            # Always update the updated_at timestamp
            content.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(content)
            
            logger.info(f"Updated content: {content_id}")
            return content
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating content {content_id}: {str(e)}")
            raise
    
    async def delete_content(self, content_id: str) -> bool:
        """Delete content by ID
        
        Args:
            content_id: Content ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            content = await self.get_content_by_id(content_id)
            if not content:
                return False
            
            self.db.delete(content)
            self.db.commit()
            
            logger.info(f"Deleted content: {content_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting content {content_id}: {str(e)}")
            raise
    
    async def add_tags_to_content(self, content_id: str, tag_names: List[str]) -> Optional[Content]:
        """Add tags to content
        
        Args:
            content_id: Content ID
            tag_names: List of tag names
            
        Returns:
            Updated Content object or None if not found
        """
        try:
            content = await self.get_content_by_id(content_id)
            if not content:
                return None
            
            # Get or create tags
            for tag_name in tag_names:
                # Skip empty tags
                if not tag_name or tag_name.strip() == "":
                    continue
                    
                # Normalize tag name
                tag_name = tag_name.strip().lower()
                
                # Check if tag exists
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                
                # Create new tag if it doesn't exist
                if not tag:
                    tag = Tag(name=tag_name)
                    self.db.add(tag)
                
                # Add tag to content if not already present
                if tag not in content.tags:
                    content.tags.append(tag)
            
            self.db.commit()
            self.db.refresh(content)
            
            logger.info(f"Added tags to content {content_id}: {tag_names}")
            return content
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding tags to content {content_id}: {str(e)}")
            raise
    
    async def add_entities_to_content(self, content_id: str, entities: List[Dict[str, Any]]) -> Optional[Content]:
        """Add entities to content
        
        Args:
            content_id: Content ID
            entities: List of entity dictionaries with type, name, and optional relevance
            
        Returns:
            Updated Content object or None if not found
        """
        try:
            content = await self.get_content_by_id(content_id)
            if not content:
                return None
            
            # Create entity objects
            for entity_data in entities:
                entity_type = entity_data.get("type", "unknown")
                entity_name = entity_data.get("name", "")
                relevance = entity_data.get("relevance", 1)
                
                # Skip empty entities
                if not entity_name or entity_name.strip() == "":
                    continue
                
                # Create and add the entity
                entity = Entity(
                    content_id=content_id,
                    entity_type=entity_type,
                    name=entity_name.strip(),
                    relevance=relevance
                )
                self.db.add(entity)
            
            self.db.commit()
            self.db.refresh(content)
            
            logger.info(f"Added entities to content {content_id}")
            return content
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding entities to content {content_id}: {str(e)}")
            raise
    
    async def search_content(self, 
                      query: Optional[str] = None,
                      content_type: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      limit: int = 50,
                      offset: int = 0) -> Tuple[List[Content], int]:
        """Search content with various filters
        
        Args:
            query: Text search query (searches in title and summary)
            content_type: Filter by content type
            tags: Filter by tags
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Tuple of (list of Content objects, total count)
        """
        try:
            base_query = self.db.query(Content)
            
            # Apply filters
            if query:
                base_query = base_query.filter(
                    (Content.title.ilike(f"%{query}%")) | 
                    (Content.summary.ilike(f"%{query}%"))
                )
            
            if content_type:
                base_query = base_query.filter(Content.content_type == content_type)
            
            if tags and len(tags) > 0:
                for tag in tags:
                    base_query = base_query.join(Content.tags).filter(Tag.name == tag.lower())
            
            # Get total count
            total_count = base_query.count()
            
            # Apply pagination
            results = base_query.order_by(Content.created_at.desc()).offset(offset).limit(limit).all()
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error searching content: {str(e)}")
            return [], 0