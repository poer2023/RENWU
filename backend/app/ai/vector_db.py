"""
Vector Database Manager for TaskWall v3.0

Handles:
- ChromaDB integration
- Task vectorization
- Similarity search
- Vector database operations
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from ..models import Task, TaskVector


class VectorDBManager:
    """Manages vector database operations for task similarity"""
    
    def __init__(self, db_session, persist_directory: str = "./data/chroma"):
        self.db_session = db_session
        self.persist_directory = persist_directory
        self.client = None
        self.task_collection = None
        self.model = None
        
        # Initialize if dependencies are available
        if CHROMADB_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE:
            self._initialize_chromadb()
            self._initialize_model()
        else:
            print("Warning: ChromaDB or SentenceTransformers not available. "
                  "Vector similarity features will be limited.")
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collections"""
        try:
            # Ensure persist directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create task collection
            self.task_collection = self.client.get_or_create_collection(
                name="task_vectors",
                metadata={
                    "description": "Task content vectors for similarity search",
                    "version": "3.0"
                }
            )
            
            print(f"ChromaDB initialized with {self.task_collection.count()} existing vectors")
            
        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.task_collection = None
    
    def _initialize_model(self):
        """Initialize sentence transformer model"""
        try:
            # Use multilingual model for Chinese/English support
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("Sentence transformer model loaded successfully")
        except Exception as e:
            print(f"Failed to load sentence transformer model: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if vector database is available"""
        return (self.client is not None and 
                self.task_collection is not None and 
                self.model is not None)
    
    def add_task_vector(self, task: Task, force_update: bool = False) -> bool:
        """Add or update task vector in the database"""
        if not self.is_available():
            return False
        
        try:
            # Check if vector already exists and is up to date
            if not force_update and task.vector_id and not task.needs_vector_update():
                return True
            
            # Generate content for vectorization
            content = task.get_content_for_vectorization()
            
            # Create embedding
            embedding = self.model.encode(content).tolist()
            
            # Generate unique vector ID
            vector_id = f"task_{task.id}_{int(datetime.now().timestamp())}"
            
            # Prepare metadata
            metadata = {
                "task_id": task.id,
                "title": task.title[:100],  # Limit length
                "category": task.category or "uncategorized",
                "priority": task.priority.value if hasattr(task.priority, 'value') else task.urgency,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            
            # Remove old vector if exists
            if task.vector_id:
                try:
                    self.task_collection.delete(ids=[task.vector_id])
                except Exception:
                    pass  # Vector might not exist
            
            # Add new vector
            self.task_collection.add(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            # Update task record
            task.vector_id = vector_id
            task.last_vector_update = datetime.utcnow()
            
            # Update or create TaskVector record
            task_vector = self.db_session.query(TaskVector).filter(
                TaskVector.task_id == task.id
            ).first()
            
            if task_vector:
                task_vector.vector_id = vector_id
                task_vector.last_updated = datetime.utcnow()
            else:
                task_vector = TaskVector(
                    task_id=task.id,
                    vector_id=vector_id,
                    last_updated=datetime.utcnow()
                )
                self.db_session.add(task_vector)
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            print(f"Failed to add task vector: {e}")
            self.db_session.rollback()
            return False
    
    def find_similar_tasks(
        self, 
        content: str, 
        n_results: int = 5, 
        threshold: float = 0.7,
        exclude_task_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find similar tasks based on content"""
        if not self.is_available():
            return []
        
        try:
            # Create query embedding
            query_embedding = self.model.encode(content).tolist()
            
            # Search for similar vectors
            results = self.task_collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results * 2, 50),  # Get more results to filter
                include=["documents", "metadatas", "distances"]
            )
            
            if not results["distances"] or not results["distances"][0]:
                return []
            
            # Process results
            similar_tasks = []
            for i, distance in enumerate(results["distances"][0]):
                # Convert distance to similarity (ChromaDB uses cosine distance)
                similarity = 1 - distance
                
                if similarity < threshold:
                    continue
                
                metadata = results["metadatas"][0][i]
                document = results["documents"][0][i]
                task_id = metadata.get("task_id")
                
                # Exclude the query task itself
                if exclude_task_id and task_id == exclude_task_id:
                    continue
                
                similar_tasks.append({
                    "task_id": task_id,
                    "similarity": similarity,
                    "content": document,
                    "metadata": metadata,
                    "title": metadata.get("title", ""),
                    "category": metadata.get("category", ""),
                    "priority": metadata.get("priority", 2)
                })
            
            # Sort by similarity and limit results
            similar_tasks.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_tasks[:n_results]
            
        except Exception as e:
            print(f"Failed to search similar tasks: {e}")
            return []
    
    def remove_task_vector(self, task: Task) -> bool:
        """Remove task vector from the database"""
        if not self.is_available() or not task.vector_id:
            return False
        
        try:
            # Remove from ChromaDB
            self.task_collection.delete(ids=[task.vector_id])
            
            # Remove from TaskVector table
            task_vector = self.db_session.query(TaskVector).filter(
                TaskVector.task_id == task.id
            ).first()
            
            if task_vector:
                self.db_session.delete(task_vector)
            
            # Clear task vector references
            task.vector_id = None
            task.last_vector_update = None
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            print(f"Failed to remove task vector: {e}")
            self.db_session.rollback()
            return False
    
    def update_all_task_vectors(self, force: bool = False) -> int:
        """Update vectors for all tasks that need it"""
        if not self.is_available():
            return 0
        
        try:
            # Get tasks that need vector updates
            tasks_query = self.db_session.query(Task)
            
            if not force:
                # Only update tasks that need updates
                tasks_query = tasks_query.filter(
                    (Task.vector_id.is_(None)) |
                    (Task.last_vector_update.is_(None)) |
                    (Task.updated_at > Task.last_vector_update)
                )
            
            tasks = tasks_query.all()
            updated_count = 0
            
            for task in tasks:
                if self.add_task_vector(task, force_update=force):
                    updated_count += 1
                    
                    # Process in batches to avoid memory issues
                    if updated_count % 50 == 0:
                        print(f"Updated {updated_count} task vectors...")
            
            print(f"Updated {updated_count} task vectors total")
            return updated_count
            
        except Exception as e:
            print(f"Failed to update task vectors: {e}")
            return 0
    
    def get_vector_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        if not self.is_available():
            return {
                "available": False,
                "total_vectors": 0,
                "tasks_with_vectors": 0,
                "tasks_needing_update": 0
            }
        
        try:
            # ChromaDB stats
            total_vectors = self.task_collection.count()
            
            # Database stats
            total_tasks = self.db_session.query(Task).count()
            tasks_with_vectors = self.db_session.query(Task).filter(
                Task.vector_id.isnot(None)
            ).count()
            
            tasks_needing_update = self.db_session.query(Task).filter(
                (Task.vector_id.is_(None)) |
                (Task.last_vector_update.is_(None)) |
                (Task.updated_at > Task.last_vector_update)
            ).count()
            
            return {
                "available": True,
                "total_vectors": total_vectors,
                "total_tasks": total_tasks,
                "tasks_with_vectors": tasks_with_vectors,
                "tasks_needing_update": tasks_needing_update,
                "vector_coverage": (tasks_with_vectors / total_tasks * 100) if total_tasks > 0 else 0
            }
            
        except Exception as e:
            print(f"Failed to get vector stats: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def clear_all_vectors(self) -> bool:
        """Clear all vectors (use with caution)"""
        if not self.is_available():
            return False
        
        try:
            # Clear ChromaDB collection
            self.client.delete_collection("task_vectors")
            
            # Recreate collection
            self.task_collection = self.client.get_or_create_collection(
                name="task_vectors",
                metadata={
                    "description": "Task content vectors for similarity search",
                    "version": "3.0"
                }
            )
            
            # Clear database records
            self.db_session.query(TaskVector).delete()
            self.db_session.query(Task).update({
                Task.vector_id: None,
                Task.last_vector_update: None
            })
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            print(f"Failed to clear vectors: {e}")
            self.db_session.rollback()
            return False