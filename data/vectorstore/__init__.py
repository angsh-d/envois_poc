"""Vector store module for document embeddings and retrieval.

Components:
    PgVectorStore: Main vector store class with PostgreSQL/pgvector
    DocumentChunk: Data class representing a document chunk
    PDFExtractor: Extract and chunk PDF documents
    get_vector_store: Get singleton PgVectorStore instance
    index_all_documents: Utility to index all documents

Usage:
    from data.vectorstore import get_vector_store, PDFExtractor

    # Index documents
    extractor = PDFExtractor()
    chunks = extractor.extract_pdf("protocol.pdf", source_type="protocol")

    store = get_vector_store()
    store.add_documents(chunks)

    # Search
    results = store.search("visit windows", source_type="protocol")
"""
from data.vectorstore.pg_vector_store import (
    PgVectorStore,
    get_vector_store,
    DocumentChunk,
)
from data.vectorstore.pdf_extractor import (
    PDFExtractor,
    index_all_documents,
)

__all__ = [
    "PgVectorStore",
    "get_vector_store",
    "DocumentChunk",
    "PDFExtractor",
    "index_all_documents",
]
