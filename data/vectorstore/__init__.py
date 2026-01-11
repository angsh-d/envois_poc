"""Vector store module for document embeddings and retrieval.

Components:
    ChromaVectorStore: Main vector store class with Gemini embeddings
    DocumentChunk: Data class representing a document chunk
    PDFExtractor: Extract and chunk PDF documents
    get_vector_store: Get singleton ChromaVectorStore instance
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
from data.vectorstore.chroma_store import (
    ChromaVectorStore,
    get_vector_store,
    DocumentChunk,
)
from data.vectorstore.pdf_extractor import (
    PDFExtractor,
    index_all_documents,
)

__all__ = [
    "ChromaVectorStore",
    "get_vector_store",
    "DocumentChunk",
    "PDFExtractor",
    "index_all_documents",
]
