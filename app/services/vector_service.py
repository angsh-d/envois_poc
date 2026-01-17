"""
Vector Service for Embedding and Retrieval.

Provides vector storage and similarity search using ChromaDB.
Handles document chunking, embedding generation, and semantic retrieval.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

# Default chunk settings
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# ChromaDB storage path
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "data/chroma_db"))


class VectorService:
    """
    Vector embedding and retrieval service using ChromaDB.

    Features:
    - Document chunking with configurable overlap
    - Embedding generation via Gemini
    - Semantic similarity search
    - Collection management per product
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize vector service with ChromaDB.

        Args:
            persist_directory: Path to store ChromaDB data
        """
        self._persist_directory = persist_directory or str(CHROMA_DB_PATH)

        # Ensure directory exists
        Path(self._persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self._client = chromadb.PersistentClient(
            path=self._persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        self._llm_service = get_llm_service()
        logger.info(f"VectorService initialized with ChromaDB at {self._persist_directory}")

    def get_or_create_collection(
        self,
        product_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> chromadb.Collection:
        """
        Get or create a collection for a product.

        Args:
            product_id: Product identifier
            metadata: Optional collection metadata

        Returns:
            ChromaDB collection
        """
        collection_name = f"product_{product_id.replace('-', '_')}"

        # Sanitize collection name (ChromaDB requirements)
        collection_name = "".join(c if c.isalnum() or c == "_" else "_" for c in collection_name)
        collection_name = collection_name[:63]  # Max 63 chars

        collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata=metadata or {"hnsw:space": "cosine"},
        )

        logger.debug(f"Got collection {collection_name} with {collection.count()} documents")
        return collection

    def chunk_document(
        self,
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> List[str]:
        """
        Split document into overlapping chunks.

        Args:
            text: Document text to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Find end of chunk
            end = min(start + chunk_size, text_length)

            # Try to break at sentence boundary if not at end
            if end < text_length:
                # Look for sentence endings
                for sep in [". ", ".\n", "! ", "!\n", "? ", "?\n", "\n\n"]:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - chunk_overlap if end < text_length else text_length

        logger.debug(f"Chunked document into {len(chunks)} chunks")
        return chunks

    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 10,
        max_retries: int = 3,
    ) -> List[List[float]]:
        """
        Generate embeddings for texts using Gemini with retry logic.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts per batch
            max_retries: Maximum retry attempts per batch

        Returns:
            List of embedding vectors
        """
        import asyncio
        import google.generativeai as genai

        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    # Use Gemini embedding model
                    result = genai.embed_content(
                        model="models/text-embedding-004",
                        content=batch,
                        task_type="retrieval_document",
                    )
                    batch_embeddings = result["embedding"]
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Embedding attempt {attempt + 1}/{max_retries} failed for batch {i}: {e}"
                    )
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        await asyncio.sleep(2 ** attempt)

            if batch_embeddings:
                embeddings.extend(batch_embeddings)
            else:
                # All retries failed - raise error instead of using zero vectors
                logger.error(
                    f"All {max_retries} embedding attempts failed for batch {i}. "
                    f"Last error: {last_error}"
                )
                raise RuntimeError(
                    f"Failed to generate embeddings after {max_retries} attempts: {last_error}"
                )

        return embeddings

    async def embed_and_store(
        self,
        product_id: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate embeddings and store documents in vector DB.

        Args:
            product_id: Product identifier for collection
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional document IDs (generated if not provided)

        Returns:
            Storage result with counts
        """
        if not documents:
            return {"success": True, "count": 0}

        collection = self.get_or_create_collection(product_id)

        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{hashlib.md5(doc.encode()).hexdigest()[:12]}" for doc in documents]

        # Ensure metadatas list matches documents
        if metadatas is None:
            metadatas = [{} for _ in documents]
        elif len(metadatas) != len(documents):
            metadatas = metadatas[:len(documents)] + [{} for _ in range(len(documents) - len(metadatas))]

        # Generate embeddings
        embeddings = await self.generate_embeddings(documents)

        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Stored {len(documents)} documents in collection for product {product_id}")

        return {
            "success": True,
            "count": len(documents),
            "collection": collection.name,
        }

    async def process_and_store_document(
        self,
        product_id: str,
        document_text: str,
        source_id: str,
        source_type: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Chunk a document and store all chunks in vector DB.

        Args:
            product_id: Product identifier
            document_text: Full document text
            source_id: Source identifier
            source_type: Type of source (protocol, literature, etc.)
            chunk_size: Chunk size in characters
            chunk_overlap: Overlap between chunks
            additional_metadata: Extra metadata for chunks

        Returns:
            Processing result
        """
        # Chunk the document
        chunks = self.chunk_document(document_text, chunk_size, chunk_overlap)

        if not chunks:
            return {"success": True, "chunks": 0, "message": "No content to store"}

        # Generate IDs and metadata for each chunk
        ids = [f"{source_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = []
        for i, _ in enumerate(chunks):
            meta = {
                "source_id": source_id,
                "source_type": source_type,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            if additional_metadata:
                meta.update(additional_metadata)
            metadatas.append(meta)

        # Store in vector DB
        result = await self.embed_and_store(product_id, chunks, metadatas, ids)

        return {
            "success": result.get("success", False),
            "chunks": len(chunks),
            "collection": result.get("collection"),
        }

    async def similarity_search(
        self,
        product_id: str,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents in a product's collection.

        Args:
            product_id: Product identifier
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching documents with scores
        """
        collection = self.get_or_create_collection(product_id)

        # Generate query embedding
        query_embeddings = await self.generate_embeddings([query])

        # Search
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    "document": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                    "similarity": 1 - results["distances"][0][i] if results.get("distances") else 1,
                })

        return formatted_results

    async def get_context_for_query(
        self,
        product_id: str,
        query: str,
        max_chunks: int = 5,
        max_context_length: int = 8000,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant context for a query.

        Args:
            product_id: Product identifier
            query: Query to get context for
            max_chunks: Maximum number of chunks to include
            max_context_length: Maximum total context length

        Returns:
            Tuple of (combined context string, list of sources used)
        """
        results = await self.similarity_search(product_id, query, n_results=max_chunks)

        context_parts = []
        sources = []
        total_length = 0

        for result in results:
            doc = result.get("document", "")
            if total_length + len(doc) > max_context_length:
                break

            context_parts.append(doc)
            sources.append({
                "source_id": result.get("metadata", {}).get("source_id"),
                "source_type": result.get("metadata", {}).get("source_type"),
                "similarity": result.get("similarity", 0),
            })
            total_length += len(doc)

        context = "\n\n---\n\n".join(context_parts)
        return context, sources

    def delete_collection(self, product_id: str) -> bool:
        """
        Delete a product's collection.

        Args:
            product_id: Product identifier

        Returns:
            Success status
        """
        collection_name = f"product_{product_id.replace('-', '_')}"
        collection_name = "".join(c if c.isalnum() or c == "_" else "_" for c in collection_name)

        try:
            self._client.delete_collection(collection_name)
            logger.info(f"Deleted collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    def get_collection_stats(self, product_id: str) -> Dict[str, Any]:
        """
        Get statistics for a product's collection.

        Args:
            product_id: Product identifier

        Returns:
            Collection statistics
        """
        collection = self.get_or_create_collection(product_id)
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata,
        }

    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        return [c.name for c in self._client.list_collections()]


# Singleton instance
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get singleton vector service instance."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
