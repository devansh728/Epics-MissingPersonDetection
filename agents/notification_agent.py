"""
Notification Agent for email alerts and blockchain reports
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.notification_utils import send_match_notification, send_case_filed_notification
from utils.blockchain_utils import create_blockchain_report
from database import get_db_connection

def notify_match_found(case_id, match_data, location_data):
    """
    Send notification when a match is found.
    Creates blockchain report and sends email.
    
    Args:
        case_id: Case ID
        match_data: Match details (frame, score, image path)
        location_data: CCTV location details
        
    Returns:
        Dictionary with notification status and blockchain hash
    """
    try:
        # Get case details from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM missing_cases WHERE id = ?", (case_id,))
        case_row = cursor.fetchone()
        
        if not case_row:
            return {"success": False, "error": "Case not found"}
        
        case_data = dict(case_row)
        
        # Create blockchain report
        blockchain_report = create_blockchain_report(case_id, match_data, location_data)
        
        # Save blockchain report to database
        cursor.execute("""
            INSERT INTO blockchain_reports (case_id, report_data, blockchain_hash)
            VALUES (?, ?, ?)
        """, (case_id, str(blockchain_report["report"]), blockchain_report["blockchain_hash"]))
        
        conn.commit()
        
        # Send email notification (if email is configured)
        email_sent = False
        recipient_email = case_data.get("email")
        
        if recipient_email and recipient_email != "":
            email_sent = send_match_notification(
                recipient_email,
                case_data,
                match_data,
                location_data,
                blockchain_report["blockchain_hash"]
            )
        
        conn.close()
        
        return {
            "success": True,
            "blockchain_hash": blockchain_report["blockchain_hash"],
            "email_sent": email_sent,
            "timestamp": blockchain_report["timestamp"]
        }
        
    except Exception as e:
        print(f"Error in notify_match_found: {e}")
        return {"success": False, "error": str(e)}

def notify_case_filed(case_id, route_prediction):
    """
    Send notification when a case is filed.
    
    Args:
        case_id: Case ID
        route_prediction: Predicted route data
        
    Returns:
        Dictionary with notification status
    """
    try:
        # Get case details from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM missing_cases WHERE id = ?", (case_id,))
        case_row = cursor.fetchone()
        
        if not case_row:
            return {"success": False, "error": "Case not found"}
        
        case_data = dict(case_row)
        conn.close()
        
        # Send email notification (if email is configured)
        email_sent = False
        recipient_email = case_data.get("email")
        
        if recipient_email and recipient_email != "":
            email_sent = send_case_filed_notification(
                recipient_email,
                case_data,
                route_prediction
            )
        
        return {
            "success": True,
            "email_sent": email_sent
        }
        
    except Exception as e:
        print(f"Error in notify_case_filed: {e}")
        return {"success": False, "error": str(e)}
