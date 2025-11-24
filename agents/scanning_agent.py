"""
Background CCTV Scanning Agent
Manages background scanning tasks for CCTV footage
"""
import sys
import os
import threading
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from surveillance import surveillance_yolo_deepface
from database import get_db_connection
from agents.report_agent import generate_cctv_scan_report, generate_aggregate_report
from agents.notification_agent import notify_match_found
from utils.notification_utils import send_scan_complete_notification
from utils.websocket_utils import (
    notify_scan_started,
    notify_scan_progress,
    notify_scan_complete,
    notify_match_found_realtime
)

def start_background_scan(case_id, cctv_list, target_image_path):
    """
    Start background CCTV scanning in a separate thread.
    
    Args:
        case_id: Case ID
        cctv_list: List of CCTV locations to scan
        target_image_path: Path to target person image
        
    Returns:
        scan_task_id: ID of created scan task
    """
    try:
        # Create scan task in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO scan_tasks (case_id, status, total_cctvs, started_at)
            VALUES (?, ?, ?, ?)
        """, (case_id, 'pending', len(cctv_list), datetime.now().isoformat()))
        
        scan_task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"[INFO] Created scan task {scan_task_id} for case {case_id}")
        
        # Start background thread
        thread = threading.Thread(
            target=_run_background_scan,
            args=(scan_task_id, case_id, cctv_list, target_image_path),
            daemon=True
        )
        thread.start()
        
        return scan_task_id
        
    except Exception as e:
        print(f"[ERROR] Failed to start background scan: {e}")
        return None


def _run_background_scan(scan_task_id, case_id, cctv_list, target_image_path):
    """
    Internal function to run background scan (runs in separate thread).
    """
    try:
        print(f"[INFO] Starting background scan for task {scan_task_id}")
        
        # Notify dashboard that scan started
        notify_scan_started(case_id, scan_task_id, len(cctv_list))
        
        # Update status to in_progress
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scan_tasks SET status = 'in_progress' WHERE id = ?
        """, (scan_task_id,))
        conn.commit()
        conn.close()
        
        # Scan each CCTV
        for idx, cctv in enumerate(cctv_list):
            print(f"[INFO] Scanning CCTV {idx + 1}/{len(cctv_list)}: {cctv['name']}")
            
            scan_result = scan_single_cctv(
                scan_task_id,
                case_id,
                cctv,
                target_image_path
            )
            
            # Update progress
            update_scan_progress(scan_task_id, idx + 1)
            
            # Notify dashboard of progress
            notify_scan_progress(case_id, scan_task_id, idx + 1, len(cctv_list))
            
            # Small delay between scans
            time.sleep(1)
        
        # Generate aggregate report
        print(f"[INFO] Generating aggregate report for task {scan_task_id}")
        aggregate_report_path = generate_aggregate_report(case_id, scan_task_id)
        
        # Update scan task as completed
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scan_tasks 
            SET status = 'completed', completed_at = ?, pdf_report_path = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), aggregate_report_path, scan_task_id))
        conn.commit()
        conn.close()
        
        # Get total detections
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(detections_found) as total_detections
            FROM cctv_scan_results WHERE scan_task_id = ?
        """, (scan_task_id,))
        stats = dict(cursor.fetchone())
        total_detections = stats.get('total_detections', 0) or 0
        conn.close()
        
        # Notify dashboard that scan completed
        notify_scan_complete(case_id, scan_task_id, total_detections)
        
        # Send email notification
        print(f"[INFO] Sending scan complete notification for case {case_id}")
        send_scan_complete_notification(case_id, scan_task_id, aggregate_report_path)
        
        print(f"[SUCCESS] Background scan completed for task {scan_task_id}")
        
    except Exception as e:
        print(f"[ERROR] Background scan failed for task {scan_task_id}: {e}")
        
        # Update status to failed
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scan_tasks SET status = 'failed', completed_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), scan_task_id))
            conn.commit()
            conn.close()
        except Exception as db_error:
            print(f"[ERROR] Failed to update scan task status: {db_error}")


def scan_single_cctv(scan_task_id, case_id, cctv_data, target_image_path):
    """
    Scan a single CCTV video for target person.
    
    Args:
        scan_task_id: Scan task ID
        case_id: Case ID
        cctv_data: CCTV location data
        target_image_path: Path to target person image
        
    Returns:
        Scan result dictionary
    """
    try:
        start_time = time.time()
        
        # Run surveillance
        video_path = cctv_data.get('video_path', '')
        
        # Check if video exists
        if not os.path.exists(video_path):
            print(f"[WARNING] Video not found: {video_path}")
            result = {
                "success": False,
                "error": f"Video not found: {video_path}",
                "matches": []
            }
        else:
            result = surveillance_yolo_deepface(target_image_path, video_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate individual CCTV report
        report_path = generate_cctv_scan_report(
            case_id,
            cctv_data['cctv_id'],
            result
        )
        
        # Save scan result to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cctv_scan_results 
            (scan_task_id, cctv_id, video_path, detections_found, scan_duration_seconds, report_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            scan_task_id,
            cctv_data['cctv_id'],
            video_path,
            result.get('matches_found', 0),
            duration,
            report_path
        ))
        
        conn.commit()
        conn.close()
        
        # If matches found, send notification
        if result.get('matches_found', 0) > 0:
            print(f"[MATCH] Found {result['matches_found']} match(es) in {cctv_data['name']}")
            
            # Notify dashboard in real-time
            notify_match_found_realtime(
                case_id,
                cctv_data['cctv_id'],
                result['matches'][0]
            )
            
            # Notify about match
            notify_match_found(
                case_id,
                {
                    "frame": result['matches'][0]['frame'],
                    "score": result['matches'][0]['similarity'],
                    "image_path": result['matches'][0]['image_path']
                },
                cctv_data
            )
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Failed to scan CCTV {cctv_data.get('name', 'Unknown')}: {e}")
        return {
            "success": False,
            "error": str(e),
            "matches": []
        }


def update_scan_progress(scan_task_id, scanned_count):
    """
    Update scan progress in database.
    
    Args:
        scan_task_id: Scan task ID
        scanned_count: Number of CCTVs scanned so far
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scan_tasks SET scanned_cctvs = ? WHERE id = ?
        """, (scanned_count, scan_task_id))
        
        conn.commit()
        conn.close()
        
        print(f"[INFO] Updated scan progress: {scanned_count} CCTVs scanned")
        
    except Exception as e:
        print(f"[ERROR] Failed to update scan progress: {e}")


def get_scan_status(scan_task_id):
    """
    Get current status of a scan task.
    
    Args:
        scan_task_id: Scan task ID
        
    Returns:
        Dictionary with scan status information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scan_tasks WHERE id = ?", (scan_task_id,))
        task = cursor.fetchone()
        
        if not task:
            return None
        
        task_dict = dict(task)
        
        # Get scan results
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(detections_found) as total_detections
            FROM cctv_scan_results WHERE scan_task_id = ?
        """, (scan_task_id,))
        
        stats = dict(cursor.fetchone())
        
        conn.close()
        
        return {
            **task_dict,
            "total_detections": stats.get('total_detections', 0) or 0,
            "progress_percent": (task_dict['scanned_cctvs'] / task_dict['total_cctvs'] * 100) if task_dict['total_cctvs'] > 0 else 0
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to get scan status: {e}")
        return None
