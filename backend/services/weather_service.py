"""
Weather Service
Agniveer Sentinel - Weather Integration & Training Adjustment
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from core.config import settings


class WeatherService:
    """Weather service integration with OpenWeatherMap"""
    
    def __init__(self):
        self.api_key = settings.OPENWEATHERMAP_API_KEY
        self.base_url = settings.OPENWEATHERMAP_BASE_URL
    
    async def get_current_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """Get current weather for a city"""
        url = f"{self.base_url}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Weather API Error: {e}")
                return None
    
    async def get_forecast(self, city: str, days: int = 5) -> Optional[Dict[str, Any]]:
        """Get weather forecast"""
        url = f"{self.base_url}/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "cnt": days * 8  # 3-hour intervals
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Weather API Error: {e}")
                return None
    
    def check_training_conditions(
        self,
        temperature: float,
        humidity: float = 50,
        wind_speed: float = 0,
        rain_intensity: float = 0
    ) -> Dict[str, Any]:
        """Check if training conditions are safe"""
        
        recommendations = []
        is_safe = True
        training_modification = "normal"
        
        # Temperature checks
        if temperature > 40:
            recommendations.append("EXTREME HEAT: Cancel outdoor training")
            recommendations.append("Move all activities to indoor facilities")
            recommendations.append("Ensure adequate hydration breaks")
            is_safe = False
            training_modification = "indoor_only"
        elif temperature > 35:
            recommendations.append("HIGH TEMPERATURE: Reduce outdoor exposure time")
            recommendations.append("Increase hydration breaks")
            training_modification = "reduced_outdoor"
        elif temperature < 5:
            recommendations.append("COLD WEATHER: Extend warm-up periods")
            recommendations.append("Provide warm clothing during breaks")
            training_modification = "cold_weather"
        
        # Wind checks
        if wind_speed > 50:
            recommendations.append("HIGH WINDS: Cancel parachute/aviation training")
            recommendations.append("Avoid tall structure activities")
            is_safe = False
        elif wind_speed > 30:
            recommendations.append("MODERATE WINDS: Exercise caution during drills")
        
        # Rain checks
        if rain_intensity > 50:
            recommendations.append("HEAVY RAIN: Cancel field exercises")
            recommendations.append("Move to indoor training")
            is_safe = False
            training_modification = "indoor_only"
        elif rain_intensity > 10:
            recommendations.append("LIGHT RAIN: Provide rain gear")
            recommendations.append("Adjust running/drilling routes")
        
        # Humidity checks
        if humidity > 85:
            recommendations.append("HIGH HUMIDITY: Increase rest periods")
            recommendations.append("Monitor for heat exhaustion")
        
        return {
            "is_safe": is_safe,
            "training_modification": training_modification,
            "recommendations": recommendations,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "rain_intensity": rain_intensity,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def get_training_recommendation(self, location: str) -> Dict[str, Any]:
        """Get training recommendation based on weather"""
        
        weather_data = await self.get_current_weather(location)
        
        if not weather_data:
            return {
                "error": "Could not fetch weather data",
                "training_modification": "normal"
            }
        
        # Extract weather metrics
        main = weather_data.get("main", {})
        wind = weather_data.get("wind", {})
        weather = weather_data.get("weather", [{}])[0]
        
        temperature = main.get("temp", 20)
        humidity = main.get("humidity", 50)
        wind_speed = wind.get("speed", 0) * 3.6  # Convert m/s to km/h
        
        # Check conditions
        conditions = self.check_training_conditions(temperature, humidity, wind_speed)
        
        return {
            "location": location,
            "weather_condition": weather.get("description", "unknown"),
            "weather_icon": weather.get("icon"),
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "training_modification": conditions["training_modification"],
            "recommendations": conditions["recommendations"],
            "is_safe": conditions["is_safe"],
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def adjust_schedule(
        self,
        schedule: list,
        location: str
    ) -> Dict[str, Any]:
        """Adjust training schedule based on weather"""
        
        recommendation = await self.get_training_recommendation(location)
        
        if recommendation.get("error"):
            return {"error": recommendation["error"], "adjusted_schedule": schedule}
        
        modification = recommendation["training_modification"]
        adjusted_activities = []
        
        outdoor_activities = ["PT", "Running", "Drill", "Field Exercise", "Shooting"]
        indoor_activities = ["Classroom", "Weapon Maintenance", "Strategy", "Medical", "Admin"]
        
        for activity in schedule:
            activity_name = activity.get("activity", "").upper()
            
            if modification == "indoor_only":
                # Replace outdoor with indoor
                if activity_name in outdoor_activities:
                    # Find replacement
                    replacement = "Indoor Training / Class"
                    adjusted_activities.append({
                        **activity,
                        "original_activity": activity.get("activity"),
                        "activity": replacement,
                        "location": "Indoor Hall",
                        "adjusted": True,
                        "reason": "Weather: Extreme conditions"
                    })
                    continue
            
            elif modification == "reduced_outdoor":
                # Reduce duration for outdoor
                if activity_name in outdoor_activities:
                    adjusted_activities.append({
                        **activity,
                        "duration_adjusted": True,
                        "original_duration": activity.get("duration"),
                        "adjusted_duration": "45 min",
                        "adjusted": True,
                        "reason": "Weather: High temperature"
                    })
                    continue
            
            adjusted_activities.append(activity)
        
        return {
            "original_schedule": schedule,
            "adjusted_schedule": adjusted_activities,
            "weather_recommendation": recommendation,
            "adjustment_reason": modification
        }


# Singleton instance
weather_service = WeatherService()



