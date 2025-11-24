import random
import math
import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geohash_utils import encode_location, decode_geohash

# Average human walking speed: 3.5 - 5 km/h
# In m/s: ~1.0 - 1.4 m/s
MIN_SPEED = 1.0
MAX_SPEED = 1.4
AVERAGE_SPEED_KMH = 4.0  # Average walking speed in km/h

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def get_nearest_cctv_in_radius(lat, lon, radius_meters, max_count=3):
    """
    Get nearest CCTV locations within a radius, limited to max_count.
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_meters: Search radius in meters
        max_count: Maximum number of CCTVs to return (default 3)
        
    Returns:
        List of CCTV locations sorted by distance (max max_count items)
    """
    from config.bhopal_sehore_locations import CCTV_LOCATIONS
    
    cctv_with_distance = []
    
    for cctv in CCTV_LOCATIONS:
        distance = haversine_distance(lat, lon, cctv["lat"], cctv["lon"])
        if distance <= radius_meters:
            cctv_with_distance.append({
                **cctv,
                "distance": distance
            })
    
    # Sort by distance and return top max_count
    cctv_with_distance.sort(key=lambda x: x["distance"])
    return cctv_with_distance[:max_count]

def calculate_search_radius_from_time(hours_elapsed):
    """
    Calculate search radius based on time elapsed since person went missing.
    
    Time brackets:
    - < 1 hour: 1.5 km radius
    - 1-3 hours: 5 km radius
    - 3-6 hours: 8 km radius
    - 6-12 hours: 12 km radius
    - > 12 hours: 20 km radius
    
    Args:
        hours_elapsed: Hours since person went missing
        
    Returns:
        Search radius in meters
    """
    if hours_elapsed < 1:
        return 1500  # 1.5 km
    elif hours_elapsed < 3:
        return 5000  # 5 km
    elif hours_elapsed < 6:
        return 8000  # 8 km
    elif hours_elapsed < 12:
        return 12000  # 12 km
    else:
        return 20000  # 20 km

def predict_route_with_time_analysis(start_lat, start_lon, time_lost, current_time=None):
    """
    Predict route with time-based analysis.
    Selects nearest CCTVs based on elapsed time and walking distance.
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        time_lost: Datetime when person went missing
        current_time: Current datetime (defaults to now)
        
    Returns:
        Dictionary with route prediction and CCTV locations (max 3)
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Calculate elapsed time
    if isinstance(time_lost, str):
        time_lost = datetime.fromisoformat(time_lost)
    
    elapsed = current_time - time_lost
    hours_elapsed = elapsed.total_seconds() / 3600
    
    # Calculate search radius based on time
    search_radius = calculate_search_radius_from_time(hours_elapsed)
    
    # Get nearest CCTVs within radius (max 3)
    nearest_cctvs = get_nearest_cctv_in_radius(start_lat, start_lon, search_radius, max_count=3)
    
    # Build route prediction
    route = []
    cctv_videos = []
    
    # Add starting point
    route.append({
        "lat": start_lat,
        "lon": start_lon,
        "geohash": encode_location(start_lat, start_lon),
        "step": 0,
        "time_elapsed_hours": 0,
        "search_radius_km": search_radius / 1000
    })
    
    # Add predicted CCTV locations
    for idx, cctv in enumerate(nearest_cctvs):
        route.append({
            "lat": cctv["lat"],
            "lon": cctv["lon"],
            "geohash": encode_location(cctv["lat"], cctv["lon"]),
            "step": idx + 1,
            "nearest_cctv": cctv["name"],
            "cctv_id": cctv["id"],
            "cctv_distance": round(cctv["distance"], 2),
            "video_path": cctv["video_path"]
        })
        
        cctv_videos.append({
            "cctv_id": cctv["id"],
            "name": cctv["name"],
            "video_path": cctv["video_path"],
            "distance": round(cctv["distance"], 2)
        })
    
    return {
        "route": route,
        "cctv_videos": cctv_videos,
        "num_cctv_locations": len(cctv_videos),
        "time_analysis": {
            "hours_elapsed": round(hours_elapsed, 2),
            "search_radius_meters": search_radius,
            "search_radius_km": round(search_radius / 1000, 2),
            "max_walking_distance_km": round(hours_elapsed * AVERAGE_SPEED_KMH, 2)
        }
    }

def predict_next_location_random(lat, lon, time_delta_seconds=3600):
    """
    Predict next location based on random walk with urban bias (simplified).
    time_delta_seconds: Time elapsed in seconds.
    """
    # Calculate max distance possible
    speed = random.uniform(MIN_SPEED, MAX_SPEED)
    distance = speed * time_delta_seconds
    
    # Random bearing (0-360 degrees)
    # Urban bias: favor cardinal directions slightly
    bearing = random.uniform(0, 360)
    
    # Calculate new lat/lon
    R = 6371000
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    new_lat_rad = math.asin(math.sin(lat_rad)*math.cos(distance/R) + 
                            math.cos(lat_rad)*math.sin(distance/R)*math.cos(math.radians(bearing)))
    
    new_lon_rad = lon_rad + math.atan2(math.sin(math.radians(bearing))*math.sin(distance/R)*math.cos(lat_rad),
                                       math.cos(distance/R)-math.sin(lat_rad)*math.sin(new_lat_rad))
    
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)
    
    return new_lat, new_lon

def generate_route_prediction_with_cctv(start_lat, start_lon, steps=5):
    """
    Generate route prediction biased toward CCTV locations in Bhopal/Sehore.
    Uses urban path model that favors movement toward known landmarks.
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        steps: Number of prediction steps
        
    Returns:
        List of predicted locations with CCTV matches
    """
    from config.bhopal_sehore_locations import CCTV_LOCATIONS, get_nearest_cctv_location
    
    path = []
    current_lat, current_lon = start_lat, start_lon
    
    # Add start point with nearest CCTV
    nearest_cctv, distance = get_nearest_cctv_location(current_lat, current_lon)
    path.append({
        "lat": current_lat,
        "lon": current_lon,
        "geohash": encode_location(current_lat, current_lon),
        "step": 0,
        "nearest_cctv": nearest_cctv["name"],
        "cctv_id": nearest_cctv["id"],
        "cctv_distance": round(distance, 2),
        "video_path": nearest_cctv["video_path"]
    })
    
    visited_cctv_ids = {nearest_cctv["id"]}
    
    for i in range(1, steps + 1):
        # Get unvisited CCTV locations
        available_cctv = [loc for loc in CCTV_LOCATIONS if loc["id"] not in visited_cctv_ids]
        
        if not available_cctv:
            # If all visited, allow revisiting
            available_cctv = CCTV_LOCATIONS
        
        # Calculate weights based on distance (closer = higher probability)
        weights = []
        for loc in available_cctv:
            dist = haversine_distance(current_lat, current_lon, loc["lat"], loc["lon"])
            # Inverse distance weighting (closer locations have higher weight)
            weight = 1.0 / (dist + 100)  # +100 to avoid division by zero
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Select next CCTV location based on weights
        next_cctv = random.choices(available_cctv, weights=weights, k=1)[0]
        
        # Move toward the selected CCTV location (but not exactly to it)
        # Add some randomness to simulate realistic movement
        progress = random.uniform(0.3, 0.8)  # Move 30-80% toward target
        
        next_lat = current_lat + (next_cctv["lat"] - current_lat) * progress
        next_lon = current_lon + (next_cctv["lon"] - current_lon) * progress
        
        # Find nearest CCTV to predicted location
        nearest_cctv, distance = get_nearest_cctv_location(next_lat, next_lon)
        
        path.append({
            "lat": next_lat,
            "lon": next_lon,
            "geohash": encode_location(next_lat, next_lon),
            "step": i,
            "nearest_cctv": nearest_cctv["name"],
            "cctv_id": nearest_cctv["id"],
            "cctv_distance": round(distance, 2),
            "video_path": nearest_cctv["video_path"]
        })
        
        visited_cctv_ids.add(nearest_cctv["id"])
        current_lat, current_lon = next_lat, next_lon
    
    return path

def generate_route_prediction(start_lat, start_lon, steps=5, interval_minutes=30, time_lost=None):
    """
    Generate a sequence of predicted locations.
    If time_lost is provided, uses time-based analysis.
    Otherwise, uses CCTV-biased prediction.
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        steps: Number of prediction steps (ignored if time_lost is provided)
        interval_minutes: Time interval (ignored if time_lost is provided)
        time_lost: Datetime when person went missing (optional)
        
    Returns:
        Route prediction data
    """
    if time_lost:
        # Use time-based prediction
        return predict_route_with_time_analysis(start_lat, start_lon, time_lost)
    else:
        # Use CCTV-biased prediction (legacy)
        path = generate_route_prediction_with_cctv(start_lat, start_lon, steps)
        return {
            "route": path,
            "cctv_videos": get_cctv_videos_for_route(path),
            "num_cctv_locations": len(get_cctv_videos_for_route(path))
        }

def get_cctv_videos_for_route(route_prediction):
    """
    Extract unique CCTV video paths from route prediction.
    
    Args:
        route_prediction: List of predicted locations
        
    Returns:
        List of unique CCTV video information
    """
    seen_ids = set()
    cctv_videos = []
    
    for point in route_prediction:
        cctv_id = point.get("cctv_id")
        if cctv_id and cctv_id not in seen_ids:
            cctv_videos.append({
                "cctv_id": cctv_id,
                "name": point.get("nearest_cctv"),
                "video_path": point.get("video_path"),
                "distance": point.get("cctv_distance")
            })
            seen_ids.add(cctv_id)
    
    return cctv_videos

