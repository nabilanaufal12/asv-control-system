# core/navigation.py

import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Menghitung jarak antara dua titik di bumi (dalam kilometer)
    menggunakan formula Haversine.
    """
    R = 6371  # Radius bumi dalam kilometer

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Menghitung arah (bearing) dari titik 1 ke titik 2 (dalam derajat).
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad

    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)

    initial_bearing = math.atan2(y, x)
    initial_bearing = math.degrees(initial_bearing)
    bearing = (initial_bearing + 360) % 360

    return bearing

# Contoh penggunaan:
# home_lat, home_lon = -6.2088, 106.8456
# wp1_lat, wp1_lon = -6.2095, 106.8470
#
# distance_to_wp1 = haversine(home_lat, home_lon, wp1_lat, wp1_lon)
# bearing_to_wp1 = calculate_bearing(home_lat, home_lon, wp1_lat, wp1_lon)
#
# print(f"Jarak ke Waypoint 1: {distance_to_wp1:.3f} km")
# print(f"Arah ke Waypoint 1: {bearing_to_wp1:.2f} derajat")