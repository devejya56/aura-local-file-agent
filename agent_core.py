"""Agent Core Module - LLM Logic and Reasoning

The brain of Aura. Uses LLMs to analyze files and make decisions about organization.
"""

import os
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from loguru import logger

from agent_tools import tools, move_and_rename_file, create_folder
from memory import get_memory

# Initialize the LLM
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")

llm = ChatOllama(
    base_url=OLLAMA_BASE_URL,
    model=MODEL_NAME,
    temperature=0,  # Deterministic for file organization
)

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)


def process_new_file(file_path: str) -> bool:
    """Process a newly detected file using the AI agent.
    
    Args:
        file_path: Path to the file to process
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Processing file: {file_path}")
        
        # Read file preview
        file_preview = read_file_preview(file_path)
        if not file_preview:
            logger.warning(f"Could not read file: {file_path}")
            return False
        
        # Create the prompt for the LLM
        prompt = f"""You are an autonomous file organization agent. Analyze the following file and decide:
1. What category/type is this file?
2. What should be the new filename (lowercase, descriptive, with underscores)?
3. Should it be moved to a new folder? If so, what folder name?

File path: {file_path}
File preview (first 500 chars):
{file_preview}

Based on the content, decide the category and new filename. Be concise and practical.

Respond with:
CATEGORY: [category name]
NEW_FILENAME: [new_filename_with_extension]
FOLDER: [folder_name or SKIP if no move needed]
"""
        
        logger.info("Querying LLM for file analysis...")
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Parse LLM response
        response_text = response.content
        logger.debug(f"LLM Response: {response_text}")
        
        category, new_filename, folder = parse_llm_response(response_text, file_path)
        
        if not new_filename:
            logger.warning(f"Could not determine action for {file_path}")
            return False
        
        # Execute file operations
        if folder and folder.upper() != "SKIP":
            destination = os.path.join(os.path.dirname(file_path), folder)
            logger.info(f"Moving to: {destination}")
            
            # Create folder if needed
            create_folder(destination)
            
            # Move and rename file
            move_and_rename_file(file_path, destination, new_filename)
        else:
            # Just rename in place
            destination = os.path.dirname(file_path)
            move_and_rename_file(file_path, destination, new_filename)
        
        # Index the file in memory
        memory = get_memory()
        new_full_path = os.path.join(
            destination,
            new_filename
        )
        memory.index_file(new_full_path, {"category": category})
        
        logger.info(f"Successfully processed: {file_path} -> {new_filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return False


def read_file_preview(file_path: str, max_chars: int = 500) -> str:
    """Read a preview of the file content.
    
    Args:
        file_path: Path to the file
        max_chars: Maximum characters to read
        
    Returns:
        File preview text
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            preview = f.read(max_chars)
            return preview
    except Exception as e:
        logger.error(f"Could not read file: {str(e)}")
        return ""


def parse_llm_response(response: str, file_path: str) -> tuple:
    """Parse LLM response to extract decisions.
    
    Args:
        response: LLM response text
        file_path: Original file path
        
    Returns:
        (category, new_filename, folder_name)
    """
    try:
        lines = response.strip().split('\\n')
        category = "Unknown"
        new_filename = os.path.basename(file_path)  # Default: keep original
        folder = "SKIP"
        
        for line in lines:
            if line.startswith("CATEGORY:"):
                category = line.split(":", 1)[1].strip()
            elif line.startswith("NEW_FILENAME:"):
                new_filename = line.split(":", 1)[1].strip()
            elif line.startswith("FOLDER:"):
                folder = line.split(":", 1)[1].strip()
        
        return category, new_filename, folder
    except Exception as e:
        logger.error(f"Error parsing LLM response: {str(e)}")
        return "Unknown", None, "SKIP"
