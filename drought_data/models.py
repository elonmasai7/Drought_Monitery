from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Region


class NDVIData(models.Model):
    """
    Normalized Difference Vegetation Index data from satellite imagery
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='ndvi_data')
    date = models.DateField()
    
    # NDVI values typically range from -1 to 1
    ndvi_value = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        help_text="NDVI value (-1 to 1, higher values indicate healthier vegetation)"
    )
    
    # Data source information
    satellite_source = models.CharField(max_length=50, default='Landsat-8')
    cloud_cover_percent = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Quality flags
    data_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'region']
        unique_together = ['region', 'date', 'satellite_source']
    
    def __str__(self):
        return f"NDVI {self.ndvi_value:.3f} - {self.region.name} ({self.date})"
    
    @property
    def vegetation_health_status(self):
        """Categorize vegetation health based on NDVI value"""
        if self.ndvi_value >= 0.6:
            return "Healthy"
        elif self.ndvi_value >= 0.4:
            return "Moderate"
        elif self.ndvi_value >= 0.2:
            return "Stressed"
        else:
            return "Severely Stressed"


class SoilMoistureData(models.Model):
    """
    Soil moisture data from satellite or ground measurements
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='soil_moisture_data')
    date = models.DateField()
    
    # Soil moisture as percentage (0-100%)
    moisture_percent = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Soil moisture percentage (0-100%)"
    )
    
    # Soil depth in centimeters
    soil_depth_cm = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        help_text="Soil depth in centimeters"
    )
    
    # Data source
    data_source = models.CharField(
        max_length=50,
        choices=[
            ('satellite', 'Satellite (SMAP/SMOS)'),
            ('ground_sensor', 'Ground Sensor'),
            ('model_estimate', 'Model Estimate'),
        ],
        default='satellite'
    )
    
    temperature_celsius = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'region']
        unique_together = ['region', 'date', 'soil_depth_cm', 'data_source']
    
    def __str__(self):
        return f"Soil Moisture {self.moisture_percent:.1f}% - {self.region.name} ({self.date})"
    
    @property
    def moisture_status(self):
        """Categorize soil moisture status"""
        if self.moisture_percent >= 60:
            return "Saturated"
        elif self.moisture_percent >= 40:
            return "Adequate"
        elif self.moisture_percent >= 20:
            return "Low"
        else:
            return "Very Low"


class WeatherData(models.Model):
    """
    Weather information for drought context
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='weather_data')
    date = models.DateField()
    
    # Temperature in Celsius
    temperature_max = models.FloatField(null=True, blank=True)
    temperature_min = models.FloatField(null=True, blank=True)
    temperature_avg = models.FloatField(null=True, blank=True)
    
    # Precipitation in millimeters
    precipitation_mm = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Daily precipitation in millimeters"
    )
    
    # Humidity percentage
    humidity_percent = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Wind speed in km/h
    wind_speed_kmh = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Evapotranspiration
    evapotranspiration_mm = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Daily evapotranspiration in millimeters"
    )
    
    data_source = models.CharField(max_length=50, default='OpenWeatherMap')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'region']
        unique_together = ['region', 'date', 'data_source']
    
    def __str__(self):
        return f"Weather - {self.region.name} ({self.date})"


class DroughtRiskAssessment(models.Model):
    """
    Calculated drought risk assessment combining multiple data sources
    """
    RISK_LEVELS = [
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('very_high', 'Very High'),
        ('extreme', 'Extreme'),
    ]
    
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='drought_assessments')
    assessment_date = models.DateField()
    
    # Risk score (0-100)
    risk_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Drought risk score (0-100, higher is more risk)"
    )
    
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    
    # Component scores
    ndvi_component_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    soil_moisture_component_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    weather_component_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Predictions
    predicted_risk_7_days = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Predicted risk score for 7 days ahead"
    )
    predicted_risk_30_days = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Predicted risk score for 30 days ahead"
    )
    
    # Analysis metadata
    model_version = models.CharField(max_length=20, default='1.0')
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Model confidence (0-1)"
    )
    
    # Recommendations
    recommended_actions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-assessment_date', 'region']
        unique_together = ['region', 'assessment_date']
    
    def __str__(self):
        return f"Drought Risk {self.get_risk_level_display()} ({self.risk_score:.1f}) - {self.region.name}"
    
    def save(self, *args, **kwargs):
        """Auto-assign risk level based on score"""
        if self.risk_score >= 80:
            self.risk_level = 'extreme'
        elif self.risk_score >= 65:
            self.risk_level = 'very_high'
        elif self.risk_score >= 50:
            self.risk_level = 'high'
        elif self.risk_score >= 35:
            self.risk_level = 'moderate'
        elif self.risk_score >= 20:
            self.risk_level = 'low'
        else:
            self.risk_level = 'very_low'
        
        super().save(*args, **kwargs)