"""
🌤️ WEATHER TOOL
Fetches weather from OpenWeatherMap API
FREE tier: 1000 calls/day
"""

import os
import aiohttp
from typing import Dict, Any, Optional
from utils.logger import logger


class WeatherTool:
    """
    🌤️ Weather Tool using OpenWeatherMap API
    
    Requires: OPENWEATHER_API_KEY in .env
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("⚠️ OPENWEATHER_API_KEY not set, using mock data")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current weather for a city
        
        Args:
            params: {"city": "Tokyo"}
        
        Returns:
            {
                "city": "Tokyo",
                "country": "JP",
                "temperature": "25°C",
                "description": "clear sky",
                ...
            }
        """
        city = params.get("city", "London")
        
        logger.info(f"🌤️ Weather: Fetching for '{city}'")
        
        # If no API key, return mock data
        if not self.api_key:
            return self._get_mock_weather(city)
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10)
                )
            
            url = f"{self.BASE_URL}/weather"
            params_api = {
                "q": city,
                "appid": self.api_key,
                "units": "metric"
            }
            
            async with self.session.get(url, params=params_api) as response:
                if response.status == 401:
                    logger.warning("⚠️ Invalid weather API key, using mock")
                    return self._get_mock_weather(city)
                
                if response.status == 404:
                    logger.warning(f"⚠️ City not found: {city}")
                    return {
                        "city": city,
                        "error": "City not found",
                        "temperature": "N/A"
                    }
                
                if response.status != 200:
                    logger.error(f"❌ Weather API error: {response.status}")
                    return self._get_mock_weather(city)
                
                data = await response.json()
                
                weather = {
                    "city": data.get("name", city),
                    "country": data.get("sys", {}).get("country", ""),
                    "temperature": f"{round(data.get('main', {}).get('temp', 0))}°C",
                    "feels_like": f"{round(data.get('main', {}).get('feels_like', 0))}°C",
                    "description": data.get("weather", [{}])[0].get("description", ""),
                    "humidity": f"{data.get('main', {}).get('humidity', 0)}%",
                    "wind_speed": f"{data.get('wind', {}).get('speed', 0)} m/s",
                    "clouds": f"{data.get('clouds', {}).get('all', 0)}%",
                    "pressure": f"{data.get('main', {}).get('pressure', 0)} hPa",
                    "icon": data.get("weather", [{}])[0].get("icon", "01d"),
                    "timestamp": data.get("dt", 0)
                }
                
                logger.info(f"✅ Weather: {weather['city']} - {weather['temperature']}")
                
                return weather
        
        except Exception as e:
            logger.error(f"❌ Weather error: {e}")
            return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """Return mock weather data for testing"""
        logger.info(f"📋 Using mock weather for {city}")
        
        return {
            "city": city,
            "country": "XX",
            "temperature": "22°C",
            "feels_like": "20°C",
            "description": "partly cloudy",
            "humidity": "65%",
            "wind_speed": "5 m/s",
            "clouds": "40%",
            "pressure": "1013 hPa",
            "icon": "02d",
            "is_mock": True
        }
    
    async def get_forecast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather forecast (5 days)"""
        # For now, return current weather
        return await self.get_weather(params)


# Singleton instance
_weather_tool: Optional[WeatherTool] = None

async def get_weather_tool() -> WeatherTool:
    global _weather_tool
    if _weather_tool is None:
        _weather_tool = WeatherTool()
        await _weather_tool.__aenter__()
    return _weather_tool