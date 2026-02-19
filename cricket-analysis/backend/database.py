import sqlite3
import os

class Database:
    def __init__(self):
        # Point to the database folder we created earlier
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, 'database', 'cricket.db')
        self.schema_path = os.path.join(base_dir, 'database', 'schema.sql')

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        return conn

    def init_db(self):
        """Initialize the database with the schema."""
        if not os.path.exists(self.schema_path):
            print(f"Warning: Schema file not found at {self.schema_path}")
            return

        with self.get_connection() as conn:
            with open(self.schema_path, 'r') as f:
                conn.executescript(f.read())
        print("Database initialized successfully.")

    def fetch_all(self, query, params=()):
        """Helper to fetch all results as a list of dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute(self, query, params=()):
        """Helper to execute a query (insert/update/delete)."""
        with self.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

# --- THIS IS THE PART YOU WERE MISSING ---
# Create the instance that app.py imports
db = Database()