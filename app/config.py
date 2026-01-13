"""
Configuration management for the Clinical Intelligence Platform.
Loads settings from .env file and provides type-safe access.
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent,
        description="Root directory of the project"
    )

    # Gemini API
    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY",
        description="Google Gemini API key"
    )
    gemini_temperature: float = Field(
        default=0.0,
        alias="GEMINI_TEMPERATURE",
        description="Gemini temperature setting"
    )
    gemini_top_p: float = Field(
        default=0.95,
        alias="GEMINI_TOP_P",
        description="Gemini top_p setting"
    )
    gemini_max_output_tokens: int = Field(
        default=50000,
        alias="GEMINI_MAX_OUTPUT_TOKENS",
        description="Gemini max output tokens"
    )
    gemini_max_retries: int = Field(
        default=3,
        alias="GEMINI_MAX_RETRIES",
        description="Gemini max retries"
    )
    gemini_timeout: int = Field(
        default=300,
        alias="GEMINI_TIMEOUT",
        description="Gemini timeout in seconds"
    )

    # Azure OpenAI
    azure_openai_api_key: str = Field(
        default="",
        alias="AZURE_OPENAI_API_KEY",
        description="Azure OpenAI API key"
    )
    azure_openai_endpoint: str = Field(
        default="",
        alias="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_deployment: str = Field(
        default="gpt-5-mini",
        alias="AZURE_OPENAI_DEPLOYMENT",
        description="Azure OpenAI deployment name"
    )
    azure_openai_api_version: str = Field(
        default="2024-10-01-preview",
        alias="AZURE_OPENAI_API_VERSION",
        description="Azure OpenAI API version"
    )
    azure_openai_model_name: str = Field(
        default="gpt-5-mini",
        alias="AZURE_OPENAI_MODEL_NAME",
        description="Azure OpenAI model name"
    )

    # Model settings
    primary_llm: str = Field(
        default="gemini-3-pro-preview",
        alias="PRIMARY_LLM",
        description="Primary LLM model identifier"
    )
    embedding_model: str = Field(
        default="text-embedding-004",
        alias="EMBEDDING_MODEL",
        description="Embedding model for vector store"
    )

    # Data paths (relative to project root)
    h34_study_data_path: str = Field(
        default="data/raw/study/H-34DELTARevisionstudy_export_20250912.xlsx",
        alias="H34_STUDY_DATA_PATH",
        description="Path to H-34 study data export"
    )
    h34_synthetic_data_path: str = Field(
        default="data/raw/study/H-34_SYNTHETIC_PRODUCTION.xlsx",
        alias="H34_SYNTHETIC_DATA_PATH",
        description="Path to H-34 synthetic data"
    )
    protocol_path: str = Field(
        default="data/raw/protocol/CIP_H-34_v.2.0_05Nov2024_fully signed.pdf",
        alias="PROTOCOL_PATH",
        description="Path to protocol PDF"
    )
    literature_path: str = Field(
        default="data/raw/literature/",
        alias="LITERATURE_PATH",
        description="Path to literature folder"
    )
    registry_path: str = Field(
        default="data/raw/registry/",
        alias="REGISTRY_PATH",
        description="Path to registry data folder"
    )

    # Document-as-Code paths
    protocol_rules_path: str = Field(
        default="data/processed/document_as_code/protocol_rules.yaml",
        alias="PROTOCOL_RULES_PATH",
        description="Path to extracted protocol rules YAML"
    )
    literature_benchmarks_path: str = Field(
        default="data/processed/document_as_code/literature_benchmarks.yaml",
        alias="LITERATURE_BENCHMARKS_PATH",
        description="Path to extracted literature benchmarks YAML"
    )
    registry_norms_path: str = Field(
        default="data/processed/document_as_code/registry_norms.yaml",
        alias="REGISTRY_NORMS_PATH",
        description="Path to extracted registry norms YAML"
    )

    # Vector store
    chroma_persist_path: str = Field(
        default="data/vectorstore/chroma_db",
        alias="CHROMA_PERSIST_PATH",
        description="ChromaDB persistence path"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level"
    )
    log_dir: str = Field(
        default="./tmp",
        alias="LOG_DIR",
        description="Log file directory"
    )

    # Model token limits (max output tokens)
    model_max_tokens: dict = Field(
        default={
            "gemini-3-pro-preview": 65536,
            "gemini-2.5-flash-lite": 65536,
            "gemini-2.5-pro": 65536,
            "gemini-2.0-flash-exp": 8192,
            "gemini-1.5-flash": 8192,
            "gemini-1.5-pro": 8192,
            "gpt-5-mini": 16384,
            "gpt-4o": 16384,
            "gpt-4-turbo": 4096,
        },
        description="Maximum output tokens per model"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    # Path getter methods
    def get_h34_study_data_path(self) -> Path:
        """Get absolute path to H-34 study data file."""
        return self.project_root / self.h34_study_data_path

    def get_h34_synthetic_data_path(self) -> Path:
        """Get absolute path to H-34 synthetic data file."""
        return self.project_root / self.h34_synthetic_data_path

    def get_protocol_path(self) -> Path:
        """Get absolute path to protocol PDF."""
        return self.project_root / self.protocol_path

    def get_literature_path(self) -> Path:
        """Get absolute path to literature folder."""
        return self.project_root / self.literature_path

    def get_registry_path(self) -> Path:
        """Get absolute path to registry data folder."""
        return self.project_root / self.registry_path

    def get_protocol_rules_path(self) -> Path:
        """Get absolute path to protocol rules YAML."""
        return self.project_root / self.protocol_rules_path

    def get_literature_benchmarks_path(self) -> Path:
        """Get absolute path to literature benchmarks YAML."""
        return self.project_root / self.literature_benchmarks_path

    def get_registry_norms_path(self) -> Path:
        """Get absolute path to registry norms YAML."""
        return self.project_root / self.registry_norms_path

    def get_chroma_persist_path(self) -> Path:
        """Get absolute path to ChromaDB persistence directory."""
        path = self.project_root / self.chroma_persist_path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_log_dir(self) -> Path:
        """Get absolute path to log directory."""
        log_path = self.project_root / self.log_dir
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path

    def get_max_tokens(self, model: str) -> int:
        """Get maximum output tokens for a given model."""
        return self.model_max_tokens.get(model, 8192)


# Singleton settings instance
settings = Settings()
