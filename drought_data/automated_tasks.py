"""
Automated tasks for drought risk calculation and alert triggering
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Count, Q
from celery import shared_task

from core.models import Region
from .models import WeatherData, NDVIData, SoilMoistureData, DroughtRiskAssessment
from .ml_models import DroughtRiskPredictor
from alerts.models import Alert, AlertTemplate
from alerts.tasks import send_alert

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def calculate_daily_drought_risk(self, region_id=None):
    """
    Calculate drought risk assessments for all regions or a specific region
    """
    try:
        logger.info(f"Starting daily drought risk calculation for region_id={region_id}")
        
        # Get regions to process
        if region_id:
            regions = Region.objects.filter(id=region_id, region_type='county')
        else:
            regions = Region.objects.filter(region_type='county')
        
        if not regions.exists():
            logger.warning("No regions found for drought risk calculation")
            return {"status": "warning", "message": "No regions found"}
        
        today = timezone.now().date()
        results = {
            "processed_regions": 0,
            "assessments_created": 0,
            "errors": 0,
            "region_results": []
        }
        
        predictor = DroughtRiskPredictor()
        
        for region in regions:
            try:
                logger.info(f"Processing drought risk for region: {region.name}")
                
                # Check if assessment already exists for today
                existing_assessment = DroughtRiskAssessment.objects.filter(
                    region=region,
                    assessment_date=today
                ).first()
                
                if existing_assessment:
                    logger.info(f"Assessment already exists for {region.name} on {today}")
                    results["region_results"].append({
                        "region": region.name,
                        "status": "skipped",
                        "message": "Assessment already exists"
                    })
                    continue
                
                # Get recent data (last 30 days)
                end_date = today
                start_date = end_date - timedelta(days=30)
                
                # Collect data for the region
                weather_data = WeatherData.objects.filter(
                    region=region,
                    date__range=[start_date, end_date]
                ).order_by('-date')
                
                ndvi_data = NDVIData.objects.filter(
                    region=region,
                    date__range=[start_date, end_date]
                ).order_by('-date')
                
                soil_data = SoilMoistureData.objects.filter(
                    region=region,
                    date__range=[start_date, end_date]
                ).order_by('-date')
                
                # Check if we have sufficient data
                if not weather_data.exists() and not ndvi_data.exists() and not soil_data.exists():
                    logger.warning(f"Insufficient data for {region.name}")
                    results["region_results"].append({
                        "region": region.name,
                        "status": "insufficient_data",
                        "message": "No recent data available"
                    })
                    results["errors"] += 1
                    continue
                
                # Calculate component scores
                weather_score = calculate_weather_drought_score(weather_data)
                ndvi_score = calculate_ndvi_drought_score(ndvi_data)
                soil_score = calculate_soil_drought_score(soil_data)
                
                # Calculate overall risk score using weighted average
                weights = {"weather": 0.4, "ndvi": 0.3, "soil": 0.3}
                
                # Only use scores for components that have data
                available_scores = {}
                if weather_score is not None:
                    available_scores["weather"] = weather_score
                if ndvi_score is not None:
                    available_scores["ndvi"] = ndvi_score
                if soil_score is not None:
                    available_scores["soil"] = soil_score
                
                if not available_scores:
                    logger.warning(f"No valid component scores for {region.name}")
                    results["region_results"].append({
                        "region": region.name,
                        "status": "no_valid_scores",
                        "message": "Could not calculate component scores"
                    })
                    results["errors"] += 1
                    continue
                
                # Normalize weights for available components
                total_weight = sum(weights[comp] for comp in available_scores.keys())
                normalized_weights = {comp: weights[comp] / total_weight for comp in available_scores.keys()}
                
                # Calculate weighted average
                risk_score = sum(available_scores[comp] * normalized_weights[comp] 
                               for comp in available_scores.keys())
                
                # Use ML model for prediction if we have sufficient data
                try:
                    ml_predictions = predictor.predict_drought_risk(region, today)
                    predicted_risk_7_days = ml_predictions.get('7_day_risk')
                    predicted_risk_30_days = ml_predictions.get('30_day_risk')
                    confidence_score = ml_predictions.get('confidence', 0.5)
                except Exception as e:
                    logger.warning(f"ML prediction failed for {region.name}: {str(e)}")
                    predicted_risk_7_days = None
                    predicted_risk_30_days = None
                    confidence_score = 0.3
                
                # Generate recommendations
                recommendations = generate_drought_recommendations(
                    risk_score, available_scores, region
                )
                
                # Create drought risk assessment
                with transaction.atomic():
                    assessment = DroughtRiskAssessment.objects.create(
                        region=region,
                        assessment_date=today,
                        risk_score=risk_score,
                        ndvi_component_score=ndvi_score or 0,
                        soil_moisture_component_score=soil_score or 0,
                        weather_component_score=weather_score or 0,
                        predicted_risk_7_days=predicted_risk_7_days,
                        predicted_risk_30_days=predicted_risk_30_days,
                        confidence_score=confidence_score,
                        recommended_actions=recommendations
                    )
                
                logger.info(f"Created assessment for {region.name}: risk_score={risk_score:.1f}, risk_level={assessment.risk_level}")
                
                results["assessments_created"] += 1
                results["region_results"].append({
                    "region": region.name,
                    "status": "success",
                    "risk_score": risk_score,
                    "risk_level": assessment.risk_level,
                    "assessment_id": assessment.id
                })
                
            except Exception as e:
                logger.error(f"Error processing region {region.name}: {str(e)}")
                results["errors"] += 1
                results["region_results"].append({
                    "region": region.name,
                    "status": "error",
                    "message": str(e)
                })
            
            results["processed_regions"] += 1
        
        logger.info(f"Drought risk calculation completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Fatal error in drought risk calculation: {str(e)}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)
        raise


@shared_task(bind=True, max_retries=3)
def trigger_drought_alerts(self, min_risk_threshold=50.0):
    """
    Check recent drought assessments and trigger alerts for high-risk regions
    """
    try:
        logger.info(f"Starting drought alert triggering with threshold={min_risk_threshold}")
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get recent high-risk assessments
        high_risk_assessments = DroughtRiskAssessment.objects.filter(
            assessment_date__gte=yesterday,
            risk_score__gte=min_risk_threshold
        ).select_related('region')
        
        if not high_risk_assessments.exists():
            logger.info("No high-risk assessments found for alert triggering")
            return {"status": "success", "message": "No high-risk regions found", "alerts_triggered": 0}
        
        results = {
            "alerts_triggered": 0,
            "errors": 0,
            "alert_results": []
        }
        
        for assessment in high_risk_assessments:
            try:
                # Check if alert was already sent for this assessment
                existing_alert = Alert.objects.filter(
                    region=assessment.region,
                    drought_assessment=assessment,
                    status__in=['sent', 'sending']
                ).exists()
                
                if existing_alert:
                    logger.info(f"Alert already exists for {assessment.region.name} assessment {assessment.id}")
                    results["alert_results"].append({
                        "region": assessment.region.name,
                        "status": "skipped",
                        "message": "Alert already sent"
                    })
                    continue
                
                # Determine alert severity based on risk score
                if assessment.risk_score >= 80:
                    severity = 'critical'
                    alert_type = 'drought_warning'
                elif assessment.risk_score >= 65:
                    severity = 'high'
                    alert_type = 'drought_warning'
                elif assessment.risk_score >= 50:
                    severity = 'moderate'
                    alert_type = 'water_stress'
                else:
                    continue  # Skip low-risk assessments
                
                # Get or create alert template
                template = AlertTemplate.objects.filter(
                    alert_type=alert_type,
                    severity_level=severity,
                    language='en',
                    is_active=True
                ).first()
                
                if not template:
                    # Create a default template
                    template = create_default_alert_template(alert_type, severity)
                
                # Generate alert content
                alert_title = f"Drought {severity.upper()} Alert - {assessment.region.name}"
                alert_message = generate_alert_message(assessment, template)
                
                # Create alert
                alert = Alert.objects.create(
                    region=assessment.region,
                    template=template,
                    title=alert_title,
                    message=alert_message,
                    sms_message=alert_message[:160] if len(alert_message) > 160 else alert_message,
                    priority='urgent' if severity in ['critical', 'high'] else 'high',
                    status='sending',
                    drought_assessment=assessment,
                    created_by_id=1  # System user
                )
                
                # Schedule alert delivery
                send_alert.delay(alert.id)
                
                logger.info(f"Triggered {severity} alert for {assessment.region.name} (risk score: {assessment.risk_score:.1f})")
                
                results["alerts_triggered"] += 1
                results["alert_results"].append({
                    "region": assessment.region.name,
                    "status": "success",
                    "alert_id": alert.alert_id,
                    "severity": severity,
                    "risk_score": assessment.risk_score
                })
                
            except Exception as e:
                logger.error(f"Error creating alert for {assessment.region.name}: {str(e)}")
                results["errors"] += 1
                results["alert_results"].append({
                    "region": assessment.region.name,
                    "status": "error",
                    "message": str(e)
                })
        
        logger.info(f"Alert triggering completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Fatal error in alert triggering: {str(e)}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task, attempt {self.request.retries + 1}")
            raise self.retry(countdown=300, exc=e)  # 5-minute delay for retries
        raise


def calculate_weather_drought_score(weather_data):
    """
    Calculate drought score based on weather data (0-100, higher = more drought risk)
    """
    if not weather_data.exists():
        return None
    
    recent_data = weather_data[:14]  # Last 2 weeks
    
    # Calculate metrics
    avg_temp = recent_data.aggregate(avg_temp=Avg('temperature_avg'))['avg_temp'] or 0
    total_precipitation = sum(w.precipitation_mm for w in recent_data)
    avg_humidity = recent_data.aggregate(avg_humidity=Avg('humidity_percent'))['avg_humidity'] or 0
    
    # Score components (0-100 scale)
    temp_score = min(max((avg_temp - 20) * 2.5, 0), 100)  # Higher temp = higher risk
    precip_score = max(min(100 - (total_precipitation * 2), 100), 0)  # Less rain = higher risk
    humidity_score = max(min(100 - avg_humidity, 100), 0)  # Lower humidity = higher risk
    
    # Weighted average
    weather_score = (temp_score * 0.4 + precip_score * 0.4 + humidity_score * 0.2)
    
    return min(max(weather_score, 0), 100)


def calculate_ndvi_drought_score(ndvi_data):
    """
    Calculate drought score based on NDVI data (0-100, higher = more drought risk)
    """
    if not ndvi_data.exists():
        return None
    
    recent_ndvi = ndvi_data[:5]  # Last 5 measurements
    avg_ndvi = sum(n.ndvi_value for n in recent_ndvi) / len(recent_ndvi)
    
    # NDVI to drought risk conversion
    # NDVI > 0.6 = healthy (low risk)
    # NDVI 0.4-0.6 = moderate (medium risk)  
    # NDVI < 0.4 = stressed (high risk)
    
    if avg_ndvi >= 0.6:
        ndvi_score = max((0.8 - avg_ndvi) * 200, 0)  # 0-40 range
    elif avg_ndvi >= 0.4:
        ndvi_score = 40 + (0.6 - avg_ndvi) * 300  # 40-100 range
    else:
        ndvi_score = 100  # Maximum risk
    
    return min(max(ndvi_score, 0), 100)


def calculate_soil_drought_score(soil_data):
    """
    Calculate drought score based on soil moisture data (0-100, higher = more drought risk)
    """
    if not soil_data.exists():
        return None
    
    recent_soil = soil_data[:7]  # Last week
    avg_moisture = sum(s.moisture_percent for s in recent_soil) / len(recent_soil)
    
    # Soil moisture to drought risk conversion
    # >60% = saturated (very low risk)
    # 40-60% = adequate (low risk)
    # 20-40% = low (medium risk)
    # <20% = very low (high risk)
    
    if avg_moisture >= 60:
        soil_score = 10  # Very low risk
    elif avg_moisture >= 40:
        soil_score = 30  # Low risk
    elif avg_moisture >= 20:
        soil_score = 70  # Medium-high risk
    else:
        soil_score = 90  # High risk
    
    return min(max(soil_score, 0), 100)


def generate_drought_recommendations(risk_score, component_scores, region):
    """
    Generate drought management recommendations based on assessment
    """
    recommendations = []
    
    if risk_score >= 80:
        recommendations.extend([
            "CRITICAL: Implement emergency water conservation measures",
            "Consider livestock destocking to reduce pressure on grazing lands",
            "Activate community drought response plans",
            "Coordinate with disaster management authorities"
        ])
    elif risk_score >= 65:
        recommendations.extend([
            "HIGH RISK: Intensify water conservation practices",
            "Monitor livestock and crop conditions closely",
            "Prepare contingency plans for water and feed supplies",
            "Consider early harvesting of mature crops"
        ])
    elif risk_score >= 50:
        recommendations.extend([
            "MODERATE RISK: Begin water conservation measures",
            "Monitor weather forecasts closely",
            "Check irrigation systems and water storage",
            "Prepare drought-resistant crop varieties for next season"
        ])
    
    # Component-specific recommendations
    weather_score = component_scores.get('weather', 0)
    if weather_score > 70:
        recommendations.append("Weather conditions show high drought risk - monitor rainfall patterns")
    
    ndvi_score = component_scores.get('ndvi', 0)
    if ndvi_score > 70:
        recommendations.append("Vegetation stress detected - consider supplemental feeding for livestock")
    
    soil_score = component_scores.get('soil', 0)
    if soil_score > 70:
        recommendations.append("Low soil moisture detected - optimize irrigation scheduling")
    
    return "; ".join(recommendations)


def generate_alert_message(assessment, template):
    """
    Generate alert message using template and assessment data
    """
    context = {
        'region_name': assessment.region.name,
        'risk_score': assessment.risk_score,
        'risk_level': assessment.get_risk_level_display(),
        'assessment_date': assessment.assessment_date.strftime('%Y-%m-%d'),
        'recommendations': assessment.recommended_actions,
        'predicted_risk_7_days': assessment.predicted_risk_7_days,
        'predicted_risk_30_days': assessment.predicted_risk_30_days
    }
    
    # Simple template substitution
    message = template.message_template
    for key, value in context.items():
        placeholder = '{' + key + '}'
        if placeholder in message and value is not None:
            message = message.replace(placeholder, str(value))
    
    return message


def create_default_alert_template(alert_type, severity_level):
    """
    Create a default alert template if none exists
    """
    templates = {
        ('drought_warning', 'critical'): {
            'title': 'CRITICAL Drought Warning - {region_name}',
            'message': 'CRITICAL DROUGHT WARNING for {region_name}. Risk Score: {risk_score}/100. Current risk level: {risk_level}. Immediate action required: {recommendations}. Assessment date: {assessment_date}.',
            'sms': 'CRITICAL DROUGHT WARNING {region_name}. Risk: {risk_score}/100. Take immediate action.'
        },
        ('drought_warning', 'high'): {
            'title': 'HIGH Drought Warning - {region_name}',
            'message': 'HIGH DROUGHT WARNING for {region_name}. Risk Score: {risk_score}/100. Current risk level: {risk_level}. Recommended actions: {recommendations}. Assessment date: {assessment_date}.',
            'sms': 'HIGH DROUGHT WARNING {region_name}. Risk: {risk_score}/100. Take preventive action.'
        },
        ('water_stress', 'moderate'): {
            'title': 'Water Stress Alert - {region_name}',
            'message': 'WATER STRESS ALERT for {region_name}. Risk Score: {risk_score}/100. Current risk level: {risk_level}. Recommendations: {recommendations}. Assessment date: {assessment_date}.',
            'sms': 'WATER STRESS ALERT {region_name}. Risk: {risk_score}/100. Monitor conditions.'
        }
    }
    
    template_data = templates.get((alert_type, severity_level), templates[('water_stress', 'moderate')])
    
    template = AlertTemplate.objects.create(
        name=f"Auto-generated {alert_type} {severity_level}",
        alert_type=alert_type,
        severity_level=severity_level,
        title_template=template_data['title'],
        message_template=template_data['message'],
        sms_template=template_data['sms'],
        language='en',
        is_active=True,
        auto_send=True
    )
    
    return template
