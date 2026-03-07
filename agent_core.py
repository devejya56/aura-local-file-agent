"""Aura Agent Core — LLM Logic and Reasoning

The brain of Aura. Uses a local LLM (via Ollama) to analyze files
and make decisions about categorization, renaming, and organization.
"""

import os
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from loguru import logger

from config import get_config
from agent_tools import move_and_rename_file, create_folder
from memory import get_memory
from utils import FileUtils
import ocr

# ── Initialize LLM from config ──────────────────────────────

_config = get_config()

llm = ChatOllama(
    base_url=_config.ollama_base_url,
    model=_config.llm_model,
    temperature=_config.llm_temperature,
    timeout=_config.llm_timeout,
)


def process_new_file(file_path: str) -> bool:
    """Process a newly detected file using the AI agent.

    Pipeline:
      1. Read file preview (text or PDF)
      2. Prompt the LLM for categorization
      3. Parse the LLM response
      4. Move/rename the file
      5. Index in vector database

    Args:
        file_path: Path to the file to process

    Returns:
        True if successfully processed, False otherwise
    """
    try:
        logger.info(f"{'─' * 50}")
        logger.info(f"Processing: {file_path}")

        # ── Check file size ──────────────────────────────
        file_size = os.path.getsize(file_path)
        max_bytes = _config.max_file_size_mb * 1024 * 1024
        if file_size > max_bytes:
            logger.warning(f"File too large ({FileUtils.human_readable_size(file_size)}), skipping")
            return False

        # ── Read file preview ────────────────────────────
        file_preview = read_file_preview(file_path)
        if not file_preview:
            logger.warning(f"Could not read preview for: {file_path}")
            return False

        # ── Get file info ────────────────────────────────
        file_info = FileUtils.get_file_info(file_path)
        logger.info(f"File: {file_info['name']} ({file_info['size_human']}, {file_info['extension']})")

        # ── Prompt the LLM ───────────────────────────────
        prompt = f"""Analyze this file and define its category and new filename.
File: {os.path.basename(file_path)} ({file_info['size_human']})
Ext: {file_info['extension']}

Preview:
---
{file_preview}
---

Rules:
1. Provide a logical Category (Invoice, Notes, Image, etc.)
2. Provide a descriptive lowercase filename with underscores (keep original extension).

Respond ONLY in this format:
CATEGORY: <category>
NEW_FILENAME: <filename>"""

        logger.info("Querying LLM for file analysis...")
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        logger.debug(f"LLM response:\n{response_text}")

        # ── Parse LLM response ──────────────────────────
        category, new_filename = parse_llm_response(response_text, file_path)

        if not new_filename:
            logger.warning(f"LLM could not determine action for {file_path}")
            return False

        # Sanitize the LLM-suggested filename
        new_filename = FileUtils.sanitize_filename(new_filename)
        logger.info(f"Decision — Category: {category} | Name: {new_filename}")

        # ── Execute file operations ──────────────────────
        # Just rename in place
        destination = os.path.dirname(file_path)
        new_path = move_and_rename_file(file_path, destination, new_filename, category)

        if new_path and not new_path.startswith("Error"):
            # ── Index in vector database ─────────────────
            if _config.enable_vector_search:
                memory = get_memory()
                memory.index_file(new_path, {"category": category})

            logger.info(f"✓ Done: {os.path.basename(file_path)} → {new_path}")
            return True
        else:
            logger.error(f"File operation failed: {new_path}")
            return False

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False


def process_folder(folder_path: str) -> dict:
    """Process an entire folder — walk all files and organize each one.

    Recursively finds all files in the given folder and processes
    each through the LLM pipeline. Handles large folders by
    processing files one at a time.

    Args:
        folder_path: Path to the folder to process

    Returns:
        Dict with 'processed', 'failed', 'total', 'skipped' counts
    """
    results = {"processed": 0, "failed": 0, "total": 0, "skipped": 0}

    if not os.path.isdir(folder_path):
        logger.error(f"Not a directory: {folder_path}")
        return results

    # Collect all files in the folder (recursive)
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            full_path = os.path.join(root, f)
            all_files.append(full_path)

    results["total"] = len(all_files)
    logger.info(f"📁 Processing folder: {os.path.basename(folder_path)} ({len(all_files)} files)")

    for i, file_path in enumerate(all_files, 1):
        filename = os.path.basename(file_path)
        logger.info(f"  [{i}/{len(all_files)}] {filename}")

        # Skip hidden files and system files
        if filename.startswith(".") or filename.startswith("~"):
            logger.debug(f"  Skipping hidden/temp file: {filename}")
            results["skipped"] += 1
            continue

        try:
            success = process_new_file(file_path)
            if success:
                results["processed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            logger.error(f"  Error processing {filename}: {e}")
            results["failed"] += 1

    logger.info(
        f"📁 Folder done: {results['processed']} organized, "
        f"{results['failed']} failed, {results['skipped']} skipped"
    )
    return results


def read_file_preview(file_path: str, max_chars: int = None) -> str:
    """Read a preview of the file content.

    Supports text files and PDFs. For PDFs, extracts text via PyMuPDF.

    Args:
        file_path: Path to the file
        max_chars: Maximum characters to read (uses config default)

    Returns:
        File preview text, or empty string on failure
    """
    if max_chars is None:
        max_chars = _config.max_preview_chars

    file_ext = Path(file_path).suffix.lower()

    try:
        # PDF files — use PyMuPDF
        if file_ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                    if len(text) >= max_chars:
                        break
                doc.close()
                return text[:max_chars]
            except ImportError:
                logger.warning("PyMuPDF (fitz) not installed — falling back to pypdf")
                try:
                    import pypdf
                    with open(file_path, "rb") as f:
                        reader = pypdf.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() or ""
                            if len(text) >= max_chars:
                                break
                    return text[:max_chars]
                except ImportError:
                     logger.warning("Neither PyMuPDF nor pypdf installed — reading PDF skipped")
                     return ""

        # Image files — use OCR
        if file_ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
            try:
                text = ocr.extract_text_from_image(file_path, max_chars)
                if not text:
                    logger.warning(f"No text extracted via OCR for: {file_path}")
                return text
            except Exception as e:
                logger.error(f"OCR failed for {file_path}: {e}")
                return ""

        # Text-based files
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            preview = f.read(max_chars)
            return preview

    except Exception as e:
        logger.error(f"Could not read file preview: {e}")
        return ""


def parse_llm_response(response: str, file_path: str) -> tuple:
    """Parse LLM response to extract categorization decisions.

    Expected format:
        CATEGORY: <value>
        NEW_FILENAME: <value>

    Args:
        response: LLM response text
        file_path: Original file path (used as fallback filename)

    Returns:
        (category, new_filename)
    """
    try:
        lines = response.strip().split("\n")
        category = "Unknown"
        new_filename = os.path.basename(file_path)  # Default: keep original

        for line in lines:
            line = line.strip()
            if line.upper().startswith("CATEGORY:"):
                category = line.split(":", 1)[1].strip()
            elif line.upper().startswith("NEW_FILENAME:"):
                new_filename = line.split(":", 1)[1].strip()

        return category, new_filename

    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}")
        return "Unknown", None
