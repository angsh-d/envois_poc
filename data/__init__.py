"""Data module for loading, modeling, processing, and retrieving clinical study data.

Submodules:
    loaders: Data loading utilities (H34ExcelLoader, db_loader, yaml_loader)
    generators: Synthetic data generation (SyntheticH34Generator)
    models: Data models and schemas (unified_schema, database)
    vectorstore: Vector embeddings and RAG retrieval (PgVectorStore)

Data Directory Structure:
    data/
    ├── raw/              # Original source files (immutable)
    │   ├── study/        # H-34 study exports (real + synthetic)
    │   ├── protocol/     # Protocol PDFs
    │   ├── literature/   # Literature PDFs
    │   └── registry/     # Registry data
    ├── processed/        # Processed/extracted data (YAML fallback)
    │   └── document_as_code/  # YAML extractions
    └── vectorstore/      # PostgreSQL pgvector storage
"""
