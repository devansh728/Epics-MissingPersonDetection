import geohash2

def encode_location(lat, lon, precision=8):
    """Encode latitude and longitude into a geohash."""
    return geohash2.encode(lat, lon, precision=precision)

def decode_geohash(gh):
    """Decode a geohash into latitude and longitude."""
    lat, lon = geohash2.decode(gh)
    return float(lat), float(lon)

def get_neighbors(gh):
    """Get neighboring geohashes."""
    return geohash2.neighbors(gh)
