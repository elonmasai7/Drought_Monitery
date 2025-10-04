from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Region(models.Model):
    """
    Geographic regions (Counties, Wards, etc.) for drought monitoring
    """
    REGION_TYPES = [
        ('country', 'Country'),
        ('county', 'County'),
        ('ward', 'Ward'),
        ('village', 'Village'),
    ]
    
    name = models.CharField(max_length=100)
    region_type = models.CharField(max_length=20, choices=REGION_TYPES)
    parent_region = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    
    # GPS Coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Additional metadata
    area_sq_km = models.FloatField(null=True, blank=True, help_text="Area in square kilometers")
    population = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['region_type', 'name']
        unique_together = ['name', 'region_type', 'parent_region']
    
    def __str__(self):
        return f"{self.name} ({self.get_region_type_display()})"
    
    @property
    def full_name(self):
        """Return full hierarchical name"""
        if self.parent_region:
            return f"{self.parent_region.full_name} > {self.name}"
        return self.name


class UserProfile(models.Model):
    """
    Extended user profile for farmers and administrators
    """
    USER_TYPES = [
        ('farmer', 'Farmer'),
        ('admin', 'Administrator'),
        ('extension_officer', 'Extension Officer'),
    ]
    
    LANGUAGES = [
        ('en', 'English'),
        ('sw', 'Swahili'),
        ('ki', 'Kikuyu'),
        ('lu', 'Luhya'),
        ('luo', 'Luo'),
        ('ka', 'Kamba'),
        ('me', 'Meru'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='farmer')
    phone_number = models.CharField(max_length=20, unique=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_language = models.CharField(max_length=5, choices=LANGUAGES, default='en')
    
    # Contact preferences
    receive_whatsapp_alerts = models.BooleanField(default=True)
    receive_sms_alerts = models.BooleanField(default=True)
    receive_email_alerts = models.BooleanField(default=False)
    
    # Farmer-specific fields
    farm_size_acres = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.1)])
    primary_crops = models.CharField(max_length=200, blank=True, help_text="Comma-separated list of crops")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_user_type_display()})"
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username