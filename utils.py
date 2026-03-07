"""Aura Utility Module

File and string utility functions used across the project.
"""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Tuple
from datetime import datetime
from loguru import logger


class FileUtils:
    """File utility functions."""

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Calculate MD5 hash of a file for dedup detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hex digest string
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    @staticmethod
    def safe_move_file(src: str, dst: str, backup: bool = True) -> Tuple[bool, str]:
        """Safely move a file, optionally backing up the destination if it exists.
        
        Args:
            src: Source file path
            dst: Destination file path
            backup: Whether to back up existing destination file
            
        Returns:
            (success, result_path_or_error_message)
        """
        try:
            if backup and os.path.exists(dst):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{dst}.backup.{timestamp}"
                shutil.copy2(dst, backup_path)
                logger.info(f"Backed up existing file: {dst} → {backup_path}")

            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            logger.info(f"Moved: {src} → {dst}")
            return True, dst
        except Exception as e:
            error_msg = f"Failed to move {src} → {dst}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize a filename by removing invalid characters and lowercasing.
        
        Args:
            filename: Raw filename string (from LLM or user)
            
        Returns:
            Cleaned, lowercase filename safe for all OSes
        """
        invalid_chars = '<>:"|?*\\'
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, "_")
        # Collapse multiple underscores
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        # Strip leading/trailing whitespace and dots
        sanitized = sanitized.strip().strip(".")
        return sanitized.lower()

    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """Get detailed file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict with path, name, size, created, modified, extension
        """
        stat_info = os.stat(file_path)
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size_bytes": stat_info.st_size,
            "size_human": FileUtils.human_readable_size(stat_info.st_size),
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "extension": os.path.splitext(file_path)[1].lower(),
        }

    @staticmethod
    def human_readable_size(size_bytes: int) -> str:
        """Convert bytes to human-readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


class StringUtils:
    """String utility functions."""

    @staticmethod
    def truncate(text: str, max_length: int = 100) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Collapse all whitespace into single spaces."""
        return " ".join(text.split())
