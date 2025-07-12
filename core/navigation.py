# core/navigation.py

import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Menghitung jarak "garis lurus" antara dua titik di permukaan bumi
    menggunakan formula Haversine.

    Args:
        lat1, lon1: Lintang dan bujur titik pertama (dalam derajat).
        lat2, lon2: Lintang dan bujur titik kedua (dalam derajat).

    Returns:
        float: Jarak antara dua titik dalam meter.
    """
    R = 6371000  # Radius rata-rata bumi dalam meter

    # Konversi derajat ke radian
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Selisih lintang dan bujur
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Rumus Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Menghitung arah awal (bearing) dari titik 1 ke titik 2.

    Args:
        lat1, lon1: Lintang dan bujur titik pertama (dalam derajat).
        lat2, lon2: Lintang dan bujur titik kedua (dalam derajat).

    Returns:
        float: Arah dalam derajat (0-360), di mana 0 adalah Utara.
    """
    # Konversi derajat ke radian
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Selisih bujur
    dLon = lon2_rad - lon1_rad

    # Rumus Bearing
    y = math.sin(dLon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dLon)

    # Hitung bearing awal dan konversi ke derajat
    initial_bearing = math.atan2(y, x)
    initial_bearing_deg = math.degrees(initial_bearing)
    
    # Normalisasi bearing agar berada dalam rentang 0-360 derajat
    compass_bearing = (initial_bearing_deg + 360) % 360

    return compass_bearing

