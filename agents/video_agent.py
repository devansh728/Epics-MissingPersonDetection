import sys
import os
import sqlite3
# Add parent directory to path to import surveillance
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from surveillance import surveillance_yolo_deepface
except ImportError:
    # Fallback if surveillance.py is not found or has issues
    def surveillance_yolo_deepface(target, video):
        print(f"[MOCK] Scanning {video} for {target}")
        return

def scan_video(case_id, video_path, target_image_path):
    """
    Wrapper for surveillance.py logic.
    """
    print(f"Starting scan for Case {case_id} on video {video_path}")
    
    # Run the surveillance logic
    # Note: surveillance.py uses its own DB (face_db.sqlite) and output dir (output_frames)
    # We might need to sync results or just let it run.
    
    try:
        surveillance_yolo_deepface(target_image_path, video_path)
        return True
    except Exception as e:
        print(f"Error running surveillance: {e}")
        return False
