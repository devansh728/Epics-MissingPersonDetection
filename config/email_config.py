"""
Email Configuration for Gmail SMTP Notifications
"""
import os
from dotenv import load_dotenv
load_dotenv()    

# Gmail SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Email credentials (to be set by user)
# For security, use environment variables or config file
SENDER_EMAIL = os.getenv("SENDER_EMAIL")  # Replace with actual email
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  # Use Gmail App Password, not regular password

# Email Templates
MATCH_FOUND_SUBJECT = "🚨 ALERT: Potential Match Found - Case #{case_id}"

MATCH_FOUND_BODY = """
Dear {recipient_name},

This is an automated alert from the Missing Person Detection System.

A potential match has been found for the missing person case:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CASE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Case ID: {case_id}
Name: {person_name}
Age: {age}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: {location_name}
CCTV Camera: {cctv_id}
Confidence Score: {confidence}%
Timestamp: {timestamp}
Geohash: {geohash}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOCKCHAIN VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Report Hash: {blockchain_hash}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please log in to the system dashboard to view the matched images and detailed report.

This is an automated message. Please do not reply to this email.

---
Missing Person Detection System
Bhopal/Sehore District
"""

CASE_FILED_SUBJECT = "✅ Missing Person Complaint Filed - Case #{case_id}"

CASE_FILED_BODY = """
Dear {recipient_name},

Your missing person complaint has been successfully filed in the system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CASE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Case ID: {case_id}
Name: {person_name}
Age: {age}
Last Seen: {last_seen_location}
Date Reported: {date_reported}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Detected Emotion: {emotion}
Location Geohash: {geohash}

Predicted Route:
{predicted_route}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Our AI system is now monitoring {num_cctv} CCTV locations along the predicted route.
You will receive email alerts if any matches are found.

Thank you for using the Missing Person Detection System.

---
Missing Person Detection System
Bhopal/Sehore District
"""

def get_email_config():
    """Get email configuration (can be overridden by environment variables)."""
    import os
    return {
        "smtp_server": os.getenv("SMTP_SERVER", SMTP_SERVER),
        "smtp_port": int(os.getenv("SMTP_PORT", SMTP_PORT)),
        "sender_email": os.getenv("SENDER_EMAIL", SENDER_EMAIL),
        "sender_password": os.getenv("SENDER_PASSWORD", SENDER_PASSWORD)
    }
