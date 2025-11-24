"""
Bhopal/Sehore Region CCTV Locations Configuration
10 fixed locations with coordinates, geohashes, and video paths
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geohash_utils import encode_location

# Bhopal/Sehore district boundaries (approximate)
REGION_BOUNDS = {
    "min_lat": 22.9,
    "max_lat": 23.5,
    "min_lon": 77.0,
    "max_lon": 77.7
}

# 10 Fixed CCTV Locations in Bhopal/Sehore
CCTV_LOCATIONS = [
    {
        "id": 1,
        "name": "Bhopal Junction Railway Station",
        "lat": 23.2699,
        "lon": 77.4026,
        "type": "railway_station",
        "video_path": "cctv_footage/bhopal_junction.mp4",
        "description": "Main railway station, high foot traffic"
    },
    {
        "id": 2,
        "name": "Sehore Bus Stand",
        "lat": 23.2020,
        "lon": 77.0847,
        "type": "bus_stand",
        "video_path": "cctv_footage/sehore_busstand.mp4",
        "description": "Central bus terminal in Sehore"
    },
    {
        "id": 3,
        "name": "MP Nagar Zone 1",
        "lat": 23.2327,
        "lon": 77.4278,
        "type": "market",
        "video_path": "cctv_footage/mp_nagar.mp4",
        "description": "Major shopping and commercial area"
    },
    {
        "id": 4,
        "name": "Habibganj Railway Station",
        "lat": 23.2285,
        "lon": 77.4385,
        "type": "railway_station",
        "video_path": "cctv_footage/habibganj_station.mp4",
        "description": "Modern railway station"
    },
    {
        "id": 5,
        "name": "New Market Bhopal",
        "lat": 23.2599,
        "lon": 77.4126,
        "type": "market",
        "video_path": "cctv_footage/new_market.mp4",
        "description": "Traditional market area"
    },
    {
        "id": 6,
        "name": "BRTS Corridor - Roshanpura",
        "lat": 23.2156,
        "lon": 77.4304,
        "type": "transit",
        "video_path": "cctv_footage/brts_roshanpura.mp4",
        "description": "Bus Rapid Transit System stop"
    },
    {
        "id": 7,
        "name": "Sehore Railway Station",
        "lat": 23.2000,
        "lon": 77.0833,
        "type": "railway_station",
        "video_path": "cctv_footage/sehore_station.mp4",
        "description": "Sehore railway station"
    },
    {
        "id": 8,
        "name": "DB Mall Bhopal",
        "lat": 23.2420,
        "lon": 77.4347,
        "type": "mall",
        "video_path": "cctv_footage/db_mall.mp4",
        "description": "Popular shopping mall"
    },
    {
        "id": 9,
        "name": "Bhopal ISBT (Bus Stand)",
        "lat": 23.2543,
        "lon": 77.4071,
        "type": "bus_stand",
        "video_path": "cctv_footage/bhopal_isbt.mp4",
        "description": "Inter-State Bus Terminal"
    },
    {
        "id": 10,
        "name": "Ashoka Garden Market",
        "lat": 23.2156,
        "lon": 77.4481,
        "type": "market",
        "video_path": "cctv_footage/ashoka_garden.mp4",
        "description": "Local market and residential area"
    }
]

# Add geohash to each location
for loc in CCTV_LOCATIONS:
    loc["geohash"] = encode_location(loc["lat"], loc["lon"], precision=8)

# Location name to coordinates mapping
LOCATION_NAME_MAP = {
    loc["name"].lower(): {"lat": loc["lat"], "lon": loc["lon"], "geohash": loc["geohash"]}
    for loc in CCTV_LOCATIONS
}

# Common aliases for locations
LOCATION_ALIASES = {
    "bhopal junction": "bhopal junction railway station",
    "bhopal station": "bhopal junction railway station",
    "sehore bus": "sehore bus stand",
    "sehore stand": "sehore bus stand",
    "mp nagar": "mp nagar zone 1",
    "habibganj": "habibganj railway station",
    "new market": "new market bhopal",
    "brts": "brts corridor - roshanpura",
    "roshanpura": "brts corridor - roshanpura",
    "sehore station": "sehore railway station",
    "db mall": "db mall bhopal",
    "isbt": "bhopal isbt (bus stand)",
    "bus stand": "bhopal isbt (bus stand)",
    "ashoka garden": "ashoka garden market"
}

def is_location_in_region(lat, lon):
    """Check if coordinates are within Bhopal/Sehore district."""
    return (REGION_BOUNDS["min_lat"] <= lat <= REGION_BOUNDS["max_lat"] and
            REGION_BOUNDS["min_lon"] <= lon <= REGION_BOUNDS["max_lon"])

def get_location_by_name(name):
    """Get location details by name (case-insensitive, supports aliases)."""
    name_lower = name.lower().strip()
    
    # Check aliases first
    if name_lower in LOCATION_ALIASES:
        name_lower = LOCATION_ALIASES[name_lower]
    
    # Check exact match
    if name_lower in LOCATION_NAME_MAP:
        return LOCATION_NAME_MAP[name_lower]
    
    # Check partial match
    for loc_name, coords in LOCATION_NAME_MAP.items():
        if name_lower in loc_name or loc_name in name_lower:
            return coords
    
    return None

def get_nearest_cctv_location(lat, lon):
    """Find the nearest CCTV location to given coordinates."""
    from utils.route_utils import haversine_distance
    
    min_distance = float('inf')
    nearest_loc = None
    
    for loc in CCTV_LOCATIONS:
        dist = haversine_distance(lat, lon, loc["lat"], loc["lon"])
        if dist < min_distance:
            min_distance = dist
            nearest_loc = loc
    
    return nearest_loc, min_distance

def get_cctv_locations_in_radius(lat, lon, radius_meters=5000):
    """Get all CCTV locations within radius of given point."""
    from utils.route_utils import haversine_distance
    
    locations = []
    for loc in CCTV_LOCATIONS:
        dist = haversine_distance(lat, lon, loc["lat"], loc["lon"])
        if dist <= radius_meters:
            locations.append({**loc, "distance": dist})
    
    return sorted(locations, key=lambda x: x["distance"])
