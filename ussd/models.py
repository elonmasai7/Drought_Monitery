from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Region


class USSDSession(models.Model):
    """Track USSD sessions for feature phone users"""
    SESSION_STATES = [
        ('main_menu', 'Main Menu'),
        ('weather_info', 'Weather Information'),
        ('drought_alerts', 'Drought Alerts'),
        ('crop_advice', 'Crop Advice'),
        ('registration', 'User Registration'),
        ('profile_update', 'Profile Update'),
        ('help', 'Help'),
        ('ended', 'Session Ended'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    current_state = models.CharField(max_length=20, choices=SESSION_STATES, default='main_menu')
    language = models.CharField(max_length=5, default='en')
    context_data = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_requests = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"USSD Session {self.session_id} - {self.phone_number}"
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.total_requests += 1
        self.save()

    def end_session(self):
        """Mark session as ended"""
        self.is_active = False
        self.ended_at = timezone.now()
        self.current_state = 'ended'
        self.save()


class USSDUser(models.Model):
    """Extended profile for USSD users (feature phone users)"""
    phone_number = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    preferred_language = models.CharField(max_length=5, default='en')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    farm_size_acres = models.FloatField(null=True, blank=True)
    primary_crops = models.CharField(max_length=200, blank=True)
    receive_alerts = models.BooleanField(default=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"USSD User {self.phone_number} ({self.full_name or 'Unnamed'})"
