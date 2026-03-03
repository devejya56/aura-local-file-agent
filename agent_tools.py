"""Agent Tools Module

Provides the AI agent with tools to manipulate the file system.
Each tool is a function decorated with @tool that the LLM can call.
"""

import os
import shutil
from pathlib import Path
from langchain_core.tools import tool
from loguru import logger


@tool
def move_and_rename_file(source_path: str, destination_folder: str, new_filename: str) -> str:
    """Moves a file to a new folder and renames it.
    
    Creates the destination folder if it doesn't exist.
    
    Args:
        source_path: Full path to the source file
        destination_folder: Target directory path
        new_filename: New name for the file (without path)
        
    Returns:
        Success or error message
    """
    try:
        # Create destination folder if it doesn't exist
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            logger.info(f"Created folder: {destination_folder}")
        
        # Construct new full path
        new_path = os.path.join(destination_folder, new_filename)
        
        # Move and rename the file
        shutil.move(source_path, new_path)
        logger.info(f"Moved {source_path} to {new_path}")
        
        return f"Success: Moved {source_path} to {new_path}"
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def create_folder(folder_path: str) -> str:
    """Creates a directory if it doesn't exist.
    
    Args:
        folder_path: Path to the folder to create
        
    Returns:
        Success or error message
    """
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logger.info(f"Created folder: {folder_path}")
            return f"Success: Created folder {folder_path}"
        else:
            return f"Folder already exists: {folder_path}"
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def get_file_size(file_path: str) -> str:
    """Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes or error message
    """
    try:
        size = os.path.getsize(file_path)
        logger.info(f"File size of {file_path}: {size} bytes")
        return f"File size: {size} bytes"
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


# List of tools available to the agent
tools = [move_and_rename_file, create_folder, get_file_size]
