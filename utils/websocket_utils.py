"""
WebSocket utilities for real-time dashboard updates
"""
import asyncio
import json
from datetime import datetime
import threading

# Simple in-memory storage for WebSocket connections
# In production, use Redis or similar for multi-process support
active_connections = []
update_queue = asyncio.Queue() if hasattr(asyncio, 'Queue') else None

def send_scan_progress_update(case_id, progress_data):
    """
    Send scan progress update to dashboard via WebSocket.
    
    Args:
        case_id: Case ID
        progress_data: Dictionary with progress information
    """
    try:
        message = {
            "type": "scan_progress",
            "case_id": case_id,
            "timestamp": datetime.now().isoformat(),
            **progress_data
        }
        
        # Add to queue for async processing
        broadcast_to_dashboard("scan_progress", message)
        
        print(f"[WebSocket] Sent progress update for case {case_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to send WebSocket update: {e}")


def broadcast_to_dashboard(message_type, data):
    """
    Broadcast message to all connected dashboard clients.
    
    Args:
        message_type: Type of message
        data: Message data
    """
    try:
        message = {
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Store in global queue for WebSocket server to process
        # This is a simplified implementation
        # In production, use proper WebSocket server (e.g., websockets library)
        
        print(f"[WebSocket] Broadcasting {message_type}: {json.dumps(data, indent=2)}")
        
        # For now, just log the message
        # Actual WebSocket implementation would send to connected clients
        
    except Exception as e:
        print(f"[ERROR] Failed to broadcast message: {e}")


def notify_scan_started(case_id, scan_task_id, total_cctvs):
    """
    Notify dashboard that scan has started.
    """
    send_scan_progress_update(case_id, {
        "scan_task_id": scan_task_id,
        "status": "started",
        "total_cctvs": total_cctvs,
        "scanned_cctvs": 0,
        "progress_percent": 0
    })


def notify_scan_progress(case_id, scan_task_id, scanned_cctvs, total_cctvs):
    """
    Notify dashboard of scan progress.
    """
    send_scan_progress_update(case_id, {
        "scan_task_id": scan_task_id,
        "status": "in_progress",
        "total_cctvs": total_cctvs,
        "scanned_cctvs": scanned_cctvs,
        "progress_percent": (scanned_cctvs / total_cctvs * 100) if total_cctvs > 0 else 0
    })


def notify_scan_complete(case_id, scan_task_id, total_detections):
    """
    Notify dashboard that scan is complete.
    """
    send_scan_progress_update(case_id, {
        "scan_task_id": scan_task_id,
        "status": "completed",
        "total_detections": total_detections,
        "progress_percent": 100
    })


def notify_match_found_realtime(case_id, cctv_id, match_data):
    """
    Notify dashboard immediately when a match is found.
    """
    broadcast_to_dashboard("match_found", {
        "case_id": case_id,
        "cctv_id": cctv_id,
        "frame": match_data.get('frame'),
        "similarity": match_data.get('similarity'),
        "image_path": match_data.get('image_path')
    })


# Note: This is a simplified WebSocket implementation
# For production, implement a proper WebSocket server using the 'websockets' library
# Example:
#
# import websockets
# 
# async def websocket_handler(websocket, path):
#     active_connections.append(websocket)
#     try:
#         async for message in websocket:
#             # Handle incoming messages
#             pass
#     finally:
#         active_connections.remove(websocket)
#
# async def broadcast_loop():
#     while True:
#         if not update_queue.empty():
#             message = await update_queue.get()
#             for conn in active_connections:
#                 try:
#                     await conn.send(json.dumps(message))
#                 except:
#                     pass
#         await asyncio.sleep(0.1)
#
# def start_websocket_server(host='localhost', port=8765):
#     asyncio.run(websockets.serve(websocket_handler, host, port))
