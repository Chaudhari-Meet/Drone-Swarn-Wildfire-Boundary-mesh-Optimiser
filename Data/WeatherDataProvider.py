"""
WeatherDataProvider - Supplies real and simulated weather data for wildfire analysis.

Provides wind speed/direction, temperature, humidity, and other meteorological data
that influences fire behavior and spread prediction.

Can use real APIs (OpenWeather, NOAA) or provide simulated data for testing.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

import numpy as np
import requests

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather observation at a specific location and time."""
    timestamp: datetime
    latitude: float
    longitude: float
    wind_speed_ms: float  # m/s
    wind_direction_deg: float  # 0-360 degrees
    temperature_c: float  # Celsius
    humidity_percent: float  # 0-100
    pressure_hpa: float  # hectopascals
    precipitation_mm: float  # mm last hour
    
    # Fire-relevant derived metrics
    @property
    def fire_danger_index(self) -> float:
        """
        Simple fire danger index (0-100).
        Based on temperature, humidity, and wind speed.
        Higher = more dangerous.
        """
        # Normalize inputs
        temp_factor = min(100, max(0, (self.temperature_c - 10) / 30 * 100))  # 10-40C range
        humidity_factor = min(100, max(0, (100 - self.humidity_percent) / 50 * 100))  # Lower humidity = higher danger
        wind_factor = min(100, max(0, self.wind_speed_ms / 20 * 100))  # 0-20 m/s range
        
        # Weighted average
        danger = (temp_factor * 0.4 + humidity_factor * 0.4 + wind_factor * 0.2)
        return danger
    
    @property
    def is_favorable_for_spread(self) -> bool:
        """Check if conditions favor fire spread."""
        return (self.temperature_c > 25 and
                self.humidity_percent < 40 and
                self.wind_speed_ms > 5)


class WeatherDataProvider:
    """
    Weather data provider with support for real APIs and simulation.
    
    Modes:
    - "real": Fetch from OpenWeather API
    - "noaa": Fetch from NOAA API
    - "simulated": Generate synthetic but realistic weather data
    - "cached": Use locally cached weather data
    """
    
    def __init__(self, mode: str = "simulated", api_key: Optional[str] = None):
        """
        Initialize weather provider.
        
        Args:
            mode: Data source mode (real, noaa, simulated, cached)
            api_key: API key for real data sources
        """
        self.mode = mode
        self.api_key = api_key or os.environ.get("OPENWEATHER_API_KEY")
        
        # API endpoints
        self.openweather_url = "https://api.openweathermap.org/data/2.5/weather"
        self.noaa_points_url = "https://api.weather.gov/points"
        self.noaa_forecast_url = None  # Set after getting grid points
        
        self.weather_cache = {}
        self.last_fetch_time = None
        
        logger.info(f"WeatherDataProvider initialized in {mode} mode")
    
    def get_weather(self, latitude: float, longitude: float,
                   timestamp: Optional[datetime] = None) -> Optional[WeatherData]:
        """
        Get weather data for a location and time.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            timestamp: Timestamp (defaults to now)
        
        Returns:
            WeatherData object or None if fetch fails
        """
        timestamp = timestamp or datetime.now()
        
        try:
            if self.mode == "real":
                return self._fetch_from_openweather(latitude, longitude)
            elif self.mode == "noaa":
                return self._fetch_from_noaa(latitude, longitude)
            elif self.mode == "simulated":
                return self._generate_simulated_weather(latitude, longitude, timestamp)
            elif self.mode == "cached":
                return self._get_cached_weather(latitude, longitude, timestamp)
            else:
                logger.error(f"Unknown weather mode: {self.mode}")
                return None
        except Exception as e:
            logger.error(f"Failed to get weather for ({latitude}, {longitude}): {e}")
            return None
    
    def get_weather_forecast(self, latitude: float, longitude: float,
                            hours: int = 24) -> List[WeatherData]:
        """
        Get weather forecast for multiple hours ahead.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            hours: Number of hours to forecast (1-120)
        
        Returns:
            List of WeatherData objects
        """
        forecast = []
        
        if self.mode == "simulated":
            # Generate simulated forecast
            now = datetime.now()
            for h in range(0, hours, 3):  # 3-hour intervals
                timestamp = now + timedelta(hours=h)
                weather = self._generate_simulated_weather(latitude, longitude, timestamp)
                if weather:
                    forecast.append(weather)
        else:
            logger.warning(f"Forecast not implemented for mode: {self.mode}")
        
        return forecast
    
    def _fetch_from_openweather(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """
        Fetch weather from OpenWeather API (requires API key).
        
        Free tier: 1000 calls/day, 60 calls/minute
        """
        if not self.api_key:
            logger.warning("No OpenWeather API key configured")
            return None
        
        try:
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"  # Celsius
            }
            
            response = requests.get(self.openweather_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            weather = WeatherData(
                timestamp=datetime.fromtimestamp(data["dt"]),
                latitude=latitude,
                longitude=longitude,
                wind_speed_ms=data["wind"]["speed"],
                wind_direction_deg=data["wind"].get("deg", 0),
                temperature_c=data["main"]["temp"],
                humidity_percent=data["main"]["humidity"],
                pressure_hpa=data["main"]["pressure"],
                precipitation_mm=data.get("rain", {}).get("1h", 0)
            )
            
            self.last_fetch_time = datetime.now()
            logger.info(f"Fetched OpenWeather: {temperature_c:.1f}C, {wind_speed_ms:.1f} m/s wind")
            return weather
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeather API error: {e}")
            return None
    
    def _fetch_from_noaa(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """
        Fetch weather from NOAA API (US/territories only, free, no key required).
        """
        try:
            # First get grid point
            points_response = requests.get(f"{self.noaa_points_url}/{latitude},{longitude}", timeout=10)
            points_response.raise_for_status()
            points_data = points_response.json()
            
            # Get forecast URL
            forecast_url = points_data["properties"]["forecast"]
            
            # Fetch forecast
            forecast_response = requests.get(forecast_url, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Use first period
            period = forecast_data["properties"]["periods"][0]
            
            # Parse wind direction string (e.g., "NW", "SW 10 mph")
            wind_parts = period["windDirection"].split()
            wind_dir_map = {
                "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
                "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
                "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
                "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5
            }
            wind_direction_deg = wind_dir_map.get(wind_parts[0], 0)
            
            # Parse wind speed (e.g., "10 mph")
            wind_speed_mph = float(period["windSpeed"].split()[0])
            wind_speed_ms = wind_speed_mph * 0.44704  # mph to m/s
            
            # Extract temperature
            temperature_c = period["temperature"]
            if period["temperatureUnit"] == "F":
                temperature_c = (temperature_c - 32) * 5/9
            
            # Estimate humidity from short forecast
            humidity_percent = self._estimate_humidity_from_forecast(period["shortForecast"])
            
            weather = WeatherData(
                timestamp=datetime.now(),
                latitude=latitude,
                longitude=longitude,
                wind_speed_ms=wind_speed_ms,
                wind_direction_deg=wind_direction_deg,
                temperature_c=temperature_c,
                humidity_percent=humidity_percent,
                pressure_hpa=1013,  # Standard, not provided by NOAA
                precipitation_mm=0  # Not in brief forecast
            )
            
            logger.info(f"Fetched NOAA: {temperature_c:.1f}C, {wind_speed_ms:.1f} m/s wind")
            return weather
            
        except Exception as e:
            logger.error(f"NOAA API error: {e}")
            return None
    
    def _estimate_humidity_from_forecast(self, forecast_text: str) -> float:
        """
        Estimate humidity from short forecast text.
        
        Args:
            forecast_text: Short forecast description
        
        Returns:
            Estimated humidity 0-100
        """
        forecast_lower = forecast_text.lower()
        
        # Dry conditions
        if any(word in forecast_lower for word in ["dry", "clear", "sunny"]):
            return np.random.uniform(20, 40)
        
        # Moderate conditions
        elif any(word in forecast_lower for word in ["partly", "mostly", "scattered"]):
            return np.random.uniform(40, 60)
        
        # Wet conditions
        elif any(word in forecast_lower for word in ["rain", "wet", "cloudy", "overcast"]):
            return np.random.uniform(60, 85)
        
        else:
            return 50.0  # Default
    
    def _generate_simulated_weather(self, latitude: float, longitude: float,
                                   timestamp: datetime) -> WeatherData:
        """
        Generate realistic simulated weather data.
        
        Uses latitude and time of day to create plausible variations.
        """
        # Time-based variation (diurnal cycle)
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        
        # Temperature varies with time of day and latitude
        # Hottest at 14:00 (2 PM), coldest at 5:00 (5 AM)
        base_temp = 25 - abs(latitude) * 0.5  # Hotter near equator
        temp_cycle = 15 * np.sin((hour - 5) * np.pi / 12)  # ±15C swing
        temperature_c = base_temp + temp_cycle + np.random.normal(0, 2)
        
        # Humidity inversely correlated with temperature
        base_humidity = 60 - abs(latitude) * 0.3
        humidity_cycle = -20 * np.sin((hour - 5) * np.pi / 12)  # Humidity drops when hot
        humidity_percent = np.clip(base_humidity + humidity_cycle + np.random.normal(0, 5), 10, 95)
        
        # Wind direction varies slowly with day
        wind_direction_base = (day_of_year * 360 / 365 + latitude * 2) % 360
        wind_direction_deg = (wind_direction_base + np.random.normal(0, 20)) % 360
        
        # Wind speed peaks in afternoon, varies with location
        wind_base = 5 + abs(latitude) * 0.1  # Higher at poles (simplified)
        wind_cycle = 3 * np.sin((hour - 6) * np.pi / 12)  # Peaks at noon
        wind_speed_ms = np.clip(wind_base + wind_cycle + np.random.exponential(1), 0, 25)
        
        # Pressure (fairly constant, slight variations)
        pressure_hpa = 1013 + np.random.normal(0, 5)
        
        # Precipitation (random events)
        precipitation_mm = 0
        if np.random.random() < 0.1:  # 10% chance of precipitation
            precipitation_mm = np.random.exponential(2)  # Typical rainfall
        
        weather = WeatherData(
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            wind_speed_ms=wind_speed_ms,
            wind_direction_deg=wind_direction_deg,
            temperature_c=temperature_c,
            humidity_percent=humidity_percent,
            pressure_hpa=pressure_hpa,
            precipitation_mm=precipitation_mm
        )
        
        return weather
    
    def _get_cached_weather(self, latitude: float, longitude: float,
                           timestamp: datetime) -> Optional[WeatherData]:
        """Get weather from local cache."""
        cache_key = f"{latitude:.2f},{longitude:.2f}"
        
        if cache_key in self.weather_cache:
            cached_data, cached_time = self.weather_cache[cache_key]
            
            # Use cache if less than 1 hour old
            if (datetime.now() - cached_time).total_seconds() < 3600:
                logger.info(f"Using cached weather for {cache_key}")
                return cached_data
        
        # Fall back to simulated
        logger.debug(f"Cache miss for {cache_key}, generating simulated data")
        weather = self._generate_simulated_weather(latitude, longitude, timestamp)
        
        if weather:
            self.weather_cache[cache_key] = (weather, datetime.now())
        
        return weather
    
    def cache_weather(self, weather: WeatherData):
        """Add weather data to cache."""
        cache_key = f"{weather.latitude:.2f},{weather.longitude:.2f}"
        self.weather_cache[cache_key] = (weather, datetime.now())
    
    def get_weather_summary(self, latitude: float, longitude: float,
                           hours: int = 24) -> Dict:
        """
        Get weather summary for a region.
        
        Returns:
            Dictionary with average/min/max values
        """
        forecast = self.get_weather_forecast(latitude, longitude, hours)
        
        if not forecast:
            return {}
        
        temps = [w.temperature_c for w in forecast]
        winds = [w.wind_speed_ms for w in forecast]
        humidities = [w.humidity_percent for w in forecast]
        dangers = [w.fire_danger_index for w in forecast]
        
        return {
            "period_hours": hours,
            "samples": len(forecast),
            "temperature": {
                "min": min(temps),
                "max": max(temps),
                "avg": np.mean(temps)
            },
            "wind_speed": {
                "min": min(winds),
                "max": max(winds),
                "avg": np.mean(winds)
            },
            "humidity": {
                "min": min(humidities),
                "max": max(humidities),
                "avg": np.mean(humidities)
            },
            "fire_danger": {
                "min": min(dangers),
                "max": max(dangers),
                "avg": np.mean(dangers)
            },
            "favorable_periods": sum(1 for w in forecast if w.is_favorable_for_spread)
        }


# Singleton instance for easy access
_provider_instance = None


def get_weather_provider(mode: str = "simulated", api_key: Optional[str] = None) -> WeatherDataProvider:
    """
    Get or create weather provider instance.
    
    Args:
        mode: Data source mode
        api_key: API key for real data sources
    
    Returns:
        WeatherDataProvider instance
    """
    global _provider_instance
    
    if _provider_instance is None:
        _provider_instance = WeatherDataProvider(mode=mode, api_key=api_key)
    
    return _provider_instance
