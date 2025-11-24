import geohash2


def encode_location(lat, lon, precision=8):
    """Encode latitude and longitude into a geohash."""
    return geohash2.encode(lat, lon, precision=precision)


def decode_geohash(gh):
    """Decode a geohash into latitude and longitude."""
    lat, lon = geohash2.decode(gh)
    return float(lat), float(lon)


def get_neighbors(gh):
    """
    Get neighboring geohashes.
    geohash2 doesn't have a neighbors function, so we implement it manually.
    """
    try:
        # Decode the geohash to get lat/lon
        lat, lon = geohash2.decode(gh)
        # Ensure lat and lon are floats to avoid type errors
        lat = float(lat)
        lon = float(lon)
        precision = len(gh)

        # Calculate approximate degree offset based on precision
        # At precision 8, each character is roughly 0.00001 degrees
        offset = 0.0001 * (8 / precision)

        # Generate 8 neighbors (N, NE, E, SE, S, SW, W, NW)
        neighbors = {
            "n": geohash2.encode(lat + offset, lon, precision=precision),
            "ne": geohash2.encode(lat + offset, lon + offset, precision=precision),
            "e": geohash2.encode(lat, lon + offset, precision=precision),
            "se": geohash2.encode(lat - offset, lon + offset, precision=precision),
            "s": geohash2.encode(lat - offset, lon, precision=precision),
            "sw": geohash2.encode(lat - offset, lon - offset, precision=precision),
            "w": geohash2.encode(lat, lon - offset, precision=precision),
            "nw": geohash2.encode(lat + offset, lon - offset, precision=precision),
        }

        return neighbors
    except Exception as e:
        print(f"[ERROR] Failed to get neighbors for geohash {gh}: {e}")
        return {}
