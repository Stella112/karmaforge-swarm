import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_db(db_path="karmaforge.db"):
    """
    Initializes the SQLite database for persistent memory across VPS restarts.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Table to store every trade intent and validation artifact
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                pair TEXT NOT NULL,
                artifact TEXT NOT NULL
            )
        ''')
        
        # Table to store exactly when and how the Reflector updated the config
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evolution_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                target_key TEXT NOT NULL,
                old_value REAL,
                new_value REAL,
                reason TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        logger.info(f"Database initialized successfully at {db_path}.")
        return conn
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return None

if __name__ == "__main__":
    init_db()
