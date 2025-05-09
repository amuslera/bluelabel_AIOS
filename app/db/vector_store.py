# app/db/vector_store.py
import os
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector database for storing and querying embeddings"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "vector_db"
        )
        
        # Ensure the vector store directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create the content collection
        self.content_collection = self._get_or_create_collection("content")
        
        logger.info(f"Vector store initialized at {self.persist_directory}")
    
    def _get_or_create_collection(self, name: str) -> Collection:
        """Get or create a collection"""
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Using existing collection: {name}")
            return collection
        except Exception as e:
            # Handle both ValueError and NotFoundError
            logger.info(f"Collection not found, creating new collection: {name}")
            return self.client.create_collection(name=name)
    
    def add_content(self,
                 content_id: str,
                 text: str,
                 metadata: Dict[str, Any],
                 embedding_provider: Optional[str] = None) -> str:
        """Add content to the vector store
        
        Args:
            content_id: Database ID of the content
            text: The text to create embeddings for
            metadata: Additional metadata to store with the content
            embedding_provider: Optional provider to use for embeddings
            
        Returns:
            The vector store ID for the added content
        """
        # Generate a unique vector ID
        vector_id = str(uuid.uuid4())
        
        # Prepare metadata (ensure it's JSON-serializable)
        metadata_clean = {
            "content_id": content_id,
            "title": metadata.get("title", "Untitled"),
            "content_type": metadata.get("content_type", "unknown"),
            "source": metadata.get("source", ""),
            "author": metadata.get("author", ""),
            "created_at": metadata.get("created_at", "")
        }
        
        try:
            # Use local embeddings - ChromaDB uses Sentence Transformers by default
            self.content_collection.add(
                ids=[vector_id],
                documents=[text],
                metadatas=[metadata_clean]
            )
            logger.info(f"Added content to vector store with ID: {vector_id}")
            return vector_id
            
        except Exception as e:
            logger.error(f"Error adding content to vector store: {str(e)}")
            raise
    
    def search(self,
               query: str,
               filter_criteria: Optional[Dict[str, Any]] = None,
               limit: int = 5) -> List[Dict[str, Any]]:
        """Search the vector database with a query
        
        Args:
            query: The search query
            filter_criteria: Optional filters to apply
            limit: Maximum number of results to return
            
        Returns:
            List of matching results with similarity scores
        """
        try:
            # Convert filter criteria to ChromaDB format if provided
            where_filter = None
            if filter_criteria:
                where_filter = {}
                for key, value in filter_criteria.items():
                    where_filter[key] = value
            
            # Query the vector store
            results = self.content_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
            
            # Format results
            formatted_results = []
            
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    vector_id = results["ids"][0][i]
                    document = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    distance = results.get("distances", [[0] * len(results["ids"][0])])[0][i]
                    
                    # Calculate a similarity score (convert distance to similarity)
                    similarity = 1.0 - (distance / 2.0) if distance is not None else 0.0
                    
                    formatted_results.append({
                        "vector_id": vector_id,
                        "content_id": metadata.get("content_id"),
                        "title": metadata.get("title", "Untitled"),
                        "content_type": metadata.get("content_type"),
                        "similarity_score": similarity,
                        "metadata": metadata,
                        "document_snippet": document[:300] + "..." if len(document) > 300 else document
                    })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def delete_content(self, vector_id: str) -> bool:
        """Delete content from the vector store
        
        Args:
            vector_id: The vector store ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.content_collection.delete(ids=[vector_id])
            logger.info(f"Deleted content from vector store with ID: {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting content from vector store: {str(e)}")
            return False