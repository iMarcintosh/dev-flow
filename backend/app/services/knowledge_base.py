"""
Knowledge Base Service for Custom Agents

Handles file uploads, text extraction, embeddings, and vector search.
"""
import os
import tempfile
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
import logging

import chromadb
from chromadb.config import Settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing agent knowledge bases with RAG"""
    
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path="./data/chromadb",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize OpenAI for embeddings
        self.openai_client = None
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized for embeddings")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    def get_or_create_collection(self, agent_id: str):
        """Get or create ChromaDB collection for an agent"""
        collection_name = f"agent_{agent_id.replace('-', '_')}"
        return self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"agent_id": agent_id}
        )
    
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
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using OpenAI or local model fallback
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        # Try OpenAI first if available
        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error generating OpenAI embedding: {e}")
        
        # Fallback to local sentence-transformers model
        try:
            from sentence_transformers import SentenceTransformer
            
            # Lazy load model (cache it after first use)
            if not hasattr(self, '_local_model'):
                logger.info("Loading local embedding model (all-MiniLM-L6-v2)...")
                self._local_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            embedding = self._local_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except ImportError:
            logger.error("sentence-transformers not installed. Cannot generate embeddings.")
            return None
        except Exception as e:
            logger.error(f"Error generating local embedding: {e}")
            return None
    
    async def add_file_to_knowledge_base(
        self,
        agent_id: str,
        file_path: str,
        filename: str,
        file_type: str
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
                embedding = self.generate_embedding(chunk)
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
        n_results: int = 5
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
            query_embedding = self.generate_embedding(query)
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
