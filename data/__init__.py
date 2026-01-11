"""Data module for loading, modeling, processing, and retrieving clinical study data.

Submodules:
    loaders: Data loading utilities (H34ExcelLoader)
    generators: Synthetic data generation (SyntheticH34Generator)
    models: Data models and schemas (unified_schema)
    vectorstore: Vector embeddings and RAG retrieval (ChromaVectorStore)

Data Directory Structure:
    data/
    ├── raw/              # Original source files (immutable)
    │   ├── study/        # H-34 study exports (real + synthetic)
    │   ├── protocol/     # Protocol PDFs
    │   ├── literature/   # Literature PDFs
    │   └── registry/     # Registry data
    ├── processed/        # Processed/extracted data
    │   └── document_as_code/  # YAML extractions
    └── vectorstore/      # ChromaDB persistent storage
"""
