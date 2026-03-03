"""Aura - Main Entry Point

File system monitor using Watchdog.
Triggers the AI agent when new files are detected.
"""

import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

from agent_core import process_new_file
from memory import init_memory

# Configuration
WATCH_DIRECTORY = os.getenv("WATCH_DIR", "./Downloads_Test")
DB_PATH = os.getenv("DB_PATH", "./local_file_db")


class FileWatcherHandler(FileSystemEventHandler):
    """Handles file system events."""
    
    def on_created(self, event):
        """Triggered when a new file is created."""
        if not event.is_directory:
            # Wait briefly to ensure file writing is complete
            time.sleep(1)
            logger.info(f"New file detected: {event.src_path}")
            process_new_file(event.src_path)
    
    def on_modified(self, event):
        """Triggered when a file is modified."""
        if not event.is_directory:
            logger.debug(f"File modified: {event.src_path}")


def start_agent():
    """Initialize and start the Aura file watching agent."""
    # Initialize the vector database
    init_memory(DB_PATH)
    logger.info("Aura agent initialized")
    
    # Create watch directory if it doesn't exist
    if not os.path.exists(WATCH_DIRECTORY):
        os.makedirs(WATCH_DIRECTORY)
        logger.info(f"Created watch directory: {WATCH_DIRECTORY}")
    
    # Set up file system observer
    event_handler = FileWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    
    logger.info(f"Aura is now monitoring: {WATCH_DIRECTORY}")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Aura shutting down...")
        observer.stop()
    observer.join()
    logger.info("Aura stopped")


if __name__ == "__main__":
    start_agent()
