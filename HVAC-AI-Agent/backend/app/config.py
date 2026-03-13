import os

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHER_API_KEY = OPENWEATHER_API_KEY or "demo_key"
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

IDEAL_IKW_TR = 0.9          
MAX_ACCEPTABLE_IKW_TR = 1.2  
COMFORT_TEMP_MIN = 22 
COMFORT_TEMP_MAX = 26 
DEFAULT_COP = 3.5            

APP_TITLE = "HVAC AI Agent – Autonomous Energy Optimization System"
VERSION = "1.0.0"
DEBUG = True
