# app/services/knowledge/knowledge_service.py
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import json

from app.db.vector_store import VectorStore
from app.db.repositories.content_repository import ContentRepository
from app.db.schema.content import Content

logger = logging.getLogger(__name__)

class KnowledgeService:
    """Service for managing knowledge content storage and retrieval"""
    
    def __init__(self, db: Session, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store
        self.content_repo = ContentRepository(db)
    
    async def store_content(self, processed_content: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        """Store processed content in both the database and vector store
        
        Args:
            processed_content: The processed content dictionary
            content_type: Type of content (url, pdf, audio, text)
            
        Returns:
            Dictionary with the stored content information
        """
        try:
            # Extract basic content fields
            title = processed_content.get("title", "Untitled")
            full_text = processed_content.get("text", "")
            summary = processed_content.get("summary", "")
            source = processed_content.get("source", "")
            author = processed_content.get("author")
            
            # Handle published date
            published_date = None
            if processed_content.get("published_date"):
                try:
                    # Attempt to parse the date string
                    published_date = datetime.fromisoformat(processed_content["published_date"])
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse published_date: {processed_content.get('published_date')}")
            
            # Prepare metadata
            metadata = {}
            
            # Add content-type specific metadata
            if content_type == "pdf" and processed_content.get("page_count"):
                metadata["page_count"] = processed_content["page_count"]
            elif content_type == "audio":
                if processed_content.get("duration"):
                    metadata["duration"] = processed_content["duration"]
                if processed_content.get("language"):
                    metadata["language"] = processed_content["language"]
            
            # Create the content record in the database
            content = await self.content_repo.create_content(
                title=title,
                content_type=content_type,
                full_text=full_text,
                source=source,
                author=author,
                published_date=published_date,
                summary=summary,
                metadata=metadata
            )
            
            # Store the content in the vector database
            vector_metadata = {
                "title": title,
                "content_type": content_type,
                "source": source,
                "author": author if author else "",
                "created_at": content.created_at.isoformat() if content.created_at else ""
            }
            
            # Add the content to the vector store (use full text for embedding)
            vector_id = self.vector_store.add_content(
                content_id=content.id,
                text=full_text,
                metadata=vector_metadata
            )
            
            # Update the content record with the vector_id
            await self.content_repo.update_content(content.id, {"vector_id": vector_id})
            
            # Add tags if available
            if processed_content.get("tags") and isinstance(processed_content["tags"], list):
                await self.content_repo.add_tags_to_content(content.id, processed_content["tags"])
            
            # Add entities if available
            if processed_content.get("entities") and isinstance(processed_content["entities"], dict):
                entities_list = []
                
                # Convert the entities dictionary to a list of entity objects
                for entity_type, names in processed_content["entities"].items():
                    if isinstance(names, list):
                        for name in names:
                            entities_list.append({
                                "type": entity_type, 
                                "name": name,
                                "relevance": 5  # Default relevance
                            })
                
                if entities_list:
                    await self.content_repo.add_entities_to_content(content.id, entities_list)
            
            logger.info(f"Successfully stored content: {content.id}")
            
            return {
                "status": "success",
                "content_id": content.id,
                "vector_id": vector_id,
                "title": title,
                "content_type": content_type,
                "created_at": content.created_at.isoformat() if content.created_at else ""
            }
        
        except Exception as e:
            logger.error(f"Error storing content: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to store content: {str(e)}"
            }
    
    async def retrieve_content(self, content_id: str) -> Dict[str, Any]:
        """Retrieve content by ID
        
        Args:
            content_id: The content ID
            
        Returns:
            Dictionary with the content information
        """
        try:
            content = await self.content_repo.get_content_by_id(content_id)
            
            if not content:
                return {
                    "status": "error",
                    "message": f"Content not found with ID: {content_id}"
                }
            
            # Get the tags
            tags = [tag.name for tag in content.tags] if content.tags else []
            
            # Get the entities
            entities = {}
            if content.entities:
                for entity in content.entities:
                    if entity.entity_type not in entities:
                        entities[entity.entity_type] = []
                    entities[entity.entity_type].append(entity.name)
            
            # Format the result
            result = {
                "status": "success",
                "content": {
                    "id": content.id,
                    "title": content.title,
                    "content_type": content.content_type,
                    "source": content.source,
                    "author": content.author,
                    "published_date": content.published_date.isoformat() if content.published_date else None,
                    "summary": content.summary,
                    "full_text": content.full_text,
                    "metadata": content.content_metadata,
                    "tags": tags,
                    "entities": entities,
                    "created_at": content.created_at.isoformat() if content.created_at else None,
                    "updated_at": content.updated_at.isoformat() if content.updated_at else None
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving content {content_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to retrieve content: {str(e)}"
            }
    
    async def search(self, 
                query: str, 
                content_type: Optional[str] = None,
                tags: Optional[List[str]] = None,
                limit: int = 10) -> Dict[str, Any]:
        """Search for content
        
        Args:
            query: The search query
            content_type: Optional content type filter
            tags: Optional list of tags to filter by
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            # Prepare filter for vector search
            vector_filter = {}
            if content_type:
                vector_filter["content_type"] = content_type
            
            # Perform vector search
            vector_results = self.vector_store.search(
                query=query,
                filter_criteria=vector_filter,
                limit=limit
            )
            
            # Get the content IDs from vector results
            content_ids = [result["content_id"] for result in vector_results]
            
            # Get the full content objects
            result_details = []
            for vector_result in vector_results:
                content_id = vector_result["content_id"]
                content = await self.content_repo.get_content_by_id(content_id)
                
                if content:
                    # Check tag filter
                    if tags and not set(tags).issubset(set(tag.name for tag in content.tags)):
                        continue
                    
                    # Get the tags
                    content_tags = [tag.name for tag in content.tags] if content.tags else []
                    
                    # Add to results
                    result_details.append({
                        "id": content.id,
                        "title": content.title,
                        "content_type": content.content_type,
                        "source": content.source,
                        "author": content.author,
                        "summary": content.summary,
                        "similarity": vector_result["similarity_score"],
                        "published_date": content.published_date.isoformat() if content.published_date else None,
                        "tags": content_tags,
                        "created_at": content.created_at.isoformat() if content.created_at else None,
                        "snippet": vector_result["document_snippet"]
                    })
            
            # If no vector results, fall back to database search
            if not result_details:
                db_results, total = await self.content_repo.search_content(
                    query=query,
                    content_type=content_type,
                    tags=tags,
                    limit=limit
                )
                
                for content in db_results:
                    content_tags = [tag.name for tag in content.tags] if content.tags else []
                    
                    result_details.append({
                        "id": content.id,
                        "title": content.title,
                        "content_type": content.content_type,
                        "source": content.source,
                        "author": content.author,
                        "summary": content.summary,
                        "similarity": None,  # No similarity score for DB results
                        "published_date": content.published_date.isoformat() if content.published_date else None,
                        "tags": content_tags,
                        "created_at": content.created_at.isoformat() if content.created_at else None,
                        "snippet": content.summary[:300] + "..." if content.summary and len(content.summary) > 300 else (content.summary or "")
                    })
            
            return {
                "status": "success",
                "results": result_details,
                "count": len(result_details)
            }
            
        except Exception as e:
            logger.error(f"Error searching for content: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to search content: {str(e)}",
                "results": [],
                "count": 0
            }
    
    async def delete_content(self, content_id: str) -> Dict[str, Any]:
        """Delete content by ID
        
        Args:
            content_id: The content ID
            
        Returns:
            Dictionary with result status
        """
        try:
            # Get the content to retrieve vector_id
            content = await self.content_repo.get_content_by_id(content_id)
            
            if not content:
                return {
                    "status": "error",
                    "message": f"Content not found with ID: {content_id}"
                }
            
            # Delete from vector store if it has a vector_id
            if content.vector_id:
                self.vector_store.delete_content(content.vector_id)
            
            # Delete from database
            result = await self.content_repo.delete_content(content_id)
            
            if result:
                return {
                    "status": "success",
                    "message": f"Content deleted: {content_id}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to delete content: {content_id}"
                }
            
        except Exception as e:
            logger.error(f"Error deleting content {content_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to delete content: {str(e)}"
            }
    
    async def list_content(self, 
                     content_type: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     limit: int = 50,
                     offset: int = 0) -> Dict[str, Any]:
        """List content with filters
        
        Args:
            content_type: Optional content type filter
            tags: Optional list of tags to filter by
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Dictionary with paginated content list
        """
        try:
            results, total = await self.content_repo.search_content(
                content_type=content_type,
                tags=tags,
                limit=limit,
                offset=offset
            )
            
            # Format the results
            result_list = []
            for content in results:
                content_tags = [tag.name for tag in content.tags] if content.tags else []
                
                result_list.append({
                    "id": content.id,
                    "title": content.title,
                    "content_type": content.content_type,
                    "source": content.source,
                    "author": content.author,
                    "summary": content.summary,
                    "published_date": content.published_date.isoformat() if content.published_date else None,
                    "tags": content_tags,
                    "created_at": content.created_at.isoformat() if content.created_at else None
                })
            
            return {
                "status": "success",
                "results": result_list,
                "count": len(result_list),
                "total": total,
                "offset": offset,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error listing content: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to list content: {str(e)}",
                "results": [],
                "count": 0,
                "total": 0
            }