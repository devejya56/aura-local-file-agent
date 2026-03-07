"""Aura — Desktop Application

Native desktop app using pywebview with Flask backend.
Provides a dashboard, history, search, and settings interface
with an orange/cream liquid glass design.
"""

import os
import sys
import time
import json
import queue
import threading
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, jsonify, request, Response
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

from config import get_config, setup_directories
from agent_core import process_new_file, process_folder, llm
from memory import init_memory, get_memory
from database import init_db, get_recent_moves, get_move_count
from undo import undo_last_move
from utils import FileUtils

# ── Flask App ────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", template_folder="templates")

config = get_config()

# Event queue for Server-Sent Events (live activity feed)
event_queue = queue.Queue(maxsize=100)

# Stats tracking
stats = {
    "files_processed": 0,
    "files_failed": 0,
    "folders_processed": 0,
    "agent_running": False,
    "start_time": None,
}

# Activity log (in-memory, last 50 events)
activity_log = []
MAX_ACTIVITY = 50


def push_event(event_type: str, data: dict):
    """Push an event to the SSE queue and activity log."""
    event = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }
    activity_log.insert(0, event)
    if len(activity_log) > MAX_ACTIVITY:
        activity_log.pop()
    try:
        event_queue.put_nowait(event)
    except queue.Full:
        pass


# ── File Watcher (Background Thread) ────────────────────────

class WebFileWatcherHandler(FileSystemEventHandler):
    """Handles file system events and pushes updates to the web UI."""

    def on_created(self, event):
        file_path = event.src_path

        # Handle folders
        if event.is_directory:
            time.sleep(config.file_settle_delay + 1.0)  # extra delay for folder copies
            folder_name = os.path.basename(file_path)

            push_event("folder_detected", {
                "filename": f"📁 {folder_name}",
                "path": file_path,
                "status": "processing",
            })

            logger.info(f"📁 New folder detected: {file_path}")
            results = process_folder(file_path)

            processed = results.get("processed", 0)
            failed = results.get("failed", 0)
            total = results.get("total", 0)

            stats["files_processed"] += processed
            stats["files_failed"] += failed
            stats["folders_processed"] += 1

            push_event("folder_processed", {
                "filename": f"📁 {folder_name}",
                "path": file_path,
                "status": "success",
                "details": f"{processed}/{total} files organized",
            })
            return

        # Handle single files
        time.sleep(config.file_settle_delay)
        filename = os.path.basename(file_path)

        push_event("file_detected", {
            "filename": filename,
            "path": file_path,
            "status": "processing",
        })

        logger.info(f"📄 New file detected: {file_path}")
        success = process_new_file(file_path)

        if success:
            stats["files_processed"] += 1
            push_event("file_processed", {
                "filename": filename,
                "path": file_path,
                "status": "success",
            })
        else:
            stats["files_failed"] += 1
            push_event("file_failed", {
                "filename": filename,
                "path": file_path,
                "status": "failed",
            })


observer = None


def start_watcher():
    """Start the file watcher in the background."""
    global observer

    if observer and observer.is_alive():
        return

    setup_directories(config)
    event_handler = WebFileWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, config.watch_directory, recursive=False)
    observer.daemon = True
    observer.start()

    stats["agent_running"] = True
    stats["start_time"] = datetime.now().isoformat()

    push_event("agent_started", {"message": "Aura is watching for files"})
    logger.info(f"Watcher started on: {os.path.abspath(config.watch_directory)}")


def stop_watcher():
    """Stop the file watcher."""
    global observer

    if observer and observer.is_alive():
        observer.stop()
        observer.join(timeout=5)
        stats["agent_running"] = False
        push_event("agent_stopped", {"message": "Aura stopped watching"})
        logger.info("Watcher stopped")


# ── Setup Logging ────────────────────────────────────────────

def setup_logging():
    """Configure loguru for the app."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=config.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <level>{message}</level>",
        colorize=True,
    )
    if config.log_file:
        logger.add(config.log_file, level="DEBUG", rotation="10 MB", retention="7 days")


# ── Routes: Pages ────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")


# ── Routes: API ──────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    """Get dashboard statistics."""
    memory = get_memory()
    mem_stats = memory.get_stats()

    return jsonify({
        "files_processed": stats["files_processed"],
        "files_failed": stats["files_failed"],
        "folders_processed": stats["folders_processed"],
        "total_moves": get_move_count(),
        "total_indexed": mem_stats["total_documents"],
        "agent_running": stats["agent_running"],
        "start_time": stats["start_time"],
        "watch_directory": os.path.abspath(config.watch_directory),
        "archive_directory": os.path.abspath(config.archive_directory),
        "model": config.llm_model,
    })


@app.route("/api/activity")
def api_activity():
    """Get recent activity feed."""
    return jsonify(activity_log)


@app.route("/api/history")
def api_history():
    """Get move history from the database."""
    n = request.args.get("n", 20, type=int)
    moves = get_recent_moves(n)
    return jsonify(moves)


@app.route("/api/search", methods=["POST"])
def api_search():
    """Semantic search across indexed files."""
    data = request.get_json()
    query = data.get("query", "").strip()
    top_k = data.get("top_k", 5)

    if not query:
        return jsonify({"error": "Query is required"}), 400

    memory = get_memory()
    results = memory.search(query, top_k=top_k)
    return jsonify(results)


@app.route("/api/undo", methods=["POST"])
def api_undo():
    """Undo the last file move."""
    success = undo_last_move()
    return jsonify({"success": success})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """RAG Chat endpoint to answer questions about indexed files."""
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    memory = get_memory()
    result = memory.generate_answer(query, llm)
    return jsonify(result)


@app.route("/api/select-folder", methods=["GET"])
def api_select_folder():
    """Open native OS dialog to select a folder."""
    import webview
    
    if not webview.windows:
        return jsonify({"error": "No active window"}), 400
        
    window = webview.windows[0]
    folder_path = window.create_file_dialog(webview.FOLDER_DIALOG)
    
    if folder_path and len(folder_path) > 0:
        return jsonify({"path": folder_path[0]})
    return jsonify({"path": None})


@app.route("/api/process-folder", methods=["POST"])
def api_process_folder():
    """Process an existing folder explicitly chosen by the user."""
    data = request.get_json()
    folder_path = data.get("path", "").strip()

    if not folder_path or not os.path.isdir(folder_path):
        return jsonify({"error": "Invalid folder path"}), 400

    # Run in background to avoid blocking the API
    def background_process():
        folder_name = os.path.basename(folder_path)
        push_event("folder_detected", {
            "filename": f"📁 Select: {folder_name}",
            "path": folder_path,
            "status": "processing",
        })

        results = process_folder(folder_path)

        processed = results.get("processed", 0)
        failed = results.get("failed", 0)
        total = results.get("total", 0)

        stats["files_processed"] += processed
        stats["files_failed"] += failed
        stats["folders_processed"] += 1

        push_event("folder_processed", {
            "filename": f"📁 {folder_name}",
            "path": folder_path,
            "status": "success",
            "details": f"{processed}/{total} files organized",
        })

    threading.Thread(target=background_process, daemon=True).start()
    return jsonify({"success": True, "message": "Processing started"})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload a file to the watch directory."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    dest_path = os.path.join(config.watch_directory, file.filename)
    file.save(dest_path)

    push_event("file_uploaded", {
        "filename": file.filename,
        "path": dest_path,
    })

    return jsonify({"success": True, "filename": file.filename})


@app.route("/api/watcher/start", methods=["POST"])
def api_start_watcher():
    """Start the file watcher."""
    start_watcher()
    return jsonify({"success": True, "running": True})


@app.route("/api/watcher/stop", methods=["POST"])
def api_stop_watcher():
    """Stop the file watcher."""
    stop_watcher()
    return jsonify({"success": True, "running": False})


@app.route("/api/config")
def api_config():
    """Get current configuration."""
    return jsonify({
        "watch_directory": config.watch_directory,
        "archive_directory": config.archive_directory,
        "db_path": config.db_path,
        "ollama_base_url": config.ollama_base_url,
        "llm_model": config.llm_model,
        "llm_temperature": config.llm_temperature,
        "enable_vector_search": config.enable_vector_search,
        "enable_backup": config.enable_backup,
        "log_level": config.log_level,
    })


@app.route("/api/archived-files")
def api_archived_files():
    """List organized files in the archive directory."""
    archive_dir = config.archive_directory
    result = []

    if not os.path.exists(archive_dir):
        return jsonify(result)

    for root, dirs, files in os.walk(archive_dir):
        for f in files:
            full_path = os.path.join(root, f)
            category = os.path.relpath(root, archive_dir)
            if category == ".":
                category = "Uncategorized"
            try:
                info = FileUtils.get_file_info(full_path)
                info["category"] = category
                result.append(info)
            except Exception:
                pass

    result.sort(key=lambda x: x.get("modified", ""), reverse=True)
    return jsonify(result)


# ── SSE: Live Event Stream ───────────────────────────────────

@app.route("/api/events")
def api_events():
    """Server-Sent Events endpoint for live activity updates."""
    def generate():
        while True:
            try:
                event = event_queue.get(timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Main ─────────────────────────────────────────────────────

def main():
    """Start the Aura desktop application."""
    setup_logging()

    print(r"""
     █████╗ ██╗   ██╗██████╗  █████╗
    ██╔══██╗██║   ██║██╔══██╗██╔══██╗
    ███████║██║   ██║██████╔╝███████║
    ██╔══██║██║   ██║██╔══██╗██╔══██║
    ██║  ██║╚██████╔╝██║  ██║██║  ██║
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

    🧠  Desktop App — Liquid Glass
    ─────────────────────────────────────
    """)

    # Initialize subsystems
    init_db()
    init_memory(config.db_path)
    logger.info("All subsystems initialized")

    # Auto-start the file watcher
    start_watcher()

    print(f"    📂 Watching: {os.path.abspath(config.watch_directory)}")
    print(f"    🤖 Model: {config.llm_model}")
    print(f"    🖥️  Launching native window...")
    print()

    # Start Flask in a background thread
    flask_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5000, debug=False, threaded=True, use_reloader=False),
        daemon=True,
    )
    flask_thread.start()

    # Give Flask a moment to start
    time.sleep(1.0)

    # Launch native desktop window with pywebview
    import webview
    window = webview.create_window(
        "Aura — AI File Organization Agent",
        "http://127.0.0.1:5000",
        width=1280,
        height=820,
        min_size=(900, 600),
        background_color="#1B1B1B",
        text_select=False,
    )
    webview.start()

    # Window closed — clean up
    stop_watcher()
    print("\n    Goodbye! 👋")


if __name__ == "__main__":
    main()
