"""
Email notification utilities using Gmail SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.email_config import (
    get_email_config,
    MATCH_FOUND_SUBJECT,
    MATCH_FOUND_BODY,
    CASE_FILED_SUBJECT,
    CASE_FILED_BODY,
)


def send_email(recipient_email, subject, body):
    """
    Send email via Gmail SMTP.

    Args:
        recipient_email: Recipient's email address
        subject: Email subject
        body: Email body (plain text)

    Returns:
        Boolean indicating success
    """
    try:
        config = get_email_config()

        # Create message
        msg = MIMEMultipart()
        msg["From"] = config["sender_email"]
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Add body
        msg.attach(MIMEText(body, "plain"))

        # Connect to Gmail SMTP server
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()

        # Login
        server.login(config["sender_email"], config["sender_password"])

        # Send email
        text = msg.as_string()
        server.sendmail(config["sender_email"], recipient_email, text)

        # Disconnect
        server.quit()

        print(f"✅ Email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def send_match_notification(
    recipient_email, case_data, match_data, location_data, blockchain_hash
):
    """
    Send notification when a match is found.

    Args:
        recipient_email: Email to send notification to
        case_data: Case information
        match_data: Match details
        location_data: CCTV location details
        blockchain_hash: Blockchain report hash

    Returns:
        Boolean indicating success
    """
    subject = MATCH_FOUND_SUBJECT.format(case_id=case_data.get("id", "N/A"))

    body = MATCH_FOUND_BODY.format(
        recipient_name=case_data.get("name", "User"),
        case_id=case_data.get("id", "N/A"),
        person_name=case_data.get("name", "N/A"),
        age=case_data.get("age", "N/A"),
        location_name=location_data.get("name", "N/A"),
        cctv_id=location_data.get("id", "N/A"),
        confidence=round(match_data.get("score", 0) * 100, 2),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        geohash=location_data.get("geohash", "N/A"),
        blockchain_hash=blockchain_hash,
    )

    return send_email(recipient_email, subject, body)


def send_case_filed_notification(recipient_email, case_data, route_prediction):
    """
    Send notification when a case is filed.

    Args:
        recipient_email: Email to send notification to
        case_data: Case information
        route_prediction: Predicted route data

    Returns:
        Boolean indicating success
    """
    subject = CASE_FILED_SUBJECT.format(case_id=case_data.get("id", "N/A"))

    # Format predicted route
    route_text = ""
    if route_prediction and len(route_prediction) > 0:
        for i, point in enumerate(route_prediction[:5]):  # Show first 5 points
            route_text += f"  {i+1}. Lat: {point.get('lat', 0):.4f}, Lon: {point.get('lon', 0):.4f}\n"
    else:
        route_text = "  No route prediction available"

    body = CASE_FILED_BODY.format(
        recipient_name=case_data.get("name", "User"),
        case_id=case_data.get("id", "N/A"),
        person_name=case_data.get("name", "N/A"),
        age=case_data.get("age", "N/A"),
        last_seen_location=case_data.get("last_seen_location", "N/A"),
        date_reported=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        emotion=case_data.get("emotion", "N/A"),
        geohash=case_data.get("geohash", "N/A"),
        predicted_route=route_text,
        num_cctv=len(route_prediction) if route_prediction else 0,
    )

    return send_email(recipient_email, subject, body)


def send_email_with_attachment(recipient_email, subject, body, attachment_path):
    """
    Send email with PDF attachment via Gmail SMTP.

    Args:
        recipient_email: Recipient's email address
        subject: Email subject
        body: Email body (plain text)
        attachment_path: Path to PDF file to attach

    Returns:
        Boolean indicating success
    """
    try:
        config = get_email_config()

        # Create message
        msg = MIMEMultipart()
        msg["From"] = config["sender_email"]
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Add body
        msg.attach(MIMEText(body, "plain"))

        # Add PDF attachment
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                pdf_attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(attachment_path),
                )
                msg.attach(pdf_attachment)

        # Connect to Gmail SMTP server
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()

        # Login
        server.login(config["sender_email"], config["sender_password"])

        # Send email
        text = msg.as_string()
        server.sendmail(config["sender_email"], recipient_email, text)

        # Disconnect
        server.quit()

        print(f"✅ Email with attachment sent successfully to {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email with attachment: {e}")
        return False


def send_scan_complete_notification(case_id, scan_task_id, pdf_report_path):
    """
    Send notification when CCTV scanning is complete.

    Args:
        case_id: Case ID
        scan_task_id: Scan task ID
        pdf_report_path: Path to aggregate PDF report

    Returns:
        Boolean indicating success
    """
    try:
        from database import get_db_connection

        # Get case details
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM missing_cases WHERE id = ?", (case_id,))
        case_row = cursor.fetchone()
        if not case_row:
            print(f"[ERROR] Case {case_id} not found for notification")
            return False
        case = dict(case_row)

        cursor.execute("SELECT * FROM scan_tasks WHERE id = ?", (scan_task_id,))
        scan_task_row = cursor.fetchone()
        if not scan_task_row:
            print(f"[ERROR] Scan task {scan_task_id} not found for notification")
            return False
        scan_task = dict(scan_task_row)

        cursor.execute(
            """
            SELECT SUM(detections_found) as total_detections
            FROM cctv_scan_results WHERE scan_task_id = ?
        """,
            (scan_task_id,),
        )
        stats_row = cursor.fetchone()
        stats = dict(stats_row) if stats_row else {"total_detections": 0}

        conn.close()

        recipient_email = case.get("email")
        if not recipient_email:
            print("[WARNING] No email address for case, skipping notification")
            return False

        total_detections = stats.get("total_detections", 0) or 0

        subject = f"🔍 CCTV Scan Complete - Case #{case_id}"

        body = f"""
Dear {case.get('name', 'User')},

Your CCTV scan for the missing person case has been completed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CASE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Case ID: {case.get('id', 'N/A')}
Name: {case.get('name', 'N/A')}
Age: {case.get('age', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCAN RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total CCTVs Scanned: {scan_task.get('scanned_cctvs', 0)}
Total Detections: {total_detections}
Status: {scan_task.get('status', 'N/A')}
Completed At: {scan_task.get('completed_at', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{'🎉 GOOD NEWS! Potential matches were found in the CCTV footage.' if total_detections > 0 else '⚠️ No matches were found in the scanned CCTV footage.'}

Please find the detailed aggregate report attached to this email.
You can also view the results on the dashboard.

Thank you for using the Missing Person Detection System.

---
Missing Person Detection System
Bhopal/Sehore District
"""

        return send_email_with_attachment(
            recipient_email, subject, body, pdf_report_path
        )

    except Exception as e:
        print(f"[ERROR] Failed to send scan complete notification: {e}")
        return False
