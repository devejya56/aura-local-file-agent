"""Aura Agent Tools Module

File system operations used by the AI agent.
Each function performs a specific file operation with logging.
"""

import os
import shutil
from pathlib import Path
from loguru import logger

from database import log_move
from utils import FileUtils


def move_and_rename_file(source_path: str, destination_folder: str, new_filename: str, category: str = "Unknown") -> str:
    """Move a file to a new folder and rename it.

    Creates the destination folder if it doesn't exist.
    Logs the move to the history database for undo support.
    Backs up the destination file if it already exists.

    Args:
        source_path: Full path to the source file
        destination_folder: Target directory path
        new_filename: New name for the file (without path)
        category: LLM-assigned category for this file

    Returns:
        New file path on success, or error message
    """
    try:
        # Create destination folder if needed
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            logger.info(f"Created folder: {destination_folder}")

        # Build new full path
        new_path = os.path.join(destination_folder, new_filename)

        # Backup if destination already exists
        if os.path.exists(new_path):
            timestamp = Path(source_path).stat().st_mtime
            backup_name = f"{new_filename}.backup"
            backup_path = os.path.join(destination_folder, backup_name)
            shutil.copy2(new_path, backup_path)
            logger.info(f"Backed up existing: {new_path} → {backup_path}")

        # Move and rename
        shutil.move(source_path, new_path)
        logger.info(f"Moved: {source_path} → {new_path}")

        # Log to history database for undo
        log_move(source_path, new_path, category)

        return new_path

    except Exception as e:
        error_msg = f"Error moving file: {str(e)}"
        logger.error(error_msg)
        return error_msg


def create_folder(folder_path: str) -> str:
    """Create a directory if it doesn't exist.

    Args:
        folder_path: Path to the folder to create

    Returns:
        Success or error message
    """
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logger.info(f"Created folder: {folder_path}")
            return f"Created: {folder_path}"
        else:
            return f"Already exists: {folder_path}"
    except Exception as e:
        error_msg = f"Error creating folder: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_file_size(file_path: str) -> str:
    """Get the size of a file in human-readable format.

    Args:
        file_path: Path to the file

    Returns:
        Human-readable file size
    """
    try:
        size = os.path.getsize(file_path)
        human = FileUtils.human_readable_size(size)
        logger.debug(f"File size of {file_path}: {human}")
        return human
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


def list_directory(dir_path: str) -> list[str]:
    """List files in a directory.

    Args:
        dir_path: Path to the directory

    Returns:
        List of filenames in the directory
    """
    try:
        entries = os.listdir(dir_path)
        files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e))]
        return files
    except Exception as e:
        logger.error(f"Error listing directory: {e}")
        return []
