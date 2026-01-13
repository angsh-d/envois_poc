"""PostgreSQL vector store with pgvector for document retrieval.

This module provides RAG (Retrieval Augmented Generation) capabilities using
Replit's managed PostgreSQL database with pgvector extension.

Architecture:
    Documents → PDF Extraction → Chunking → Gemini Embeddings → PostgreSQL/pgvector

    Query → Gemini Embedding → pgvector Similarity Search → Relevant Chunks
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import logging

import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from pgvector.psycopg2 import register_vector
import google.generativeai as genai
from dotenv import load_dotenv

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

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            input: List of text strings to embed.

        Returns:
            List of embedding vectors (768 dimensions each).
        """
        embeddings = []

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


class PgVectorStore:
    """PostgreSQL-based vector store using pgvector for document retrieval.

    Supports multiple source types:
    - protocol: Clinical Investigation Protocol documents
    - literature: Published literature PDFs
    - registry: Registry reports and benchmarks

    Usage:
        store = PgVectorStore()

        # Add documents
        chunks = [DocumentChunk(content="...", source_file="protocol.pdf", source_type="protocol")]
        store.add_documents(chunks)

        # Search
        results = store.search("What are the visit windows?", source_type="protocol", n_results=5)
    """

    TABLE_NAME = "document_embeddings"

    def __init__(
        self,
        database_url: Optional[str] = None,
        embedding_function: Optional[GeminiEmbeddingFunction] = None
    ):
        """Initialize PostgreSQL vector store.

        Args:
            database_url: PostgreSQL connection URL. Defaults to DATABASE_URL env var.
            embedding_function: Custom embedding function. Defaults to GeminiEmbeddingFunction.
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        self.embedding_function = embedding_function or GeminiEmbeddingFunction()
        self._dimension = self.embedding_function.dimension

        self._init_database()
        logger.info("PgVectorStore initialized with PostgreSQL")

    def _get_connection(self, register_vec: bool = True):
        """Get a new database connection.
        
        Args:
            register_vec: Whether to register vector type (set False during init)
        """
        conn = psycopg2.connect(self.database_url)
        if register_vec:
            register_vector(conn)
        return conn

    def _init_database(self):
        """Initialize database with pgvector extension and table."""
        conn = self._get_connection(register_vec=False)
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
            
            register_vector(conn)
            
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        source_file TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        page_number INTEGER,
                        section TEXT,
                        chunk_index INTEGER,
                        metadata JSONB DEFAULT '{{}}',
                        embedding vector({self._dimension}),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_source_type 
                    ON {self.TABLE_NAME} (source_type)
                """)
                
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_embedding 
                    ON {self.TABLE_NAME} 
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """)
                
                conn.commit()
                logger.info("Database initialized with pgvector extension and table")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

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

        documents = [chunk.content for chunk in chunks]
        embeddings = self.embedding_function(documents)

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                values = []
                for chunk, embedding in zip(chunks, embeddings):
                    st = source_type or chunk.source_type
                    import json
                    metadata_json = json.dumps(chunk.metadata)
                    values.append((
                        chunk.chunk_id,
                        chunk.content,
                        chunk.source_file,
                        st,
                        chunk.page_number,
                        chunk.section or "",
                        chunk.chunk_index,
                        metadata_json,
                        embedding
                    ))

                execute_values(
                    cur,
                    f"""
                    INSERT INTO {self.TABLE_NAME} 
                    (id, content, source_file, source_type, page_number, section, chunk_index, metadata, embedding)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                    """,
                    values,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)"
                )
                conn.commit()
                logger.info(f"Added {len(chunks)} chunks to PostgreSQL")
                return len(chunks)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

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
            source_type: Which source to search ('protocol', 'literature', 'registry', 'all').
            n_results: Number of results to return.
            where: Optional metadata filter.
            include_distances: Whether to include similarity distances in results.

        Returns:
            List of result dictionaries with keys: content, metadata, distance (if included).
        """
        query_embedding = self.embedding_function.embed_query(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if source_type != "all":
                    if include_distances:
                        cur.execute(
                            f"""
                            SELECT id, content, source_file, source_type, page_number, 
                                   section, chunk_index, metadata,
                                   1 - (embedding <=> %s::vector) AS similarity
                            FROM {self.TABLE_NAME}
                            WHERE source_type = %s
                            ORDER BY embedding <=> %s::vector
                            LIMIT %s
                            """,
                            (embedding_str, source_type, embedding_str, n_results)
                        )
                    else:
                        cur.execute(
                            f"""
                            SELECT id, content, source_file, source_type, page_number, 
                                   section, chunk_index, metadata
                            FROM {self.TABLE_NAME}
                            WHERE source_type = %s
                            ORDER BY embedding <=> %s::vector
                            LIMIT %s
                            """,
                            (source_type, embedding_str, n_results)
                        )
                else:
                    if include_distances:
                        cur.execute(
                            f"""
                            SELECT id, content, source_file, source_type, page_number, 
                                   section, chunk_index, metadata,
                                   1 - (embedding <=> %s::vector) AS similarity
                            FROM {self.TABLE_NAME}
                            ORDER BY embedding <=> %s::vector
                            LIMIT %s
                            """,
                            (embedding_str, embedding_str, n_results)
                        )
                    else:
                        cur.execute(
                            f"""
                            SELECT id, content, source_file, source_type, page_number, 
                                   section, chunk_index, metadata
                            FROM {self.TABLE_NAME}
                            ORDER BY embedding <=> %s::vector
                            LIMIT %s
                            """,
                            (embedding_str, n_results)
                        )

                rows = cur.fetchall()
                
                results = []
                for row in rows:
                    extra_metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
                    result = {
                        "id": row["id"],
                        "content": row["content"],
                        "metadata": {
                            "source_file": row["source_file"],
                            "source_type": row["source_type"],
                            "page_number": row["page_number"],
                            "section": row["section"],
                            "chunk_index": row["chunk_index"],
                            **extra_metadata
                        }
                    }
                    if include_distances and "similarity" in row:
                        similarity = row["similarity"]
                        result["distance"] = float(1 - similarity) if similarity else 1.0
                    results.append(result)
                
                return results
        finally:
            conn.close()

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
        """Get document counts for each source type.

        Returns:
            Dictionary mapping source type to document count.
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT source_type, COUNT(*) as count
                    FROM {self.TABLE_NAME}
                    GROUP BY source_type
                """)
                rows = cur.fetchall()
                stats = {row[0]: row[1] for row in rows}
                
                cur.execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME}")
                stats["all"] = cur.fetchone()[0]
                
                return stats
        finally:
            conn.close()

    def delete_collection(self, source_type: str) -> bool:
        """Delete all documents of a specific source type.

        Args:
            source_type: Source type to delete.

        Returns:
            True if deleted, False otherwise.
        """
        if source_type == "all":
            return self.clear_all()

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE source_type = %s",
                    [source_type]
                )
                deleted = cur.rowcount
                conn.commit()
                logger.info(f"Deleted {deleted} documents from source type: {source_type}")
                return deleted > 0
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def clear_all(self) -> bool:
        """Clear all documents from the store."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {self.TABLE_NAME}")
                conn.commit()
                logger.info("All documents cleared from PostgreSQL")
                return True
        except Exception as e:
            logger.error(f"Error clearing all documents: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


_vector_store: Optional[PgVectorStore] = None


def get_vector_store(
    database_url: Optional[str] = None,
    force_new: bool = False
) -> PgVectorStore:
    """Get or create the vector store singleton.

    Args:
        database_url: Custom database URL (only used on first call).
        force_new: Force creation of a new instance.

    Returns:
        PgVectorStore instance.
    """
    global _vector_store

    if _vector_store is None or force_new:
        _vector_store = PgVectorStore(database_url=database_url)

    return _vector_store
