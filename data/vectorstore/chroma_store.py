"""ChromaDB vector store with Gemini embeddings for document retrieval.

This module provides RAG (Retrieval Augmented Generation) capabilities for:
- Protocol documents (CIP v2.0)
- Literature PDFs (12 publications)
- Registry reports

Architecture:
    Documents → PDF Extraction → Chunking → Gemini Embeddings → ChromaDB

    Query → Gemini Embedding → ChromaDB Similarity Search → Relevant Chunks
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import logging

import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""

    content: str
    source_file: str
    source_type: str  # 'protocol', 'literature', 'registry'
    page_number: Optional[int] = None
    section: Optional[str] = None
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def chunk_id(self) -> str:
        """Generate unique ID for this chunk."""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
        return f"{self.source_type}_{Path(self.source_file).stem}_{self.chunk_index}_{content_hash}"


class GeminiEmbeddingFunction:
    """Custom embedding function using Gemini text-embedding-004."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini embedding function.

        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=self.api_key)
        self.model = "models/text-embedding-004"
        self._dimension = 768  # text-embedding-004 output dimension

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            input: List of text strings to embed.

        Returns:
            List of embedding vectors (768 dimensions each).
        """
        embeddings = []

        # Process in batches to handle rate limits
        batch_size = 100
        for i in range(0, len(input), batch_size):
            batch = input[i:i + batch_size]

            for text in batch:
                try:
                    result = genai.embed_content(
                        model=self.model,
                        content=text,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                except Exception as e:
                    logger.error(f"Error generating embedding: {e}")
                    # Return zero vector on error (ChromaDB requires consistent dimensions)
                    embeddings.append([0.0] * self._dimension)

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query.

        Args:
            query: Search query text.

        Returns:
            Embedding vector (768 dimensions).
        """
        try:
            result = genai.embed_content(
                model=self.model,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return [0.0] * self._dimension


class ChromaVectorStore:
    """ChromaDB-based vector store for document retrieval.

    Supports multiple collections:
    - protocol: Clinical Investigation Protocol documents
    - literature: Published literature PDFs
    - registry: Registry reports and benchmarks

    Usage:
        store = ChromaVectorStore()

        # Add documents
        chunks = [DocumentChunk(content="...", source_file="protocol.pdf", source_type="protocol")]
        store.add_documents(chunks)

        # Search
        results = store.search("What are the visit windows?", source_type="protocol", n_results=5)
    """

    # Collection names for different document types
    COLLECTIONS = {
        "protocol": "h34_protocol",
        "literature": "h34_literature",
        "registry": "h34_registry",
        "all": "h34_all_documents"  # Combined collection for cross-source search
    }

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_function: Optional[GeminiEmbeddingFunction] = None
    ):
        """Initialize ChromaDB vector store.

        Args:
            persist_directory: Directory for persistent storage.
                              Defaults to data/vectorstore/chroma_db
            embedding_function: Custom embedding function.
                               Defaults to GeminiEmbeddingFunction.
        """
        # Set persist directory
        if persist_directory is None:
            base_path = Path(__file__).parent
            persist_directory = str(base_path / "chroma_db")

        self.persist_directory = persist_directory

        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence (modern API)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Initialize embedding function
        self.embedding_function = embedding_function or GeminiEmbeddingFunction()

        # Initialize collections
        self._collections: Dict[str, chromadb.Collection] = {}
        self._init_collections()

        logger.info(f"ChromaDB initialized with persist_directory: {persist_directory}")

    def _init_collections(self):
        """Initialize or get existing collections."""
        for source_type, collection_name in self.COLLECTIONS.items():
            self._collections[source_type] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"source_type": source_type}
            )

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        source_type: Optional[str] = None
    ) -> int:
        """Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects to add.
            source_type: Override source type (uses chunk.source_type if not provided).

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        # Group chunks by source type
        chunks_by_type: Dict[str, List[DocumentChunk]] = {}
        for chunk in chunks:
            st = source_type or chunk.source_type
            if st not in chunks_by_type:
                chunks_by_type[st] = []
            chunks_by_type[st].append(chunk)

        total_added = 0

        for st, type_chunks in chunks_by_type.items():
            # Get or create collection
            collection = self._collections.get(st)
            if collection is None:
                logger.warning(f"Unknown source type: {st}, using 'all' collection")
                collection = self._collections["all"]

            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in type_chunks]
            documents = [chunk.content for chunk in type_chunks]
            metadatas = [
                {
                    "source_file": chunk.source_file,
                    "source_type": chunk.source_type,
                    "page_number": chunk.page_number or -1,
                    "section": chunk.section or "",
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
                for chunk in type_chunks
            ]

            # Generate embeddings
            embeddings = self.embedding_function(documents)

            # Add to collection
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )

            # Also add to 'all' collection for cross-source search
            if st != "all":
                self._collections["all"].add(
                    ids=[f"all_{id}" for id in ids],
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings
                )

            total_added += len(type_chunks)
            logger.info(f"Added {len(type_chunks)} chunks to {st} collection")

        # Note: PersistentClient auto-persists, no manual persist needed

        return total_added

    def search(
        self,
        query: str,
        source_type: str = "all",
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include_distances: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks.

        Args:
            query: Search query text.
            source_type: Which collection to search ('protocol', 'literature', 'registry', 'all').
            n_results: Number of results to return.
            where: Optional metadata filter (ChromaDB where clause).
            include_distances: Whether to include similarity distances in results.

        Returns:
            List of result dictionaries with keys: content, metadata, distance (if included).
        """
        collection = self._collections.get(source_type)
        if collection is None:
            logger.warning(f"Unknown source type: {source_type}, using 'all'")
            collection = self._collections["all"]

        # Generate query embedding
        query_embedding = self.embedding_function.embed_query(query)

        # Search
        include = ["documents", "metadatas"]
        if include_distances:
            include.append("distances")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=include
        )

        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            result = {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            }
            if include_distances and "distances" in results:
                result["distance"] = results["distances"][0][i]
            formatted_results.append(result)

        return formatted_results

    def search_multi_source(
        self,
        query: str,
        source_types: List[str],
        n_results_per_source: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across multiple source types.

        Args:
            query: Search query text.
            source_types: List of source types to search.
            n_results_per_source: Number of results per source type.

        Returns:
            Dictionary mapping source type to list of results.
        """
        results = {}
        for source_type in source_types:
            results[source_type] = self.search(
                query=query,
                source_type=source_type,
                n_results=n_results_per_source
            )
        return results

    def get_collection_stats(self) -> Dict[str, int]:
        """Get document counts for each collection.

        Returns:
            Dictionary mapping collection name to document count.
        """
        stats = {}
        for source_type, collection in self._collections.items():
            stats[source_type] = collection.count()
        return stats

    def delete_collection(self, source_type: str) -> bool:
        """Delete a collection and all its documents.

        Args:
            source_type: Collection to delete.

        Returns:
            True if deleted, False if collection not found.
        """
        if source_type not in self._collections:
            return False

        collection_name = self.COLLECTIONS.get(source_type)
        if collection_name:
            self.client.delete_collection(collection_name)
            del self._collections[source_type]
            self._init_collections()  # Recreate empty collection
            logger.info(f"Deleted and recreated collection: {source_type}")
            return True
        return False

    def clear_all(self):
        """Clear all collections (useful for reindexing)."""
        for source_type in list(self._collections.keys()):
            self.delete_collection(source_type)
        logger.info("All collections cleared")


# Singleton instance
_vector_store: Optional[ChromaVectorStore] = None


def get_vector_store(
    persist_directory: Optional[str] = None,
    force_new: bool = False
) -> ChromaVectorStore:
    """Get or create the vector store singleton.

    Args:
        persist_directory: Custom persist directory (only used on first call).
        force_new: Force creation of a new instance.

    Returns:
        ChromaVectorStore instance.
    """
    global _vector_store

    if _vector_store is None or force_new:
        _vector_store = ChromaVectorStore(persist_directory=persist_directory)

    return _vector_store
