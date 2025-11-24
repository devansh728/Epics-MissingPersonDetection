"""
COMPLETE DATABASE MIGRATION - Run this with Streamlit STOPPED
"""

import sqlite3
import os
import sys

DB_PATH = "missing_persons.db"

print("\n" + "=" * 70)
print("⚠️  IMPORTANT: Make sure Streamlit is STOPPED before running this!")
print("=" * 70)

# Check if database is locked
try:
    test_conn = sqlite3.connect(DB_PATH, timeout=1)
    test_conn.execute("BEGIN IMMEDIATE")
    test_conn.rollback()
    test_conn.close()
except sqlite3.OperationalError:
    print("\n❌ ERROR: Database is locked!")
    print("   Please stop Streamlit first (Ctrl+C in the terminal)")
    print("   Then run this script again.\n")
    sys.exit(1)

# Expected schema
EXPECTED_SCHEMA = {
    "missing_cases": [
        ("name", "TEXT"),
        ("age", "INTEGER"),
        ("description", "TEXT"),
        ("last_seen_geohash", "TEXT"),
        ("last_seen_location", "TEXT"),
        ("time_lost", "TIMESTAMP"),
        ("date_reported", "TIMESTAMP"),
        ("embedding", "array"),
        ("transcript", "TEXT"),
        ("emotion", "TEXT"),
        ("image_path", "TEXT"),
        ("email", "TEXT"),
        ("status", "TEXT"),
    ],
    "geohash_predictions": [
        ("case_id", "INTEGER"),
        ("start_geohash", "TEXT"),
        ("predicted_path", "TEXT"),
        ("cctv_videos", "TEXT"),
        ("timestamp", "TIMESTAMP"),
    ],
    "videos_scanned": [
        ("case_id", "INTEGER"),
        ("video_name", "TEXT"),
        ("video_path", "TEXT"),
        ("cctv_location_id", "INTEGER"),
        ("matches_found", "INTEGER"),
        ("timestamp", "TIMESTAMP"),
    ],
    "match_logs": [
        ("case_id", "INTEGER"),
        ("frame_number", "INTEGER"),
        ("score", "REAL"),
        ("saved_img_path", "TEXT"),
        ("cctv_location_id", "INTEGER"),
        ("geohash", "TEXT"),
        ("timestamp", "TIMESTAMP"),
    ],
    "scan_tasks": [
        ("case_id", "INTEGER"),
        ("status", "TEXT"),
        ("total_cctvs", "INTEGER"),
        ("scanned_cctvs", "INTEGER"),
        ("started_at", "TIMESTAMP"),
        ("completed_at", "TIMESTAMP"),
        ("pdf_report_path", "TEXT"),
    ],
    "cctv_scan_results": [
        ("scan_task_id", "INTEGER"),
        ("cctv_id", "INTEGER"),
        ("video_path", "TEXT"),
        ("detections_found", "INTEGER"),
        ("scan_duration_seconds", "REAL"),
        ("report_path", "TEXT"),
        ("scanned_at", "TIMESTAMP"),
    ],
}

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("\n🔄 Starting migration...\n")
total_added = 0

for table_name, expected_columns in EXPECTED_SCHEMA.items():
    # Check if table exists
    c.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    if not c.fetchone():
        print(
            f"⚠️  Table '{table_name}' doesn't exist - will be created on next app run"
        )
        continue

    # Get existing columns
    c.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in c.fetchall()}

    print(f"📋 {table_name}")

    for col_name, col_type in expected_columns:
        if col_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                print(f"   ✅ Added: {col_name}")
                total_added += 1
            except Exception as e:
                print(f"   ❌ Error adding {col_name}: {e}")

conn.commit()
conn.close()

print("\n" + "=" * 70)
if total_added > 0:
    print(f"✅ SUCCESS! Added {total_added} missing column(s)")
else:
    print("✅ All columns already exist - no migration needed")
print("=" * 70)
print("\n✅ You can now restart Streamlit!\n")
