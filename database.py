import sqlite3
import os
import numpy as np
import io

DB_PATH = "missing_persons.db"

def adapt_array(arr):
    """
    http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
    """
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

# Register numpy array adapter
sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("array", convert_array)

def init_db():
    """Initialize the SQLite database and create tables."""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    # Table: missing_cases
    c.execute('''
        CREATE TABLE IF NOT EXISTS missing_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            description TEXT,
            last_seen_geohash TEXT,
            last_seen_location TEXT,
            time_lost TIMESTAMP,
            date_reported TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            embedding array,
            transcript TEXT,
            emotion TEXT,
            image_path TEXT,
            email TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')

    # Table: videos_scanned
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos_scanned (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            video_name TEXT,
            video_path TEXT,
            cctv_location_id INTEGER,
            matches_found INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES missing_cases(id)
        )
    ''')

    # Table: match_logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS match_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            frame_number INTEGER,
            score REAL,
            saved_img_path TEXT,
            cctv_location_id INTEGER,
            geohash TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES missing_cases(id)
        )
    ''')
    
    # Table: geohash_predictions (for route prediction caching/logging)
    c.execute('''
        CREATE TABLE IF NOT EXISTS geohash_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            start_geohash TEXT,
            predicted_path TEXT,
            cctv_videos TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES missing_cases(id)
        )
    ''')
    
    # Table: blockchain_reports
    c.execute('''
        CREATE TABLE IF NOT EXISTS blockchain_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            report_data TEXT,
            blockchain_hash TEXT UNIQUE,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES missing_cases(id)
        )
    ''')
    
    # Table: cctv_locations (for reference)
    c.execute('''
        CREATE TABLE IF NOT EXISTS cctv_locations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            lat REAL,
            lon REAL,
            geohash TEXT,
            type TEXT,
            video_path TEXT,
            description TEXT
        )
    ''')
    
    # Table: scan_tasks (for background CCTV scanning)
    c.execute('''
        CREATE TABLE IF NOT EXISTS scan_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            status TEXT DEFAULT 'pending',
            total_cctvs INTEGER,
            scanned_cctvs INTEGER DEFAULT 0,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            pdf_report_path TEXT,
            FOREIGN KEY(case_id) REFERENCES missing_cases(id)
        )
    ''')
    
    # Table: cctv_scan_results (detailed scan results per CCTV)
    c.execute('''
        CREATE TABLE IF NOT EXISTS cctv_scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_task_id INTEGER,
            cctv_id INTEGER,
            video_path TEXT,
            detections_found INTEGER DEFAULT 0,
            scan_duration_seconds REAL,
            report_path TEXT,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(scan_task_id) REFERENCES scan_tasks(id),
            FOREIGN KEY(cctv_id) REFERENCES cctv_locations(id)
        )
    ''')

    conn.commit()
    
    # Populate CCTV locations if empty
    c.execute("SELECT COUNT(*) FROM cctv_locations")
    if c.fetchone()[0] == 0:
        from config.bhopal_sehore_locations import CCTV_LOCATIONS
        for loc in CCTV_LOCATIONS:
            c.execute('''
                INSERT INTO cctv_locations (id, name, lat, lon, geohash, type, video_path, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (loc["id"], loc["name"], loc["lat"], loc["lon"], loc["geohash"], 
                  loc["type"], loc["video_path"], loc["description"]))
        conn.commit()
    
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    init_db()
