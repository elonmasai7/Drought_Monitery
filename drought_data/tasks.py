from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import logging
import json
from typing import Optional, Dict, Any

from .models import NDVIData, SoilMoistureData, WeatherData, DroughtRiskAssessment
from core.models import Region
from django.conf import settings
from .services import DataIntegrationService
from .ml_models import DroughtEarlyWarningSystem

logger = logging.getLogger(__name__)


@shared_task
def fetch_ndvi_data_for_region(region_id: int, date_str: str = None) -> Dict[str, Any]:
    """
    Fetch NDVI data for a specific region
    This is a placeholder that would integrate with Google Earth Engine or other APIs
    """
    try:
        region = Region.objects.get(id=region_id)
        
        # Use provided date or today
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        # Check if data already exists
        existing = NDVIData.objects.filter(region=region, date=date).first()
        if existing:
            logger.info(f"NDVI data already exists for {region.name} on {date}")
            return {'status': 'exists', 'region': region.name, 'date': str(date)}
        
        # Use data integration service
        integration_service = DataIntegrationService()
        data_result = integration_service.collect_all_data_for_region(region, date_str or str(date))
        
        if data_result['ndvi_data']:
            ndvi_info = data_result['ndvi_data']
            ndvi_data = NDVIData.objects.create(
                region=region,
                date=date,
                ndvi_value=ndvi_info['ndvi_value'],
                satellite_source=ndvi_info['satellite_source'],
                cloud_cover_percent=ndvi_info['cloud_cover_percent'],
                data_quality=ndvi_info['data_quality']
            )
            mock_ndvi_value = ndvi_info['ndvi_value']
        else:
            # Fallback to mock data
            mock_ndvi_value = _generate_mock_ndvi_value(region)
            ndvi_data = NDVIData.objects.create(
                region=region,
                date=date,
                ndvi_value=mock_ndvi_value,
                satellite_source='Landsat-8',
                cloud_cover_percent=15.0,
                data_quality='good'
            )
        
        logger.info(f"Created NDVI data for {region.name}: {mock_ndvi_value}")
        return {
            'status': 'created',
            'region': region.name,
            'date': str(date),
            'ndvi_value': mock_ndvi_value
        }
        
    except Region.DoesNotExist:
        logger.error(f"Region with ID {region_id} not found")
        return {'status': 'error', 'message': 'Region not found'}
    except Exception as e:
        logger.error(f"Error fetching NDVI data: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def fetch_soil_moisture_data_for_region(region_id: int, date_str: str = None) -> Dict[str, Any]:
    """
    Fetch soil moisture data for a specific region
    This is a placeholder that would integrate with NASA POWER API or similar
    """
    try:
        region = Region.objects.get(id=region_id)
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        # Check if data already exists
        existing = SoilMoistureData.objects.filter(region=region, date=date).first()
        if existing:
            logger.info(f"Soil moisture data already exists for {region.name} on {date}")
            return {'status': 'exists', 'region': region.name, 'date': str(date)}
        
        # Placeholder for actual API integration
        mock_moisture_value = _generate_mock_soil_moisture_value(region)
        
        soil_data = SoilMoistureData.objects.create(
            region=region,
            date=date,
            moisture_percent=mock_moisture_value,
            soil_depth_cm=10,
            data_source='satellite',
            temperature_celsius=25.0
        )
        
        logger.info(f"Created soil moisture data for {region.name}: {mock_moisture_value}%")
        return {
            'status': 'created',
            'region': region.name,
            'date': str(date),
            'moisture_percent': mock_moisture_value
        }
        
    except Region.DoesNotExist:
        logger.error(f"Region with ID {region_id} not found")
        return {'status': 'error', 'message': 'Region not found'}
    except Exception as e:
        logger.error(f"Error fetching soil moisture data: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def fetch_weather_data_for_region(region_id: int, date_str: str = None) -> Dict[str, Any]:
    """
    Fetch weather data for a specific region
    This would integrate with OpenWeatherMap or similar APIs
    """
    try:
        region = Region.objects.get(id=region_id)
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        # Check if data already exists
        existing = WeatherData.objects.filter(region=region, date=date).first()
        if existing:
            logger.info(f"Weather data already exists for {region.name} on {date}")
            return {'status': 'exists', 'region': region.name, 'date': str(date)}
        
        # Placeholder for actual API integration with OpenWeatherMap
        weather_data = _generate_mock_weather_data(region)
        
        weather = WeatherData.objects.create(
            region=region,
            date=date,
            temperature_max=weather_data['temp_max'],
            temperature_min=weather_data['temp_min'],
            temperature_avg=weather_data['temp_avg'],
            precipitation_mm=weather_data['precipitation'],
            humidity_percent=weather_data['humidity'],
            wind_speed_kmh=weather_data['wind_speed'],
            data_source='OpenWeatherMap'
        )
        
        logger.info(f"Created weather data for {region.name}")
        return {
            'status': 'created',
            'region': region.name,
            'date': str(date),
            'data': weather_data
        }
        
    except Region.DoesNotExist:
        logger.error(f"Region with ID {region_id} not found")
        return {'status': 'error', 'message': 'Region not found'}
    except Exception as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def calculate_drought_risk_for_region(region_id: int, assessment_date_str: str = None) -> Dict[str, Any]:
    """
    Calculate drought risk assessment for a region based on available data
    """
    try:
        region = Region.objects.get(id=region_id)
        
        if assessment_date_str:
            assessment_date = datetime.strptime(assessment_date_str, '%Y-%m-%d').date()
        else:
            assessment_date = timezone.now().date()
        
        # Check if assessment already exists for today
        existing = DroughtRiskAssessment.objects.filter(
            region=region, 
            assessment_date=assessment_date
        ).first()
        
        if existing:
            logger.info(f"Drought assessment already exists for {region.name} on {assessment_date}")
            return {
                'status': 'exists',
                'region': region.name,
                'date': str(assessment_date),
                'risk_score': existing.risk_score
            }
        
        # Get recent data for analysis
        recent_days = 30
        start_date = assessment_date - timedelta(days=recent_days)
        
        # Get latest NDVI data
        latest_ndvi = NDVIData.objects.filter(
            region=region,
            date__gte=start_date,
            date__lte=assessment_date
        ).order_by('-date').first()
        
        # Get latest soil moisture data
        latest_soil = SoilMoistureData.objects.filter(
            region=region,
            date__gte=start_date,
            date__lte=assessment_date
        ).order_by('-date').first()
        
        # Get recent weather data
        recent_weather = WeatherData.objects.filter(
            region=region,
            date__gte=start_date,
            date__lte=assessment_date
        ).order_by('-date')
        
        # Calculate component scores
        ndvi_score = _calculate_ndvi_risk_score(latest_ndvi)
        soil_score = _calculate_soil_moisture_risk_score(latest_soil)
        weather_score = _calculate_weather_risk_score(recent_weather)
        
        # Calculate overall risk score (weighted average)
        overall_risk_score = (ndvi_score * 0.4 + soil_score * 0.4 + weather_score * 0.2)
        
        # Generate recommendations
        recommendations = _generate_drought_recommendations(overall_risk_score, latest_ndvi, latest_soil)
        
        # Create assessment
        assessment = DroughtRiskAssessment.objects.create(
            region=region,
            assessment_date=assessment_date,
            risk_score=overall_risk_score,
            ndvi_component_score=ndvi_score,
            soil_moisture_component_score=soil_score,
            weather_component_score=weather_score,
            model_version='1.0',
            confidence_score=0.75,
            recommended_actions=recommendations
        )
        
        logger.info(f"Created drought assessment for {region.name}: {overall_risk_score:.1f}")
        return {
            'status': 'created',
            'region': region.name,
            'date': str(assessment_date),
            'risk_score': overall_risk_score,
            'risk_level': assessment.risk_level
        }
        
    except Region.DoesNotExist:
        logger.error(f"Region with ID {region_id} not found")
        return {'status': 'error', 'message': 'Region not found'}
    except Exception as e:
        logger.error(f"Error calculating drought risk: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def collect_historical_data_for_region(region_id: int, days_back: int = 30) -> Dict[str, Any]:
    """
    Collect historical data for a specific region using the integration service
    """
    try:
        region = Region.objects.get(id=region_id)
        
        integration_service = DataIntegrationService()
        result = integration_service.collect_historical_data_for_region(region, days_back)
        
        logger.info(f"Collected {result['days_collected']} days of historical data for {region.name}")
        return result
        
    except Region.DoesNotExist:
        logger.error(f"Region with ID {region_id} not found")
        return {'status': 'error', 'message': 'Region not found'}
    except Exception as e:
        logger.error(f"Error collecting historical data: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def fetch_all_data_for_all_regions(date_str: str = None):
    """
    Fetch all types of data for all regions
    This task orchestrates data collection for the entire system
    """
    results = {
        'ndvi': [],
        'soil_moisture': [],
        'weather': [],
        'drought_assessments': []
    }
    
    regions = Region.objects.all()
    
    for region in regions:
        # Fetch NDVI data
        ndvi_result = fetch_ndvi_data_for_region.apply(args=[region.id, date_str])
        results['ndvi'].append(ndvi_result.result)
        
        # Fetch soil moisture data
        soil_result = fetch_soil_moisture_data_for_region.apply(args=[region.id, date_str])
        results['soil_moisture'].append(soil_result.result)
        
        # Fetch weather data
        weather_result = fetch_weather_data_for_region.apply(args=[region.id, date_str])
        results['weather'].append(weather_result.result)
        
        # Calculate drought risk
        risk_result = calculate_drought_risk_for_region.apply(args=[region.id, date_str])
        results['drought_assessments'].append(risk_result.result)
    
    logger.info(f"Completed data fetch for {len(regions)} regions")
    return results


# Helper functions for mock data generation and risk calculation
def _generate_mock_ndvi_value(region: Region) -> float:
    """Generate realistic mock NDVI values based on region"""
    import random
    
    # Base NDVI on region type and add some randomness
    base_values = {
        'county': 0.45,
        'ward': 0.4,
        'village': 0.35
    }
    
    base = base_values.get(region.region_type, 0.4)
    return round(base + random.uniform(-0.2, 0.2), 3)


def _generate_mock_soil_moisture_value(region: Region) -> float:
    """Generate realistic mock soil moisture values"""
    import random
    return round(random.uniform(15.0, 65.0), 1)


def _generate_mock_weather_data(region: Region) -> Dict[str, float]:
    """Generate realistic mock weather data"""
    import random
    
    temp_avg = random.uniform(20.0, 35.0)
    return {
        'temp_max': round(temp_avg + random.uniform(2, 8), 1),
        'temp_min': round(temp_avg - random.uniform(3, 10), 1),
        'temp_avg': round(temp_avg, 1),
        'precipitation': round(random.uniform(0, 25), 1),
        'humidity': round(random.uniform(30, 80), 1),
        'wind_speed': round(random.uniform(5, 25), 1)
    }


def _calculate_ndvi_risk_score(ndvi_data: Optional[NDVIData]) -> float:
    """Calculate risk score based on NDVI data"""
    if not ndvi_data:
        return 50.0  # Medium risk if no data
    
    # Lower NDVI = higher risk
    if ndvi_data.ndvi_value >= 0.6:
        return 10.0  # Very low risk
    elif ndvi_data.ndvi_value >= 0.4:
        return 30.0  # Low risk
    elif ndvi_data.ndvi_value >= 0.2:
        return 60.0  # High risk
    else:
        return 90.0  # Very high risk


def _calculate_soil_moisture_risk_score(soil_data: Optional[SoilMoistureData]) -> float:
    """Calculate risk score based on soil moisture data"""
    if not soil_data:
        return 50.0  # Medium risk if no data
    
    # Lower moisture = higher risk
    if soil_data.moisture_percent >= 60:
        return 10.0  # Very low risk
    elif soil_data.moisture_percent >= 40:
        return 30.0  # Low risk
    elif soil_data.moisture_percent >= 20:
        return 60.0  # High risk
    else:
        return 90.0  # Very high risk


def _calculate_weather_risk_score(weather_data) -> float:
    """Calculate risk score based on recent weather data"""
    if not weather_data.exists():
        return 50.0  # Medium risk if no data
    
    # Analyze recent precipitation
    total_rainfall = sum(w.precipitation_mm for w in weather_data[:7])  # Last 7 days
    avg_temp = sum(w.temperature_avg for w in weather_data[:7] if w.temperature_avg) / max(len(weather_data[:7]), 1)
    
    # Risk based on rainfall and temperature
    if total_rainfall >= 50:
        return 10.0  # Very low risk
    elif total_rainfall >= 25:
        return 30.0  # Low risk
    elif total_rainfall >= 10:
        return 50.0  # Medium risk
    else:
        # No significant rain + high temperatures = high risk
        if avg_temp > 30:
            return 85.0
        else:
            return 70.0


def _generate_drought_recommendations(risk_score: float, ndvi_data, soil_data) -> str:
    """Generate recommendations based on risk assessment"""
    recommendations = []
    
    if risk_score >= 80:
        recommendations.extend([
            "CRITICAL: Implement emergency water conservation measures",
            "Avoid planting water-intensive crops",
            "Prioritize drought-resistant crop varieties",
            "Consider alternative livelihood activities"
        ])
    elif risk_score >= 65:
        recommendations.extend([
            "HIGH RISK: Increase irrigation frequency",
            "Plant early-maturing crop varieties",
            "Monitor soil moisture levels daily"
        ])
    elif risk_score >= 50:
        recommendations.extend([
            "MODERATE RISK: Monitor weather conditions closely",
            "Prepare irrigation systems",
            "Consider supplemental watering"
        ])
    else:
        recommendations.extend([
            "LOW RISK: Continue normal farming activities",
            "Monitor conditions for any changes"
        ])
    
    return "; ".join(recommendations)


@shared_task
def assess_drought_risk_ml(region_id: int, date_str: str = None) -> Dict[str, Any]:
    """
    Assess drought risk using machine learning model
    
    Args:
        region_id: ID of the region to assess
        date_str: Date string in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Dictionary with assessment results
    """
    try:
        region = Region.objects.get(id=region_id)
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        # Initialize early warning system
        ews = DroughtEarlyWarningSystem()
        
        # Create assessment
        assessment = ews.assess_drought_risk(region, date)
        
        logger.info(
            f"Created ML drought assessment for {region.name}: "
            f"{assessment.risk_level} risk (score: {assessment.risk_score})"
        )
        
        return {
            'status': 'success',
            'region': region.name,
            'date': str(date),
            'risk_score': assessment.risk_score,
            'risk_level': assessment.risk_level,
            'recommended_actions': assessment.recommended_actions
        }
        
    except Region.DoesNotExist:
        logger.error(f"Region with ID {region_id} not found")
        return {'status': 'error', 'message': 'Region not found'}
    except Exception as e:
        logger.error(f"Error in ML drought assessment: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def bulk_assess_drought_risk_all_regions(date_str: str = None) -> Dict[str, Any]:
    """
    Assess drought risk for all regions using ML model
    
    Args:
        date_str: Date string in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Dictionary with bulk assessment results
    """
    try:
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        # Get all county regions
        regions = Region.objects.filter(region_type='county')
        
        results = {
            'date': str(date),
            'total_regions': regions.count(),
            'assessments_created': 0,
            'assessments_failed': 0,
            'risk_summary': {
                'extreme': 0,
                'high': 0,
                'moderate': 0,
                'low': 0,
                'minimal': 0
            },
            'failed_regions': []
        }
        
        # Initialize early warning system
        ews = DroughtEarlyWarningSystem()
        
        for region in regions:
            try:
                # Create assessment
                assessment = ews.assess_drought_risk(region, date)
                
                results['assessments_created'] += 1
                results['risk_summary'][assessment.risk_level] += 1
                
                logger.info(
                    f"Assessed {region.name}: {assessment.risk_level} "
                    f"(score: {assessment.risk_score})"
                )
                
            except Exception as e:
                results['assessments_failed'] += 1
                results['failed_regions'].append({
                    'region': region.name,
                    'error': str(e)
                })
                logger.error(f"Failed to assess {region.name}: {e}")
        
        logger.info(
            f"Bulk assessment completed: {results['assessments_created']} successful, "
            f"{results['assessments_failed']} failed"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in bulk drought assessment: {str(e)}")
        return {'status': 'error', 'message': str(e)}