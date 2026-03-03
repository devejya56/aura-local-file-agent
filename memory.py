"""Memory Module - Vector Database Integration

Handles indexing and semantic search of file contents using ChromaDB.
"""

import os
import chromadb
from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from loguru import logger


class FileMemory:
    """Local vector database for file indexing and semantic search."""
    
    def __init__(self, db_path: str = "./local_file_db"):
        """Initialize ChromaDB client and collection.
        
        Args:
            db_path: Path to store the vector database
        """
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="aura_files",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized ChromaDB at {db_path}")
    
    def index_file(self, file_path: str, metadata: dict = None) -> bool:
        """Index a file's contents into the vector database.
        
        Args:
            file_path: Path to the file to index
            metadata: Optional metadata dict
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine file type and load accordingly
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                loader = PyMuPDFLoader(file_path)
                docs = loader.load()
            elif file_ext in ['.txt', '.md', '.py', '.json']:
                loader = TextLoader(file_path)
                docs = loader.load()
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return False
            
            # Store documents in ChromaDB
            for i, doc in enumerate(docs):
                doc_id = f"{file_path}_chunk_{i}"
                doc_metadata = metadata or {}
                doc_metadata["source"] = file_path
                doc_metadata["chunk"] = i
                
                self.collection.add(
                    documents=[doc.page_content],
                    metadatas=[doc_metadata],
                    ids=[doc_id]
                )
            
            logger.info(f"Indexed {len(docs)} chunks from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing {file_path}: {str(e)}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> list:
        """Semantic search across indexed files.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            logger.info(f"Search query '{query}' returned {len(results['ids'][0])} results")
            return results
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def delete_file_index(self, file_path: str) -> bool:
        """Remove a file's index from the database.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful
        """
        try:
            # Get all IDs with this file path as source
            results = self.collection.get(
                where={"source": file_path}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} entries for {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {str(e)}")
            return False


# Global memory instance
memory = None

def init_memory(db_path: str = "./local_file_db") -> FileMemory:
    """Initialize the global memory instance."""
    global memory
    memory = FileMemory(db_path)
    return memory

def get_memory() -> FileMemory:
    """Get the global memory instance."""
    global memory
    if memory is None:
        memory = FileMemory()
    return memory
