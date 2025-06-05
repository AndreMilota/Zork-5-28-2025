import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "rooms.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL
        )
        """
    )
    cur.execute("DELETE FROM rooms")
    cur.executemany(
        "INSERT INTO rooms (id, description) VALUES (?, ?)",
        [
            ("room1", "You are in a small, dimly lit cave. A narrow passage leads east."),
            ("room2", "You stand in a forest clearing. Paths lead west and south."),
        ],
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
