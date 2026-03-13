
# Weather Agent
#etches or simulates real-time outdoor weather conditions for a location.

import random
import hashlib


import logging
import httpx
from app.config import WEATHER_API_KEY, WEATHER_API_URL

logger = logging.getLogger("WeatherAgent")

def _hash_seed(lat: float, lon: float) -> int:
    raw = f"{lat:.4f},{lon:.4f}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


# Climate-zone → typical ranges (for simulation fallback)
_CLIMATE_PROFILES = {
    "Warm Humid":  {"temp": (28, 38), "humidity": (60, 85), "wind": (5, 18)},
    "Hot Humid":   {"temp": (30, 42), "humidity": (55, 80), "wind": (6, 20)},
    "Hot Dry":     {"temp": (32, 45), "humidity": (15, 40), "wind": (8, 25)},
    "Composite":   {"temp": (25, 44), "humidity": (30, 70), "wind": (5, 20)},
    "Moderate":    {"temp": (20, 32), "humidity": (50, 75), "wind": (4, 15)},
    "Mixed Humid": {"temp": (18, 35), "humidity": (45, 75), "wind": (5, 18)},
    "Temperate":   {"temp": (10, 25), "humidity": (55, 80), "wind": (6, 22)},
}

async def _fetch_real_weather(lat: float, lon: float) -> dict | None:
    """Fetch real weather from OpenWeatherMap."""
    if not WEATHER_API_KEY or WEATHER_API_KEY == "demo_key":
        return None

    params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(WEATHER_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        return {
            "outdoor_temp_c": round(data["main"]["temp"], 1),
            "humidity_pct": data["main"]["humidity"],
            "wind_speed_kmh": round(data["wind"]["speed"] * 3.6, 1), # m/s to km/h
            "feels_like_c": round(data["main"]["feels_like"], 1),
            "condition": data["weather"][0]["description"].title(),
            "source": "openweather_api"
        }
    except Exception as e:
        logger.error(f"Error fetching real weather: {e}")
        return None

async def _fetch_open_meteo(lat: float, lon: float) -> dict | None:
    """Fallback weather using Open-Meteo (Free, no API key)."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,apparent_temperature,weather_code"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
        current = data.get("current", {})
        if not current:
            return None
            
        return {
            "outdoor_temp_c": round(current.get("temperature_2m", 25.0), 1),
            "humidity_pct": current.get("relative_humidity_2m", 50.0),
            "wind_speed_kmh": round(current.get("wind_speed_10m", 10.0), 1),
            "feels_like_c": round(current.get("apparent_temperature", 25.0), 1),
            "condition": "Dynamic Condition", # Simplified
            "source": "open_meteo_api"
        }
    except Exception as e:
        logger.error(f"Error fetching open-meteo: {e}")
        return None

async def fetch_weather(lat: float, lon: float, climate_zone: str = "Warm Humid") -> dict:
    """
    Attempts real API call, then open-meteo fallback, then local simulation.
    """
    # 1. Try real OpenWeatherMap API
    real_data = await _fetch_real_weather(lat, lon)
    if real_data:
        return {
            "agent": "WeatherAgent",
            "status": "success",
            **real_data,
            "climate_zone": climate_zone,
        }

    # 2. Try Open-Meteo (Free, No API Key)
    om_data = await _fetch_open_meteo(lat, lon)
    if om_data:
        logger.info(f"Resolved weather via Open-Meteo for {lat}, {lon}")
        return {
            "agent": "WeatherAgent",
            "status": "success",
            **om_data,
            "climate_zone": climate_zone,
        }

    # 3. Fallback to simulation
    logger.info(f"Falling back to simulated weather for {lat}, {lon}")
    profile = _CLIMATE_PROFILES.get(climate_zone, _CLIMATE_PROFILES["Warm Humid"])
    rng = random.Random(_hash_seed(lat, lon))

    temp = round(rng.uniform(*profile["temp"]), 1)
    humidity = round(rng.uniform(*profile["humidity"]), 1)
    wind_speed = round(rng.uniform(*profile["wind"]), 1)

    # Derive related values
    feels_like = round(temp + (humidity - 50) * 0.05, 1)
    uv_index = round(rng.uniform(3, 11), 1)
    condition = rng.choice(["Clear Sky", "Partly Cloudy", "Sunny", "Hazy", "Overcast"])

    return {
        "agent": "WeatherAgent",
        "status": "success",
        "outdoor_temp_c": temp,
        "humidity_pct": humidity,
        "wind_speed_kmh": wind_speed,
        "feels_like_c": feels_like,
        "uv_index": uv_index,
        "condition": condition,
        "climate_zone": climate_zone,
        "source": "simulation"
    }
