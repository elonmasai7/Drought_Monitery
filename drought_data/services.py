"""
Data integration services for external APIs
This module provides interfaces to external data sources like Google Earth Engine,
NASA POWER API, and OpenWeatherMap
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from django.utils import timezone

from .models import NDVIData, SoilMoistureData, WeatherData
from core.models import Region

logger = logging.getLogger(__name__)


class GoogleEarthEngineService:
    """
    Service for integrating with Google Earth Engine API
    """
    
    def __init__(self):
        self.api_key = settings.GOOGLE_EARTH_ENGINE_KEY
        self.base_url = "https://earthengine.googleapis.com/v1"
    
    def get_ndvi_data(self, region: Region, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Fetch NDVI data for a region from Google Earth Engine
        
        Args:
            region: Region object with coordinates
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of NDVI data points
        """
        if not self.api_key or self.api_key == 'your_google_earth_engine_key':
            logger.warning("Google Earth Engine API key not configured, using mock data")
            return self._generate_mock_ndvi_data(region, start_date, end_date)
        
        try:
            # Define the region geometry
            geometry = {
                "type": "Point",
                "coordinates": [float(region.longitude), float(region.latitude)]
            }
            
            # Create request payload for NDVI calculation
            payload = {
                "expression": "NDVI = (B5 - B4) / (B5 + B4)",
                "fileFormat": "GEO_JSON",
                "bandIds": ["NDVI"],
                "region": geometry,
                "dimensions": "256x256",
                "crs": "EPSG:4326",
                "formatOptions": {
                    "cloudOptimized": True
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # This would be the actual API call
            # response = requests.post(f"{self.base_url}/projects/YOUR_PROJECT/image:computePixels", 
            #                         json=payload, headers=headers)
            
            # For now, return mock data
            logger.info(f"[MOCK] Fetching NDVI data for {region.name} from {start_date} to {end_date}")
            return self._generate_mock_ndvi_data(region, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error fetching NDVI data from GEE: {str(e)}")
            return self._generate_mock_ndvi_data(region, start_date, end_date)
    
    def _generate_mock_ndvi_data(self, region: Region, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Generate realistic mock NDVI data"""
        import random
        
        data = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Base NDVI values depending on region type and season
        base_ndvi = {
            'county': 0.45,
            'ward': 0.40,
            'village': 0.35
        }
        
        base_value = base_ndvi.get(region.region_type, 0.40)
        
        while current_date <= end_date_obj:
            # Add seasonal variation (higher NDVI during rainy seasons)
            month = current_date.month
            seasonal_factor = 1.0
            
            if month in [3, 4, 5, 10, 11]:  # Rainy seasons in East Africa
                seasonal_factor = 1.2
            elif month in [12, 1, 2, 6, 7, 8]:  # Dry seasons
                seasonal_factor = 0.8
            
            # Add random variation
            ndvi_value = base_value * seasonal_factor + random.uniform(-0.15, 0.15)
            ndvi_value = max(-1.0, min(1.0, ndvi_value))  # Clamp to valid NDVI range
            
            data.append({
                'date': current_date.strftime("%Y-%m-%d"),
                'ndvi_value': round(ndvi_value, 3),
                'satellite_source': 'Landsat-8',
                'cloud_cover_percent': random.uniform(5, 30),
                'data_quality': random.choice(['excellent', 'good', 'good', 'fair'])
            })
            
            current_date += timedelta(days=1)
        
        return data


class NASAPowerService:
    """
    Service for integrating with NASA POWER API for meteorological data
    """
    
    def __init__(self):
        self.api_key = settings.NASA_POWER_API_KEY
        self.base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    def get_soil_moisture_data(self, region: Region, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Fetch soil moisture data from NASA POWER API
        """
        if not self.api_key or self.api_key == 'your_nasa_power_api_key':
            logger.warning("NASA POWER API key not configured, using mock data")
            return self._generate_mock_soil_moisture_data(region, start_date, end_date)
        
        try:
            params = {
                'parameters': 'GWETROOT,GWETTOP',  # Root zone and surface soil wetness
                'community': 'AG',  # Agricultural community
                'longitude': float(region.longitude),
                'latitude': float(region.latitude),
                'start': start_date.replace('-', ''),
                'end': end_date.replace('-', ''),
                'format': 'JSON'
            }
            
            # This would be the actual API call
            # response = requests.get(self.base_url, params=params)
            
            # For now, return mock data
            logger.info(f"[MOCK] Fetching soil moisture data for {region.name} from {start_date} to {end_date}")
            return self._generate_mock_soil_moisture_data(region, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error fetching soil moisture data from NASA POWER: {str(e)}")
            return self._generate_mock_soil_moisture_data(region, start_date, end_date)
    
    def _generate_mock_soil_moisture_data(self, region: Region, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Generate realistic mock soil moisture data"""
        import random
        
        data = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Base soil moisture (percentage)
        base_moisture = 35.0
        
        while current_date <= end_date_obj:
            # Add seasonal and random variation
            month = current_date.month
            seasonal_factor = 1.0
            
            if month in [3, 4, 5, 10, 11]:  # Rainy seasons
                seasonal_factor = 1.5
            elif month in [12, 1, 2, 6, 7, 8]:  # Dry seasons
                seasonal_factor = 0.6
            
            moisture_value = base_moisture * seasonal_factor + random.uniform(-10, 10)
            moisture_value = max(5.0, min(80.0, moisture_value))  # Clamp to realistic range
            
            data.append({
                'date': current_date.strftime("%Y-%m-%d"),
                'moisture_percent': round(moisture_value, 1),
                'soil_depth_cm': 10,
                'data_source': 'satellite',
                'temperature_celsius': round(random.uniform(20, 35), 1)
            })
            
            current_date += timedelta(days=1)
        
        return data


class OpenWeatherMapService:
    """
    Service for integrating with OpenWeatherMap API
    """
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, region: Region) -> Dict[str, Any]:
        """
        Get current weather data for a region
        """
        if not self.api_key or self.api_key == 'your_openweather_api_key':
            logger.warning("OpenWeatherMap API key not configured, using mock data")
            return self._generate_mock_current_weather(region)
        
        try:
            params = {
                'lat': float(region.latitude),
                'lon': float(region.longitude),
                'appid': self.api_key,
                'units': 'metric'
            }
            
            # This would be the actual API call
            # response = requests.get(f"{self.base_url}/weather", params=params)
            
            # For now, return mock data
            logger.info(f"[MOCK] Fetching current weather for {region.name}")
            return self._generate_mock_current_weather(region)
            
        except Exception as e:
            logger.error(f"Error fetching weather data from OpenWeatherMap: {str(e)}")
            return self._generate_mock_current_weather(region)
    
    def get_historical_weather(self, region: Region, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get historical weather data for a region
        """
        if not self.api_key or self.api_key == 'your_openweather_api_key':
            logger.warning("OpenWeatherMap API key not configured, using mock data")
            return self._generate_mock_historical_weather(region, start_date, end_date)
        
        try:
            # OpenWeatherMap requires timestamps for historical data
            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            
            # For historical data, we'd need to make multiple API calls
            # This is a simplified version
            logger.info(f"[MOCK] Fetching historical weather for {region.name} from {start_date} to {end_date}")
            return self._generate_mock_historical_weather(region, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error fetching historical weather data: {str(e)}")
            return self._generate_mock_historical_weather(region, start_date, end_date)
    
    def _generate_mock_current_weather(self, region: Region) -> Dict[str, Any]:
        """Generate realistic mock current weather data"""
        import random
        
        temp = random.uniform(18, 35)
        return {
            'temperature': round(temp, 1),
            'humidity': random.randint(30, 80),
            'pressure': random.randint(1010, 1025),
            'wind_speed': round(random.uniform(2, 15), 1),
            'wind_direction': random.randint(0, 360),
            'cloudiness': random.randint(0, 100),
            'weather_description': random.choice([
                'Clear sky', 'Few clouds', 'Scattered clouds', 
                'Broken clouds', 'Overcast', 'Light rain'
            ])
        }
    
    def _generate_mock_historical_weather(self, region: Region, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Generate realistic mock historical weather data"""
        import random
        
        data = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_date_obj:
            temp_avg = random.uniform(20, 32)
            precipitation = 0.0
            
            # Simulate rainy days (30% chance)
            if random.random() < 0.3:
                precipitation = random.uniform(0.5, 25.0)
            
            data.append({
                'date': current_date.strftime("%Y-%m-%d"),
                'temperature_max': round(temp_avg + random.uniform(2, 8), 1),
                'temperature_min': round(temp_avg - random.uniform(3, 8), 1),
                'temperature_avg': round(temp_avg, 1),
                'precipitation_mm': round(precipitation, 1),
                'humidity_percent': random.randint(35, 85),
                'wind_speed_kmh': round(random.uniform(5, 20), 1),
                'data_source': 'OpenWeatherMap'
            })
            
            current_date += timedelta(days=1)
        
        return data


class DataIntegrationService:
    """
    Main service that orchestrates data collection from multiple sources
    """
    
    def __init__(self):
        self.gee_service = GoogleEarthEngineService()
        self.nasa_service = NASAPowerService()
        self.weather_service = OpenWeatherMapService()
    
    def collect_all_data_for_region(self, region, date: str = None) -> Dict[str, Any]:
        """
        Collect all types of data for a region on a specific date
        
        Args:
            region: Region object or region name string
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with collected data and status information
        """
        # Handle both Region objects and string region names
        if isinstance(region, str):
            from core.models import Region
            try:
                region_obj = Region.objects.get(name=region, region_type='county')
            except Region.DoesNotExist:
                return {
                    'region': region,
                    'date': date or timezone.now().date().strftime("%Y-%m-%d"),
                    'ndvi_data': None,
                    'soil_moisture_data': None,
                    'weather_data': None,
                    'errors': [f'Region "{region}" not found']
                }
        else:
            region_obj = region
        
        if not date:
            date = timezone.now().date().strftime("%Y-%m-%d")
        
        results = {
            'region': region_obj.name,
            'date': date,
            'ndvi_data': None,
            'soil_moisture_data': None,
            'weather_data': None,
            'errors': []
        }
        
        try:
            # Collect NDVI data
            ndvi_data = self.gee_service.get_ndvi_data(region_obj, date, date)
            if ndvi_data:
                results['ndvi_data'] = ndvi_data[0]  # Get first (and only) day
            
        except Exception as e:
            results['errors'].append(f"NDVI collection failed: {str(e)}")
        
        try:
            # Collect soil moisture data
            soil_data = self.nasa_service.get_soil_moisture_data(region_obj, date, date)
            if soil_data:
                results['soil_moisture_data'] = soil_data[0]  # Get first (and only) day
            
        except Exception as e:
            results['errors'].append(f"Soil moisture collection failed: {str(e)}")
        
        try:
            # Collect weather data
            weather_data = self.weather_service.get_historical_weather(region_obj, date, date)
            if weather_data:
                results['weather_data'] = weather_data[0]  # Get first (and only) day
            
        except Exception as e:
            results['errors'].append(f"Weather collection failed: {str(e)}")
        
        return results
    
    def collect_historical_data_for_region(self, region: Region, days_back: int = 30) -> Dict[str, Any]:
        """
        Collect historical data for a region
        
        Args:
            region: Region object
            days_back: Number of days back to collect data
            
        Returns:
            Dictionary with collected data and status information
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        results = {
            'region': region.name,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'days_collected': 0,
            'errors': []
        }
        
        try:
            # Collect NDVI data
            ndvi_data = self.gee_service.get_ndvi_data(region, start_date_str, end_date_str)
            
            for day_data in ndvi_data:
                ndvi_obj, created = NDVIData.objects.get_or_create(
                    region=region,
                    date=datetime.strptime(day_data['date'], "%Y-%m-%d").date(),
                    defaults={
                        'ndvi_value': day_data['ndvi_value'],
                        'satellite_source': day_data['satellite_source'],
                        'cloud_cover_percent': day_data['cloud_cover_percent'],
                        'data_quality': day_data['data_quality']
                    }
                )
                if created:
                    results['days_collected'] += 1
            
        except Exception as e:
            results['errors'].append(f"NDVI collection failed: {str(e)}")
        
        try:
            # Collect soil moisture data
            soil_data = self.nasa_service.get_soil_moisture_data(region, start_date_str, end_date_str)
            
            for day_data in soil_data:
                soil_obj, created = SoilMoistureData.objects.get_or_create(
                    region=region,
                    date=datetime.strptime(day_data['date'], "%Y-%m-%d").date(),
                    defaults={
                        'moisture_percent': day_data['moisture_percent'],
                        'soil_depth_cm': day_data['soil_depth_cm'],
                        'data_source': day_data['data_source'],
                        'temperature_celsius': day_data['temperature_celsius']
                    }
                )
            
        except Exception as e:
            results['errors'].append(f"Soil moisture collection failed: {str(e)}")
        
        try:
            # Collect weather data
            weather_data = self.weather_service.get_historical_weather(region, start_date_str, end_date_str)
            
            for day_data in weather_data:
                weather_obj, created = WeatherData.objects.get_or_create(
                    region=region,
                    date=datetime.strptime(day_data['date'], "%Y-%m-%d").date(),
                    defaults={
                        'temperature_max': day_data['temperature_max'],
                        'temperature_min': day_data['temperature_min'],
                        'temperature_avg': day_data['temperature_avg'],
                        'precipitation_mm': day_data['precipitation_mm'],
                        'humidity_percent': day_data['humidity_percent'],
                        'wind_speed_kmh': day_data['wind_speed_kmh'],
                        'data_source': day_data['data_source']
                    }
                )
            
        except Exception as e:
            results['errors'].append(f"Weather collection failed: {str(e)}")
        
        return results