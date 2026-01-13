"""PDF extraction and chunking for vector store ingestion.

This module provides utilities for:
- Extracting text from PDF documents
- Chunking text for optimal retrieval
- Creating DocumentChunk objects for vector store
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional, Generator
import logging
import re

from data.vectorstore.pg_vector_store import DocumentChunk

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract and chunk text from PDF documents.

    Usage:
        extractor = PDFExtractor(chunk_size=500, chunk_overlap=50)
        chunks = extractor.extract_pdf("path/to/document.pdf", source_type="protocol")
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """Initialize PDF extractor.

        Args:
            chunk_size: Target number of tokens per chunk.
            chunk_overlap: Number of overlapping tokens between chunks.
            min_chunk_size: Minimum chunk size (smaller chunks are merged).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def extract_pdf(
        self,
        pdf_path: str,
        source_type: str,
        metadata: Optional[dict] = None
    ) -> List[DocumentChunk]:
        """Extract text from PDF and create chunks.

        Args:
            pdf_path: Path to PDF file.
            source_type: Type of document ('protocol', 'literature', 'registry').
            metadata: Additional metadata to include in chunks.

        Returns:
            List of DocumentChunk objects.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        chunks = []
        metadata = metadata or {}

        try:
            doc = fitz.open(str(pdf_path))

            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text("text")

                # Clean text
                page_text = self._clean_text(page_text)

                if not page_text.strip():
                    continue

                # Create chunks from page
                page_chunks = self._chunk_text(page_text)

                for chunk_idx, chunk_text in enumerate(page_chunks):
                    chunk = DocumentChunk(
                        content=chunk_text,
                        source_file=str(pdf_path.name),
                        source_type=source_type,
                        page_number=page_num,
                        chunk_index=len(chunks),
                        metadata={
                            "page_chunk_index": chunk_idx,
                            **metadata
                        }
                    )
                    chunks.append(chunk)

            doc.close()
            logger.info(f"Extracted {len(chunks)} chunks from {pdf_path.name}")

        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {e}")
            raise

        return chunks

    def extract_directory(
        self,
        directory: str,
        source_type: str,
        pattern: str = "*.pdf",
        recursive: bool = False
    ) -> List[DocumentChunk]:
        """Extract all PDFs from a directory.

        Args:
            directory: Path to directory containing PDFs.
            source_type: Type of documents.
            pattern: Glob pattern for PDF files.
            recursive: If True, search subdirectories recursively.

        Returns:
            List of DocumentChunk objects from all PDFs.
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        all_chunks = []
        glob_pattern = f"**/{pattern}" if recursive else pattern
        pdf_files = list(dir_path.glob(glob_pattern))

        for pdf_file in pdf_files:
            try:
                chunks = self.extract_pdf(
                    pdf_path=str(pdf_file),
                    source_type=source_type,
                    metadata={"source_directory": str(directory)}
                )
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Skipping {pdf_file.name}: {e}")
                continue

        logger.info(f"Extracted {len(all_chunks)} total chunks from {len(pdf_files)} PDFs")
        return all_chunks

    def _clean_text(self, text: str) -> str:
        """Clean extracted text.

        Args:
            text: Raw extracted text.

        Returns:
            Cleaned text.
        """
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

        # Remove excessive newlines but keep paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap.

        Uses sentence-aware chunking to avoid breaking mid-sentence.

        Args:
            text: Text to chunk.

        Returns:
            List of text chunks.
        """
        # Simple sentence splitting (handles common cases)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())

            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                if len(chunk_text.split()) >= self.min_chunk_size:
                    chunks.append(chunk_text)

                # Start new chunk with overlap
                overlap_sentences = []
                overlap_length = 0
                for sent in reversed(current_chunk):
                    sent_len = len(sent.split())
                    if overlap_length + sent_len <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_length += sent_len
                    else:
                        break

                current_chunk = overlap_sentences
                current_length = overlap_length

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text.split()) >= self.min_chunk_size:
                chunks.append(chunk_text)

        return chunks


def index_all_documents(
    base_data_path: Optional[str] = None,
    force_reindex: bool = False
) -> dict:
    """Index all documents into the vector store.

    Args:
        base_data_path: Base path to data directory.
                       Defaults to data/raw/.
        force_reindex: Clear existing collections and reindex.

    Returns:
        Dictionary with indexing statistics.
    """
    from data.vectorstore import get_vector_store

    if base_data_path is None:
        base_data_path = Path(__file__).parent.parent / "raw"
    else:
        base_data_path = Path(base_data_path)

    store = get_vector_store(force_new=force_reindex)
    extractor = PDFExtractor()

    if force_reindex:
        store.clear_all()

    stats = {
        "protocol": 0,
        "literature": 0,
        "registry": 0
    }

    # Index protocol documents
    protocol_dir = base_data_path / "protocol"
    if protocol_dir.exists():
        try:
            chunks = extractor.extract_directory(str(protocol_dir), "protocol")
            stats["protocol"] = store.add_documents(chunks)
        except Exception as e:
            logger.error(f"Error indexing protocol: {e}")

    # Index literature documents
    literature_dir = base_data_path / "literature"
    if literature_dir.exists():
        try:
            chunks = extractor.extract_directory(str(literature_dir), "literature")
            stats["literature"] = store.add_documents(chunks)
        except Exception as e:
            logger.error(f"Error indexing literature: {e}")

    # Index registry documents (PDFs may be in subdirectories)
    registry_dir = base_data_path / "registry"
    if registry_dir.exists():
        try:
            # PDFs in registry - search recursively for subdirectories
            chunks = extractor.extract_directory(str(registry_dir), "registry", recursive=True)
            stats["registry"] = store.add_documents(chunks)
        except Exception as e:
            logger.error(f"Error indexing registry: {e}")

    logger.info(f"Indexing complete: {stats}")
    return stats


if __name__ == "__main__":
    # Quick test
    import sys
    from pipeline.logging_config import setup_logging

    setup_logging(log_level='INFO', log_file='pdf_extractor.log')

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        extractor = PDFExtractor()
        chunks = extractor.extract_pdf(pdf_path, source_type="test")
        print(f"Extracted {len(chunks)} chunks")
        if chunks:
            print(f"\nFirst chunk preview:\n{chunks[0].content[:500]}...")
    else:
        print("Usage: python pdf_extractor.py <pdf_path>")
