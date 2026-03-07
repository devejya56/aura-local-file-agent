"""Aura Undo Module — Reverse File Operations

Undo the last file move(s) by reading from the SQLite history database.
Can be run standalone: python undo.py
"""

import os
import shutil
from loguru import logger

from database import get_last_move, get_recent_moves, delete_move_record


def undo_last_move() -> bool:
    """Undo the most recent file move operation.
    
    Returns:
        True if the undo was successful
    """
    move = get_last_move()

    if not move:
        logger.info("No moves to undo.")
        print("✗ No moves to undo.")
        return False

    move_id = move["id"]
    original_path = move["original_path"]
    new_path = move["new_path"]
    category = move.get("category", "Unknown")
    timestamp = move.get("timestamp", "?")

    print(f"\n  Undoing last move:")
    print(f"  From: {new_path}")
    print(f"  To:   {original_path}")
    print(f"  Category: {category}  |  Time: {timestamp}")

    if not os.path.exists(new_path):
        logger.error(f"Cannot undo — file not found: {new_path}")
        print(f"\n  ✗ Error: File not found at {new_path}")
        return False

    try:
        # Recreate original directory if needed
        original_dir = os.path.dirname(original_path)
        if original_dir:
            os.makedirs(original_dir, exist_ok=True)

        # Move the file back
        shutil.move(new_path, original_path)

        # Remove the record from history
        delete_move_record(move_id)

        logger.info(f"Undo successful: {new_path} → {original_path}")
        print(f"\n  ✓ Undo successful!")
        return True

    except Exception as e:
        logger.error(f"Undo failed: {e}")
        print(f"\n  ✗ Undo failed: {e}")
        return False


def undo_last_n(n: int = 5) -> int:
    """Undo the last N file moves.
    
    Args:
        n: Number of moves to undo
        
    Returns:
        Number of successfully undone moves
    """
    moves = get_recent_moves(n)

    if not moves:
        print("✗ No moves to undo.")
        return 0

    print(f"\n  Undoing last {len(moves)} move(s)...\n")
    success_count = 0

    for move in moves:
        move_id = move["id"]
        original_path = move["original_path"]
        new_path = move["new_path"]

        if not os.path.exists(new_path):
            print(f"  ✗ Skipped (file missing): {new_path}")
            continue

        try:
            original_dir = os.path.dirname(original_path)
            if original_dir:
                os.makedirs(original_dir, exist_ok=True)

            shutil.move(new_path, original_path)
            delete_move_record(move_id)
            print(f"  ✓ {new_path} → {original_path}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print(f"\n  Done. {success_count}/{len(moves)} moves undone.")
    return success_count


def show_history(n: int = 10) -> None:
    """Display recent move history."""
    moves = get_recent_moves(n)

    if not moves:
        print("  No move history found.")
        return

    print(f"\n  Last {len(moves)} file move(s):\n")
    print(f"  {'ID':<5} {'Category':<15} {'Original → New'}")
    print(f"  {'─' * 60}")

    for move in moves:
        original = os.path.basename(move["original_path"])
        new = os.path.basename(move["new_path"])
        category = move.get("category", "?")
        print(f"  {move['id']:<5} {category:<15} {original} → {new}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--history":
        show_history()
    elif len(sys.argv) > 1 and sys.argv[1] == "--all":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        undo_last_n(n)
    else:
        undo_last_move()
