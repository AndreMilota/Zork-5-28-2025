# Room definitions / database
import sqlite3
import json
from typing import Dict, Optional
from pathlib import Path

# Database file path
DB_PATH = Path("db/rooms.db")

class RoomDatabase:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with the rooms table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    exits TEXT NOT NULL
                )
            """)
            
            # Check if we need to populate initial data
            cursor = conn.execute("SELECT COUNT(*) FROM rooms")
            if cursor.fetchone()[0] == 0:
                self._populate_initial_data(conn)
    
    def _populate_initial_data(self, conn):
        """Populate the database with initial room data."""
        initial_rooms = {
            "hall": {
                "description": (
                    "A dimly lit hallway with rough stone walls. Faintly glowing torches "
                    "cast long shadows across the cracked floor, and cobwebs hang in the "
                    "corners. Ancient portraits, nearly faded to nothing, line the walls "
                    "with ghostly faces. A heavy oak door, its iron handle worn smooth, "
                    "leads east."
                    "There is a very dusty floor to ceiling mirror on one side which will allow someone to see a reflection of themselves."
                    "There is a golden crown on the floor."
                ),
                "exits": {"east": "kitchen"},
            },
            "kitchen": {
                "description": (
                    "Dusty pots hang from the ceiling above a scarred wooden table. "
                    "A large stone hearth dominates one side, still carrying the faint "
                    "smell of old herbs and smoke. Rusty utensils litter the counters, "
                    "and a grimy window barely lets in any light. An archway to the "
                    "west returns to the hallway."
                ),
                "exits": {"west": "hall"},
            },
        }
        
        for room_id, room_data in initial_rooms.items():
            conn.execute(
                "INSERT INTO rooms (id, description, exits) VALUES (?, ?, ?)",
                (room_id, room_data["description"], json.dumps(room_data["exits"]))
            )
    
    def get_room(self, room_id: str) -> Optional[Dict]:
        """Get a room by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT description, exits FROM rooms WHERE id = ?",
                (room_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "description": row[0],
                    "exits": json.loads(row[1])
                }
        return None
    
    def update_room_description(self, room_id: str, new_description: str) -> bool:
        """Update a room's description."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE rooms SET description = ? WHERE id = ?",
                (new_description, room_id)
            )
            return cursor.rowcount > 0
    
    def get_all_rooms(self) -> Dict[str, Dict]:
        """Get all rooms as a dictionary (for backward compatibility)."""
        rooms = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, description, exits FROM rooms")
            for row in cursor.fetchall():
                rooms[row[0]] = {
                    "description": row[1],
                    "exits": json.loads(row[2])
                }
        return rooms
    
    def add_room(self, room_id: str, description: str, exits: Dict[str, str]) -> bool:
        """Add a new room to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO rooms (id, description, exits) VALUES (?, ?, ?)",
                    (room_id, description, json.dumps(exits))
                )
                return True
        except sqlite3.IntegrityError:
            return False  # Room already exists
    
    def room_exists(self, room_id: str) -> bool:
        """Check if a room exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM rooms WHERE id = ?", (room_id,))
            return cursor.fetchone() is not None

# Create a global instance
room_db = RoomDatabase()

# Backward compatibility: create a ROOMS object that behaves like the original dictionary
class RoomsProxy:
    def __init__(self, db: RoomDatabase):
        self.db = db
    
    def __getitem__(self, key: str) -> Dict:
        room = self.db.get_room(key)
        if room is None:
            raise KeyError(f"Room '{key}' not found")
        return room
    
    def __setitem__(self, key: str, value: Dict):
        if self.db.room_exists(key):
            self.db.update_room_description(key, value["description"])
        else:
            self.db.add_room(key, value["description"], value["exits"])
    
    def __contains__(self, key: str) -> bool:
        return self.db.room_exists(key)
    
    def get(self, key: str, default=None):
        room = self.db.get_room(key)
        return room if room is not None else default
    
    def keys(self):
        return self.db.get_all_rooms().keys()
    
    def values(self):
        return self.db.get_all_rooms().values()
    
    def items(self):
        return self.db.get_all_rooms().items()

# Create the backward-compatible ROOMS object
ROOMS = RoomsProxy(room_db)

player_description = ("You are a short Man about 50 years old. Have a long green beard with liken growing in it." ""
"Your eys are blue eyes and short black hair. You are wearing a battered brown leather jacket "
"torn blue jeans and boots. You bave a backpack with six pairs of socks and nothing else. "
"Have a bow with six arrows one of which is broken. You are wearing a comical hat made of red "
"felt that has little bells on it. "
"You have bulging pockets, bulging with something that may be important some day.")