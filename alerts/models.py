from django.db import models
from django.contrib.auth.models import User
from core.models import Region, UserProfile
from drought_data.models import DroughtRiskAssessment


class AlertTemplate(models.Model):
    """
    Templates for different types of alerts
    """
    ALERT_TYPES = [
        ('drought_warning', 'Drought Warning'),
        ('water_stress', 'Water Stress Alert'),
        ('planting_advisory', 'Planting Advisory'),
        ('harvest_advisory', 'Harvest Advisory'),
        ('irrigation_reminder', 'Irrigation Reminder'),
        ('weather_warning', 'Weather Warning'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency'),
    ]
    
    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity_level = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    
    # Message templates
    title_template = models.CharField(max_length=200)
    message_template = models.TextField(help_text="Use {variable_name} for dynamic content")
    sms_template = models.CharField(
        max_length=160, 
        help_text="SMS version (max 160 characters)"
    )
    
    # Languages
    language = models.CharField(
        max_length=5,
        choices=[
            ('en', 'English'),
            ('sw', 'Swahili'),
            ('ki', 'Kikuyu'),
            ('lu', 'Luhya'),
            ('luo', 'Luo'),
            ('ka', 'Kamba'),
            ('me', 'Meru'),
        ],
        default='en'
    )
    
    # Template settings
    is_active = models.BooleanField(default=True)
    auto_send = models.BooleanField(
        default=False, 
        help_text="Automatically send when conditions are met"
    )
    
    # Triggering conditions
    trigger_risk_threshold = models.FloatField(
        null=True, blank=True,
        help_text="Risk score threshold to trigger this alert"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['alert_type', 'severity_level', 'language']
        unique_together = ['name', 'language']
    
    def __str__(self):
        return f"{self.name} ({self.get_language_display()})"


class Alert(models.Model):
    """
    Individual alerts sent to users or regions
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Alert identification
    alert_id = models.CharField(max_length=20, unique=True)
    template = models.ForeignKey(AlertTemplate, on_delete=models.CASCADE)
    
    # Targeting
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    target_users = models.ManyToManyField(UserProfile, blank=True)
    
    # Alert content
    title = models.CharField(max_length=200)
    message = models.TextField()
    sms_message = models.CharField(max_length=160, blank=True)
    
    # Alert metadata
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Related data
    drought_assessment = models.ForeignKey(
        DroughtRiskAssessment, 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    
    # Scheduling
    scheduled_send_time = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Creator
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Metrics
    total_recipients = models.IntegerField(default=0)
    successfully_sent = models.IntegerField(default=0)
    failed_sends = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alert {self.alert_id}: {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.alert_id:
            # Generate unique alert ID
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.alert_id = f"ALT{timestamp}"
        super().save(*args, **kwargs)


class AlertDelivery(models.Model):
    """
    Track individual alert delivery attempts
    """
    DELIVERY_METHODS = [
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('ussd', 'USSD'),
        ('push', 'Push Notification'),
    ]
    
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='deliveries')
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    
    # Delivery details
    phone_number = models.CharField(max_length=20, blank=True)
    email_address = models.EmailField(blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # External service tracking
    external_message_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['alert', 'recipient', 'delivery_method']
    
    def __str__(self):
        return f"{self.alert.alert_id} -> {self.recipient.full_name} ({self.delivery_method})"


class AlertSubscription(models.Model):
    """
    User subscriptions to different alert types
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    alert_type = models.CharField(
        max_length=30, 
        choices=AlertTemplate.ALERT_TYPES
    )
    
    # Subscription preferences
    is_subscribed = models.BooleanField(default=True)
    min_severity_level = models.CharField(
        max_length=20,
        choices=AlertTemplate.SEVERITY_LEVELS,
        default='moderate',
        help_text="Minimum severity level to receive alerts"
    )
    
    # Delivery preferences
    prefer_whatsapp = models.BooleanField(default=True)
    prefer_sms = models.BooleanField(default=True)
    prefer_email = models.BooleanField(default=False)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(
        null=True, blank=True,
        help_text="Start of quiet hours (no alerts)"
    )
    quiet_hours_end = models.TimeField(
        null=True, blank=True,
        help_text="End of quiet hours"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user_profile', 'alert_type']
    
    def __str__(self):
        return f"{self.user_profile.full_name} -> {self.get_alert_type_display()}"


class AlertFeedback(models.Model):
    """
    User feedback on alerts
    """
    FEEDBACK_TYPES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
        ('too_frequent', 'Too Frequent'),
        ('too_late', 'Too Late'),
        ('incorrect', 'Incorrect Information'),
        ('suggestion', 'Suggestion'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='feedback')
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True, blank=True,
        help_text="Rating 1-5 stars"
    )
    
    comment = models.TextField(blank=True)
    
    # Follow-up actions taken
    action_taken = models.BooleanField(
        default=False,
        help_text="Did the user take action based on this alert?"
    )
    action_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['alert', 'user_profile']
    
    def __str__(self):
        return f"Feedback on {self.alert.alert_id} by {self.user_profile.full_name}"