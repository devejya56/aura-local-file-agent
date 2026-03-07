"""Aura Configuration Module

Centralized configuration management using pydantic-settings.
All settings are loaded from environment variables or .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class AuraConfig(BaseSettings):
    """
    Aura Configuration Manager.
    
    All settings can be overridden via environment variables
    prefixed with AURA_ (e.g. AURA_WATCH_DIRECTORY=./my_folder).
    """

    # ── File System ──────────────────────────────────────────
    watch_directory: str = Field(
        default="./watch_dir",
        description="Directory to monitor for new files"
    )

    archive_directory: str = Field(
        default="./archive",
        description="Directory to store organized files"
    )

    # ── Database ─────────────────────────────────────────────
    db_path: str = Field(
        default="./aura_db",
        description="Path for ChromaDB vector database"
    )

    history_db_file: str = Field(
        default="aura_history.db",
        description="SQLite database file for move history"
    )

    # ── LLM ──────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )

    llm_model: str = Field(
        default="llama3.2",
        description="LLM model to use for file analysis"
    )

    embedding_model: str = Field(
        default="nomic-embed-text",
        description="Embedding model for vector search"
    )

    llm_temperature: float = Field(
        default=0.0,
        description="LLM temperature (0=deterministic, 1=creative)"
    )

    llm_timeout: int = Field(
        default=120,
        description="LLM request timeout in seconds"
    )

    # ── Processing ───────────────────────────────────────────
    max_file_size_mb: int = Field(
        default=100,
        description="Maximum file size to process in MB"
    )

    max_preview_chars: int = Field(
        default=250,
        description="Maximum characters to read for file preview"
    )

    file_settle_delay: float = Field(
        default=1.0,
        description="Seconds to wait after file creation before processing"
    )

    # ── Logging ──────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    log_file: Optional[str] = Field(
        default="./aura.log",
        description="Log file path (None to disable file logging)"
    )

    # ── Feature Flags ────────────────────────────────────────
    enable_backup: bool = Field(
        default=True,
        description="Enable file backup before moving"
    )

    enable_ocr: bool = Field(
        default=False,
        description="Enable OCR for images (requires tesseract)"
    )

    enable_vector_search: bool = Field(
        default=True,
        description="Enable vector semantic search via ChromaDB"
    )

    model_config = {
        "env_prefix": "AURA_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_config() -> AuraConfig:
    """Get a new configuration instance (reads from env/.env)."""
    return AuraConfig()


def setup_directories(config: AuraConfig) -> None:
    """Create required directories if they don't exist."""
    for directory in [config.watch_directory, config.archive_directory]:
        Path(directory).mkdir(parents=True, exist_ok=True)
