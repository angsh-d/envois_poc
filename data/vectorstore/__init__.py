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
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DocumentChunk:
    """Represents a chunk of a document for vector storage."""
    content: str
    source: str
    source_type: str
    metadata: dict = None
    chunk_id: str = ""

class MockVectorStore:
    """Mock vector store for when chromadb is not available."""
    def __init__(self):
        self._collections = {}
    
    def add_documents(self, chunks: List[DocumentChunk], collection_name: str = "default"):
        pass
    
    def search(self, query: str, source_type: str = None, n_results: int = 5):
        return []
    
    def get_collection_stats(self):
        return {}

try:
    from data.vectorstore.chroma_store import (
        ChromaVectorStore,
        get_vector_store,
    )
except ImportError:
    ChromaVectorStore = MockVectorStore
    _mock_store = MockVectorStore()
    def get_vector_store():
        return _mock_store

try:
    from data.vectorstore.pdf_extractor import (
        PDFExtractor,
        index_all_documents,
    )
except ImportError:
    class PDFExtractor:
        def extract_pdf(self, *args, **kwargs):
            return []
    
    def index_all_documents(*args, **kwargs):
        pass

__all__ = [
    "ChromaVectorStore",
    "get_vector_store",
    "DocumentChunk",
    "PDFExtractor",
    "index_all_documents",
]
