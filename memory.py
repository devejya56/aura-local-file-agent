"""Aura Memory Module — Vector Database Integration

Handles indexing and semantic search of file contents using ChromaDB.
Supports PDF, text, markdown, code, and data files.
"""

import os
import chromadb
from pathlib import Path
from loguru import logger

from config import get_config


# Supported file extensions grouped by loader type
TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
                   ".csv", ".html", ".xml", ".log", ".rst", ".toml", ".ini",
                   ".cfg", ".sh", ".bat", ".ps1", ".sql", ".css", ".java",
                   ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php"}
PDF_EXTENSIONS = {".pdf"}


class FileMemory:
    """Local vector database for file indexing and semantic search."""

    def __init__(self, db_path: str = None):
        """Initialize ChromaDB client and collection.

        Args:
            db_path: Path to store the vector database (uses config default if None)
        """
        config = get_config()
        self.db_path = db_path or config.db_path

        # Ensure DB directory exists
        os.makedirs(self.db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="aura_files",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB ready at {self.db_path} ({self.collection.count()} docs)")

    def index_file(self, file_path: str, metadata: dict = None) -> bool:
        """Index a file's contents into the vector database.

        Args:
            file_path: Path to the file to index
            metadata: Optional metadata dict (e.g. {"category": "invoice"})

        Returns:
            True if successful, False otherwise
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            content = self._read_file_content(file_path, file_ext)

            if not content:
                logger.warning(f"No content to index from: {file_path}")
                return False

            # Split into chunks for large files
            chunks = self._split_content(content, max_chars=1000)

            for i, chunk in enumerate(chunks):
                doc_id = f"{os.path.abspath(file_path)}_chunk_{i}"
                doc_metadata = metadata.copy() if metadata else {}
                doc_metadata["source"] = os.path.abspath(file_path)
                doc_metadata["filename"] = os.path.basename(file_path)
                doc_metadata["extension"] = file_ext
                doc_metadata["chunk"] = i
                doc_metadata["total_chunks"] = len(chunks)

                # Upsert to handle re-indexing
                self.collection.upsert(
                    documents=[chunk],
                    metadatas=[doc_metadata],
                    ids=[doc_id],
                )

            logger.info(f"Indexed {len(chunks)} chunk(s) from {os.path.basename(file_path)}")
            return True

        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic search across indexed files.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of result dicts with 'document', 'metadata', 'distance'
        """
        try:
            if self.collection.count() == 0:
                logger.info("Search skipped — empty collection")
                return []

            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count()),
            )

            formatted = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "id": doc_id,
                        "document": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    })

            logger.info(f"Search '{query}' → {len(formatted)} result(s)")
            return formatted

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def generate_answer(self, query: str, llm) -> dict:
        """Answer a question about indexed files using RAG.

        Retrieves relevant document chunks and uses the LLM to generate
        an answer based on context.

        Args:
            query: The user's question
            llm: The initialized LangChain ChatOllama instance

        Returns:
            Dict containing 'answer' and 'sources'
        """
        try:
            from langchain_core.messages import HumanMessage
            
            # 1. Retrieve relevant context
            results = self.search(query, top_k=5)
            
            if not results:
                return {
                    "answer": "I couldn't find any information in your files to answer that question.",
                    "sources": []
                }
                
            # 2. Build context string and source list
            context_blocks = []
            sources = []
            seen_sources = set()
            
            for res in results:
                text = res.get("document", "").strip()
                if not text:
                    continue
                    
                filename = res.get("metadata", {}).get("filename", "Unknown File")
                context_blocks.append(f"--- SOURCE: {filename} ---\n{text}\n")
                
                # Deduplicate sources for the UI
                if filename not in seen_sources:
                    sources.append({
                        "filename": filename,
                        "path": res.get("metadata", {}).get("source", ""),
                        "category": res.get("metadata", {}).get("category", "")
                    })
                    seen_sources.add(filename)
                    
            context_text = "\n".join(context_blocks)
            
            # 3. Construct the RAG prompt
            prompt = f"""You are Aura, an AI assistant that answers questions based ONLY on the user's provided files.
            
Use the following pieces of retrieved context to answer the question. If you don't know the answer based on the context, just say that you don't know. Do not make up information.
Stay concise and helpful.

Context from user's files:
{context_text}

Question: {query}
Answer:"""

            # 4. Generate the answer
            logger.info("Generating RAG answer via LLM...")
            response = llm.invoke([HumanMessage(content=prompt)])
            
            return {
                "answer": response.content.strip(),
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"RAG error: {e}")
            return {
                "answer": f"Sorry, I encountered an error while analyzing your files: {str(e)}",
                "sources": []
            }

    def delete_file_index(self, file_path: str) -> bool:
        """Remove a file's index from the database.

        Args:
            file_path: Path to the file (used to find its chunks)

        Returns:
            True if successful
        """
        try:
            abs_path = os.path.abspath(file_path)
            results = self.collection.get(
                where={"source": abs_path}
            )

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} entries for {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting index for {file_path}: {e}")
            return False

    def get_stats(self) -> dict:
        """Get database statistics."""
        return {
            "total_documents": self.collection.count(),
            "db_path": self.db_path,
        }

    # ── Private helpers ──────────────────────────────────────

    def _read_file_content(self, file_path: str, file_ext: str) -> str:
        """Read file content based on type."""
        try:
            if file_ext in PDF_EXTENSIONS:
                return self._read_pdf(file_path)
            elif file_ext in TEXT_EXTENSIONS:
                return self._read_text(file_path)
            else:
                logger.debug(f"Unsupported file type for indexing: {file_ext}")
                return ""
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""

    @staticmethod
    def _read_text(file_path: str) -> str:
        """Read a text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def _read_pdf(file_path: str) -> str:
        """Read text from a PDF file using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("PyMuPDF not installed — cannot read PDFs. Install with: pip install PyMuPDF")
            return ""
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return ""

    @staticmethod
    def _split_content(content: str, max_chars: int = 1000) -> list[str]:
        """Split content into chunks for indexing."""
        if len(content) <= max_chars:
            return [content]

        chunks = []
        for i in range(0, len(content), max_chars):
            chunk = content[i : i + max_chars]
            if chunk.strip():
                chunks.append(chunk)
        return chunks if chunks else [content[:max_chars]]


# ── Global memory instance ───────────────────────────────────

_memory: FileMemory | None = None


def init_memory(db_path: str = None) -> FileMemory:
    """Initialize the global memory instance.
    
    Args:
        db_path: Override the default DB path from config
    """
    global _memory
    _memory = FileMemory(db_path)
    return _memory


def get_memory() -> FileMemory:
    """Get the global memory instance (auto-initializes if needed)."""
    global _memory
    if _memory is None:
        _memory = FileMemory()
    return _memory
