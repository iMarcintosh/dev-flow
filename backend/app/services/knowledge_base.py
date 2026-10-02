"""
Knowledge Base Service for Custom Agents

Handles file uploads, text extraction, embeddings, and vector search.
"""
import hashlib
import logging
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings

from app.services.embedding_service import embedding_service as _embedding_service

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing agent knowledge bases with RAG"""

    def __init__(self):
        # Defer ChromaDB initialization to first use so forked Celery workers
        # each open their own connection (avoids SQLite WAL lock contention).
        self._chroma_client = None

    @property
    def chroma_client(self):
        if self._chroma_client is None:
            self._chroma_client = chromadb.PersistentClient(
                path="./data/chromadb",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._chroma_client

    def get_or_create_collection(self, agent_id: str):
        """Get or create ChromaDB collection for an agent"""
        collection_name = f"agent_{agent_id.replace('-', '_')}"
        return self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"agent_id": agent_id, "hnsw:space": "cosine"}
        )

    def get_or_create_notebook_collection(self, user_id: str):
        """Get or create ChromaDB collection for a user's notebook (no agent_ prefix)"""
        collection_name = f"notebook_{user_id.replace('-', '_')}"
        return self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"user_id": user_id, "hnsw:space": "cosine"}
        )

    def search_notebook(self, user_id: str, query: str, n_results: int = 5, api_key: Optional[str] = None) -> List[Dict[str, any]]:
        """Search a user's notebook collection"""
        try:
            collection = self.get_or_create_notebook_collection(user_id)

            if collection.count() == 0:
                return []

            query_embedding = self.generate_embedding(query, api_key=api_key)
            if not query_embedding:
                return []

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None
                    })
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching notebook for user {user_id}: {e}")
            return []

    def delete_notebook_file(self, user_id: str, file_id: str) -> bool:
        """Delete a note's chunks from the notebook collection"""
        try:
            collection = self.get_or_create_notebook_collection(user_id)
            all_data = collection.get()
            ids_to_delete = []
            if all_data['ids'] and all_data['metadatas']:
                for i, metadata in enumerate(all_data['metadatas']):
                    if metadata.get('file_id') == file_id:
                        ids_to_delete.append(all_data['ids'][i])
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} chunks for file {file_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting notebook file {file_id}: {e}")
            return False
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from uploaded file
        
        Args:
            file_path: Path to file
            file_type: File MIME type or extension
            
        Returns:
            Extracted text content
        """
        try:
            # PDF files
            if 'pdf' in file_type.lower():
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            
            # Text-based files (txt, md, py, js, etc.)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:  # Only if we found a good break point
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap if end < text_len else text_len
        
        return [c for c in chunks if c]  # Filter empty chunks
    
    def generate_embedding(self, text: str, api_key: Optional[str] = None) -> Optional[List[float]]:
        """Generate embedding using the shared EmbeddingService."""
        try:
            return _embedding_service.embed_text(text, api_key=api_key)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def add_file_to_knowledge_base(
        self,
        agent_id: str,
        file_path: str,
        filename: str,
        file_type: str,
        api_key: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Add uploaded file to agent's knowledge base
        
        Args:
            agent_id: Agent UUID
            file_path: Path to uploaded file
            filename: Original filename
            file_type: File MIME type
            
        Returns:
            Dict with success status and metadata
        """
        try:
            # Extract text
            text = self.extract_text_from_file(file_path, file_type)
            if not text:
                return {
                    "success": False,
                    "error": "Could not extract text from file"
                }
            
            # Chunk text
            chunks = self.chunk_text(text)
            logger.info(f"Split {filename} into {len(chunks)} chunks")
            
            # Get collection
            collection = self.get_or_create_collection(agent_id)
            
            # Generate file ID
            file_id = hashlib.md5(f"{agent_id}:{filename}".encode()).hexdigest()
            
            # Process chunks
            added_count = 0
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.generate_embedding(chunk, api_key=api_key)
                if not embedding:
                    continue
                
                # Store in ChromaDB
                chunk_id = f"{file_id}_chunk_{i}"
                collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "filename": filename,
                        "file_id": file_id,
                        "chunk_index": i,
                        "file_type": file_type
                    }]
                )
                added_count += 1
            
            return {
                "success": True,
                "chunks_added": added_count,
                "file_id": file_id,
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error adding file to knowledge base: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_knowledge_base(
        self,
        agent_id: str,
        query: str,
        n_results: int = 5,
        api_key: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Search agent's knowledge base
        
        Args:
            agent_id: Agent UUID
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results with text and metadata
        """
        try:
            collection = self.get_or_create_collection(agent_id)
            
            # Check if collection is empty
            if collection.count() == 0:
                return []
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query, api_key=api_key)
            if not query_embedding:
                return []

            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def list_files(self, agent_id: str) -> List[Dict[str, str]]:
        """List all files in agent's knowledge base"""
        try:
            collection = self.get_or_create_collection(agent_id)
            
            # Get all documents
            all_data = collection.get()
            
            # Extract unique files
            files = {}
            if all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    file_id = metadata.get('file_id')
                    if file_id and file_id not in files:
                        files[file_id] = {
                            "file_id": file_id,
                            "filename": metadata.get('filename', 'Unknown'),
                            "file_type": metadata.get('file_type', 'Unknown')
                        }
            
            return list(files.values())
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def delete_file(self, agent_id: str, file_id: str) -> bool:
        """Delete file from knowledge base"""
        try:
            collection = self.get_or_create_collection(agent_id)
            
            # Get all IDs for this file
            all_data = collection.get()
            ids_to_delete = []
            
            if all_data['ids'] and all_data['metadatas']:
                for i, metadata in enumerate(all_data['metadatas']):
                    if metadata.get('file_id') == file_id:
                        ids_to_delete.append(all_data['ids'][i])
            
            # Delete
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} chunks for file {file_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False


# Global instance
knowledge_base_service = KnowledgeBaseService()
