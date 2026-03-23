import sqlite3
import os

DB_PATH = 'missing_persons.db'

def migrate():
    """Adds gait_model_path to missing_cases and match_type to match_logs if they don't exist."""
    print(f"Connecting to database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database not found. Exiting.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add gait_model_path to missing_cases
    try:
        cursor.execute("ALTER TABLE missing_cases ADD COLUMN gait_model_path TEXT;")
        print("Successfully added 'gait_model_path' column to 'missing_cases' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("'gait_model_path' column already exists in 'missing_cases'.")
        else:
            print(f"Error altering missing_cases: {e}")

    # Add match_type to match_logs
    try:
        cursor.execute("ALTER TABLE match_logs ADD COLUMN match_type TEXT DEFAULT 'face';")
        print("Successfully added 'match_type' column to 'match_logs' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("'match_type' column already exists in 'match_logs'.")
        else:
            print(f"Error altering match_logs: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
