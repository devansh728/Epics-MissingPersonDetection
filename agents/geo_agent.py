"""
Geo and Route Agents with Bhopal/Sehore regional validation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geohash_utils import encode_location, get_neighbors
from utils.route_utils import generate_route_prediction, get_cctv_videos_for_route
from config.bhopal_sehore_locations import (
    is_location_in_region, 
    get_location_by_name,
    get_nearest_cctv_location
)

def process_location(lat, lon):
    """
    Convert lat/lon to geohash and get neighbors.
    Validates location is in Bhopal/Sehore region.
    """
    # Validate region
    if not is_location_in_region(lat, lon):
        return {
            "error": "Location is outside Bhopal/Sehore district",
            "valid": False
        }
    
    gh = encode_location(lat, lon)
    neighbors = get_neighbors(gh)
    
    # Find nearest CCTV
    nearest_cctv, distance = get_nearest_cctv_location(lat, lon)
    
    return {
        "geohash": gh,
        "neighbors": neighbors,
        "valid": True,
        "nearest_cctv": nearest_cctv["name"],
        "cctv_distance": round(distance, 2)
    }

def process_location_by_name(location_name):
    """
    Process location by name (e.g., "Bhopal Junction").
    """
    coords = get_location_by_name(location_name)
    
    if not coords:
        return {
            "error": f"Location '{location_name}' not found in Bhopal/Sehore",
            "valid": False
        }
    
    return process_location(coords["lat"], coords["lon"])

def predict_route(start_lat, start_lon, time_lost=None):
    """
    Predict route with CCTV locations.
    If time_lost is provided, uses time-based analysis.
    """
    result = generate_route_prediction(start_lat, start_lon, steps=5, time_lost=time_lost)
    
    # Result already contains route, cctv_videos, and num_cctv_locations
    return result

