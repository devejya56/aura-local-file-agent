import sqlite3
import os
import shutil

def undo_last_move():
    """Undoes the last file move operation."""
    conn = sqlite3.connect('file_moves.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM moves ORDER BY timestamp DESC LIMIT 1')
    move = cursor.fetchone()
    
    if move:
        move_id, original_path, new_path, timestamp = move
        if os.path.exists(new_path):
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(new_path, original_path)
            cursor.execute('DELETE FROM moves WHERE id = ?', (move_id,))
            conn.commit()
            print(f"Undone: {new_path} -> {original_path}")
        else:
            print(f"Error: File not found at {new_path}")
    else:
        print("No moves to undo.")
    
    conn.close()

if __name__ == '__main__':
    undo_last_move()
