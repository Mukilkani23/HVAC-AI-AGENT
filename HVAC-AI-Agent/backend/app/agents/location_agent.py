"""
📍 Location Agent
Resolves building address to geographic coordinates using Google Maps Geocoding API.
Falls back to a simulated lookup table when the API key is not configured or the request fails.
"""

import random
import hashlib
import logging

import httpx

from app.config import GOOGLE_MAPS_API_KEY, GOOGLE_GEOCODING_URL

logger = logging.getLogger("LocationAgent")

# ── Climate-zone inference by latitude band ──────────────────────
def _infer_climate_zone(lat: float, lon: float) -> str:
    """Rough climate zone from latitude (good enough for demo)."""
    abs_lat = abs(lat)
    if abs_lat < 10:
        return "Hot Humid"
    elif abs_lat < 20:
        return "Warm Humid"
    elif abs_lat < 28:
        return "Hot Dry" if lon > 75 else "Warm Humid"
    elif abs_lat < 35:
        return "Composite"
    elif abs_lat < 45:
        return "Mixed Humid"
    elif abs_lat < 55:
        return "Temperate"
    return "Cold"


# ── Google Maps Geocoding ────────────────────────────────────────
async def _geocode_google(address: str) -> dict | None:
    """
    Call Google Maps Geocoding API and return parsed result.
    Returns None on any failure so the caller can fall back gracefully.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.info("GOOGLE_MAPS_API_KEY not set – skipping API call")
        return None

    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(GOOGLE_GEOCODING_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "OK" or not data.get("results"):
            logger.warning("Geocoding returned status=%s for '%s'", data.get("status"), address)
            return None

        result = data["results"][0]
        geometry = result["geometry"]["location"]
        components = {c["types"][0]: c["long_name"] for c in result.get("address_components", []) if c.get("types")}

        lat = round(geometry["lat"], 6)
        lon = round(geometry["lng"], 6)

        return {
            "lat": lat,
            "lon": lon,
            "formatted_address": result.get("formatted_address", address),
            "city": components.get("locality", components.get("administrative_area_level_2", "")),
            "state": components.get("administrative_area_level_1", ""),
            "country": components.get("country", ""),
            "climate_zone": _infer_climate_zone(lat, lon),
        }

    except httpx.HTTPStatusError as exc:
        logger.error("Geocoding HTTP error %s: %s", exc.response.status_code, exc)
    except httpx.RequestError as exc:
        logger.error("Geocoding request failed: %s", exc)
    except (KeyError, IndexError, ValueError) as exc:
        logger.error("Geocoding parse error: %s", exc)

    return None

# ── OpenStreetMap Nominatim Fallback (Free, No API Key) ──────────
async def _geocode_nominatim(address: str) -> dict | None:
    """Fallback geocoding using OpenStreetMap Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "HVAC-AI-Agent-Demo/1.0"
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        if not data:
            logger.warning("Nominatim returned no results for '%s'", address)
            return None

        result = data[0]
        lat = round(float(result["lat"]), 6)
        lon = round(float(result["lon"]), 6)
        display_name = result.get("display_name", address)
        parts = display_name.split(", ")

        return {
            "lat": lat,
            "lon": lon,
            "formatted_address": display_name,
            "city": parts[0] if parts else "",
            "state": parts[-2] if len(parts) > 1 else "",
            "country": parts[-1] if parts else "",
            "climate_zone": _infer_climate_zone(lat, lon),
        }
    except Exception as exc:
        logger.error("Nominatim geocoding failed: %s", exc)
        return None


# ── Fallback simulated city database ─────────────────────────────
_CITY_DATA = {
    "chennai": {"lat": 13.0827, "lon": 80.2707, "district": "Chennai", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "coimbatore": {"lat": 11.0168, "lon": 76.9558, "district": "Coimbatore", "state": "Tamil Nadu", "country": "India", "climate_zone": "Composite"},
    "madurai": {"lat": 9.9252, "lon": 78.1198, "district": "Madurai", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "tirunelveli": {"lat": 8.7139, "lon": 77.7567, "district": "Tirunelveli", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "salem": {"lat": 11.6643, "lon": 78.1460, "district": "Salem", "state": "Tamil Nadu", "country": "India", "climate_zone": "Warm Humid"},
    "tiruchirappalli": {"lat": 10.7905, "lon": 78.7047, "district": "Tiruchirappalli", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "vellore": {"lat": 12.9165, "lon": 79.1325, "district": "Vellore", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "thanjavur": {"lat": 10.7870, "lon": 79.1378, "district": "Thanjavur", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "kanchipuram": {"lat": 12.8352, "lon": 79.7000, "district": "Kanchipuram", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "tiruvallur": {"lat": 13.1430, "lon": 79.9089, "district": "Tiruvallur", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "krishnagiri": {"lat": 12.5186, "lon": 78.2137, "district": "Krishnagiri", "state": "Tamil Nadu", "country": "India", "climate_zone": "Moderate"},
    "dharmapuri": {"lat": 12.1211, "lon": 78.1582, "district": "Dharmapuri", "state": "Tamil Nadu", "country": "India", "climate_zone": "Moderate"},
    "namakkal": {"lat": 11.2190, "lon": 78.1674, "district": "Namakkal", "state": "Tamil Nadu", "country": "India", "climate_zone": "Warm Humid"},
    "erode": {"lat": 11.3410, "lon": 77.7172, "district": "Erode", "state": "Tamil Nadu", "country": "India", "climate_zone": "Composite"},
    "karur": {"lat": 10.9601, "lon": 78.0766, "district": "Karur", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "dindigul": {"lat": 10.3624, "lon": 77.9700, "district": "Dindigul", "state": "Tamil Nadu", "country": "India", "climate_zone": "Composite"},
    "thoothukudi": {"lat": 8.7642, "lon": 78.1348, "district": "Thoothukudi", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "virudhunagar": {"lat": 9.5859, "lon": 77.9579, "district": "Virudhunagar", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "ramanathapuram": {"lat": 9.3645, "lon": 78.8390, "district": "Ramanathapuram", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "nagapattinam": {"lat": 10.7640, "lon": 79.8430, "district": "Nagapattinam", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "cuddalore": {"lat": 11.7463, "lon": 79.7680, "district": "Cuddalore", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "ariyalur": {"lat": 11.1400, "lon": 79.0780, "district": "Ariyalur", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "perambalur": {"lat": 11.2330, "lon": 78.8800, "district": "Perambalur", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "pudukkottai": {"lat": 10.3833, "lon": 78.8000, "district": "Pudukkottai", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "tiruppur": {"lat": 11.1085, "lon": 77.3411, "district": "Tiruppur", "state": "Tamil Nadu", "country": "India", "climate_zone": "Composite"},
    "nilgiris": {"lat": 11.4100, "lon": 76.6950, "district": "Nilgiris", "state": "Tamil Nadu", "country": "India", "climate_zone": "Temperate"},
    "kanyakumari": {"lat": 8.0883, "lon": 77.5385, "district": "Kanyakumari", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "tiruvannamalai": {"lat": 12.2253, "lon": 79.0747, "district": "Tiruvannamalai", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "villupuram": {"lat": 11.9390, "lon": 79.4924, "district": "Villupuram", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "tirupattur": {"lat": 12.4944, "lon": 78.5650, "district": "Tirupattur", "state": "Tamil Nadu", "country": "India", "climate_zone": "Moderate"},
    "ranipet": {"lat": 12.9400, "lon": 79.3300, "district": "Ranipet", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "kallakurichi": {"lat": 11.7400, "lon": 78.9600, "district": "Kallakurichi", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "tenkasi": {"lat": 8.9600, "lon": 77.3100, "district": "Tenkasi", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Semi-Arid"},
    "chengalpattu": {"lat": 12.6920, "lon": 79.9760, "district": "Chengalpattu", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"},
    "mayiladuthurai": {"lat": 11.1000, "lon": 79.6500, "district": "Mayiladuthurai", "state": "Tamil Nadu", "country": "India", "climate_zone": "Hot Humid"}
}

def _hash_seed(address: str) -> int:
    """Deterministic seed from address string."""
    return int(hashlib.md5(address.encode()).hexdigest()[:8], 16)


def _fallback_resolve(building_name: str, address: str) -> dict:
    """Resolve from hardcoded table or deterministic random (no API)."""
    key = address.strip().lower()

    for city_key, data in _CITY_DATA.items():
        if city_key in key:
            return {
                "agent": "LocationAgent",
                "status": "success",
                "source": "fallback_lookup",
                "building": building_name,
                "address": address,
                "formatted_address": f"{building_name}, {data['city']}, {data['state']}, {data['country']}",
                **data,
            }

    # Fully random fallback
    rng = random.Random(_hash_seed(address))
    lat = round(rng.uniform(8.0, 35.0), 4)
    lon = round(rng.uniform(68.0, 97.0), 4)
    return {
        "agent": "LocationAgent",
        "status": "success",
        "source": "fallback_random",
        "building": building_name,
        "address": address,
        "formatted_address": address.title(),
        "lat": lat,
        "lon": lon,
        "city": address.title(),
        "state": "Unknown",
        "country": "India",
        "climate_zone": _infer_climate_zone(lat, lon),
    }


# ── Public API (unchanged signature) ─────────────────────────────
async def resolve_location(building_name: str, address: str) -> dict:
    """
    Resolve a building address to lat/lon and climate metadata.

    Strategy
    --------
    1. Try Google Maps Geocoding API (if GOOGLE_MAPS_API_KEY is set).
    2. Fall back to hardcoded city table / deterministic random.

    Returns a dict with at minimum:
        agent, status, building, address, lat, lon, city, state, country, climate_zone
    """

    # ── Attempt real geocoding ────────────────────────────────────
    full_address = f"{building_name}, {address}" if building_name else address
    geo = await _geocode_google(full_address)

    if geo is not None:
        logger.info("Resolved '%s' via Google Maps → (%s, %s)", full_address, geo["lat"], geo["lon"])
        return {
            "agent": "LocationAgent",
            "status": "success",
            "source": "google_maps",
            "building": building_name,
            "address": address,
            "formatted_address": geo["formatted_address"],
            "lat": geo["lat"],
            "lon": geo["lon"],
            "city": geo["city"],
            "state": geo["state"],
            "country": geo["country"],
            "climate_zone": geo["climate_zone"],
        }
        
    # ── Attempt Nominatim fallback ────────────────────────────────
    geo_osm = await _geocode_nominatim(full_address)
    
    if geo_osm is None and not building_name:
        pass # Try again with just the address if building name failed
    elif geo_osm is None and building_name:
        geo_osm = await _geocode_nominatim(address) # fallback to just address
        
    if geo_osm is not None:
        logger.info("Resolved '%s' via OpenStreetMap → (%s, %s)", address, geo_osm["lat"], geo_osm["lon"])
        return {
            "agent": "LocationAgent",
            "status": "success",
            "source": "openstreetmap",
            "building": building_name,
            "address": address,
            "formatted_address": geo_osm["formatted_address"],
            "lat": geo_osm["lat"],
            "lon": geo_osm["lon"],
            "city": geo_osm["city"],
            "state": geo_osm["state"],
            "country": geo_osm["country"],
            "climate_zone": geo_osm["climate_zone"],
        }

    # ── Fallback ──────────────────────────────────────────────────
    logger.info("Falling back to simulated lookup for '%s'", address)
    return _fallback_resolve(building_name, address)
