"""
Blockchain-style report hashing utilities
"""
import hashlib
import json
from datetime import datetime

def generate_report_hash(report_data):
    """
    Generate SHA256 hash for a report (blockchain-style).
    
    Args:
        report_data: Dictionary containing report information
        
    Returns:
        SHA256 hash string
    """
    # Convert report to JSON string (sorted keys for consistency)
    report_json = json.dumps(report_data, sort_keys=True)
    
    # Generate SHA256 hash
    hash_object = hashlib.sha256(report_json.encode('utf-8'))
    return hash_object.hexdigest()

def create_blockchain_report(case_id, match_data, location_data):
    """
    Create a blockchain-style report with hash.
    
    Args:
        case_id: Case ID
        match_data: Match details (frame, score, etc.)
        location_data: CCTV location details
        
    Returns:
        Dictionary with report and blockchain hash
    """
    timestamp = datetime.now().isoformat()
    
    report = {
        "case_id": case_id,
        "timestamp": timestamp,
        "match_details": {
            "frame_number": match_data.get("frame_number"),
            "confidence_score": match_data.get("score"),
            "saved_image_path": match_data.get("saved_img_path")
        },
        "location_details": {
            "cctv_id": location_data.get("id"),
            "location_name": location_data.get("name"),
            "geohash": location_data.get("geohash"),
            "coordinates": {
                "lat": location_data.get("lat"),
                "lon": location_data.get("lon")
            }
        },
        "report_metadata": {
            "generated_at": timestamp,
            "system_version": "1.0",
            "region": "Bhopal/Sehore"
        }
    }
    
    # Generate blockchain hash
    blockchain_hash = generate_report_hash(report)
    
    return {
        "report": report,
        "blockchain_hash": blockchain_hash,
        "timestamp": timestamp
    }

def verify_report_hash(report, provided_hash):
    """
    Verify if a report's hash matches the provided hash.
    
    Args:
        report: Report dictionary
        provided_hash: Hash to verify against
        
    Returns:
        Boolean indicating if hash is valid
    """
    calculated_hash = generate_report_hash(report)
    return calculated_hash == provided_hash
