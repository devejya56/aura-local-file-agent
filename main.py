"""Aura — Main Entry Point

Local-first AI file organization agent.
Monitors a directory, uses LLMs to categorize files, and auto-organizes them.

Usage:
    python main.py               Start the file watcher
    python main.py --undo         Undo the last file move
    python main.py --history      Show recent move history
    python main.py --search       Search indexed files
"""

import sys
import time
import os
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

from config import get_config, setup_directories
from agent_core import process_new_file
from memory import init_memory
from database import init_db, get_move_count
from undo import undo_last_move, show_history

# ── ASCII Banner ─────────────────────────────────────────────

BANNER = r"""
     █████╗ ██╗   ██╗██████╗  █████╗
    ██╔══██╗██║   ██║██╔══██╗██╔══██╗
    ███████║██║   ██║██████╔╝███████║
    ██╔══██║██║   ██║██╔══██╗██╔══██║
    ██║  ██║╚██████╔╝██║  ██║██║  ██║
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

    🧠  Local AI File Organization Agent
    ─────────────────────────────────────
"""

# ── Track stats ──────────────────────────────────────────────

files_processed = 0
files_failed = 0


class FileWatcherHandler(FileSystemEventHandler):
    """Handles file system events from Watchdog."""

    def __init__(self, config):
        super().__init__()
        self.config = config

    def on_created(self, event):
        """Triggered when a new file is created in the watch directory."""
        global files_processed, files_failed

        if event.is_directory:
            return

        # Wait for file to finish writing
        time.sleep(self.config.file_settle_delay)

        file_path = event.src_path
        logger.info(f"📄 New file detected: {file_path}")

        success = process_new_file(file_path)
        if success:
            files_processed += 1
        else:
            files_failed += 1


def setup_logging(config):
    """Configure loguru logging."""
    # Remove default handler
    logger.remove()

    # Console output
    logger.add(
        sys.stderr,
        level=config.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <level>{message}</level>",
        colorize=True,
    )

    # File output
    if config.log_file:
        logger.add(
            config.log_file,
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {message}",
        )


def do_search(config):
    """Interactive semantic search across indexed files."""
    memory = init_memory(config.db_path)
    stats = memory.get_stats()
    print(f"\n  Aura Search — {stats['total_documents']} document(s) indexed\n")

    if stats["total_documents"] == 0:
        print("  No documents indexed yet. Let Aura process some files first!")
        return

    query = input("  Search query: ").strip()
    if not query:
        return

    results = memory.search(query, top_k=5)

    if not results:
        print("  No results found.")
        return

    print(f"\n  Found {len(results)} result(s):\n")
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        filename = meta.get("filename", "Unknown")
        category = meta.get("category", "?")
        distance = r.get("distance", 0)
        snippet = r.get("document", "")[:100]
        print(f"  {i}. [{category}] {filename}")
        print(f"     Score: {1 - distance:.2%} match")
        print(f"     Preview: {snippet}...")
        print()


def start_agent():
    """Initialize all subsystems and start the file watcher."""
    global files_processed, files_failed

    # Load config
    config = get_config()

    # Setup logging
    setup_logging(config)

    # Print banner
    print(BANNER)

    # Initialize subsystems
    logger.info("Initializing Aura...")

    setup_directories(config)
    logger.info(f"Watch directory: {os.path.abspath(config.watch_directory)}")
    logger.info(f"Archive directory: {os.path.abspath(config.archive_directory)}")

    init_db()
    logger.info("Database ready")

    if config.enable_vector_search:
        memory = init_memory(config.db_path)
        stats = memory.get_stats()
        logger.info(f"Vector DB ready ({stats['total_documents']} docs indexed)")

    logger.info(f"LLM: {config.llm_model} @ {config.ollama_base_url}")
    logger.info(f"Total moves in history: {get_move_count()}")

    # Set up file watcher
    event_handler = FileWatcherHandler(config)
    observer = Observer()
    observer.schedule(event_handler, config.watch_directory, recursive=False)

    print(f"    📂 Watching: {os.path.abspath(config.watch_directory)}")
    print(f"    📁 Archive:  {os.path.abspath(config.archive_directory)}")
    print(f"    🤖 Model:    {config.llm_model}")
    print(f"\n    Drop files into the watch folder to organize them!")
    print(f"    Press Ctrl+C to stop.\n")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n")
        logger.info("Shutting down Aura...")
        observer.stop()

    observer.join()

    # Print summary
    print(f"\n    ── Session Summary ──")
    print(f"    Files processed: {files_processed}")
    print(f"    Files failed:    {files_failed}")
    print(f"    Total in history: {get_move_count()}")
    print(f"\n    Goodbye! 👋\n")


def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Aura — Local AI File Organization Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py               Start watching for files
  python main.py --undo         Undo the last file move
  python main.py --history      Show recent move history
  python main.py --search       Search indexed files
        """,
    )
    parser.add_argument("--undo", action="store_true", help="Undo the last file move")
    parser.add_argument("--history", action="store_true", help="Show recent move history")
    parser.add_argument("--search", action="store_true", help="Semantic search across files")

    args = parser.parse_args()

    if args.undo:
        init_db()
        undo_last_move()
    elif args.history:
        init_db()
        show_history()
    elif args.search:
        config = get_config()
        setup_logging(config)
        do_search(config)
    else:
        start_agent()


if __name__ == "__main__":
    main()
