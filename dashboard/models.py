from django.db import models
from django.contrib.auth.models import User
from core.models import Region


class DashboardWidget(models.Model):
    """
    Configurable dashboard widgets for different user types
    """
    WIDGET_TYPES = [
        ('map', 'Map Widget'),
        ('chart', 'Chart Widget'),
        ('metric', 'Metric Widget'),
        ('alert_summary', 'Alert Summary'),
        ('weather_summary', 'Weather Summary'),
        ('risk_overview', 'Risk Overview'),
        ('farmer_stats', 'Farmer Statistics'),
    ]
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    
    # Widget configuration (JSON would be better)
    config_data = models.TextField(
        blank=True,
        help_text="JSON configuration for widget settings"
    )
    
    # Display settings
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Layout
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=4)
    height = models.IntegerField(default=3)
    
    # Permissions
    visible_to_admins = models.BooleanField(default=True)
    visible_to_farmers = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"


class UserDashboard(models.Model):
    """
    Personalized dashboard configurations for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Layout preferences
    layout_columns = models.IntegerField(default=12)
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light Theme'),
            ('dark', 'Dark Theme'),
            ('green', 'Green Theme'),
        ],
        default='green'
    )
    
    # Widget preferences
    widgets = models.ManyToManyField(
        DashboardWidget, 
        through='UserWidgetConfig',
        blank=True
    )
    
    # Default region filter
    default_region = models.ForeignKey(
        Region, 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    
    # Refresh settings
    auto_refresh_interval = models.IntegerField(
        default=300,  # 5 minutes
        help_text="Auto-refresh interval in seconds"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard for {self.user.get_full_name()}"


class UserWidgetConfig(models.Model):
    """
    User-specific widget configuration
    """
    user_dashboard = models.ForeignKey(UserDashboard, on_delete=models.CASCADE)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    
    # User-specific positioning
    position_x = models.IntegerField()
    position_y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    
    # User-specific configuration
    user_config_data = models.TextField(
        blank=True,
        help_text="User-specific JSON configuration overrides"
    )
    
    is_visible = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user_dashboard', 'widget']
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.widget.name} for {self.user_dashboard.user.username}"


class ReportTemplate(models.Model):
    """
    Templates for generating reports
    """
    REPORT_TYPES = [
        ('drought_summary', 'Drought Summary Report'),
        ('farmer_impact', 'Farmer Impact Report'),
        ('regional_analysis', 'Regional Analysis Report'),
        ('alert_performance', 'Alert Performance Report'),
        ('seasonal_outlook', 'Seasonal Outlook Report'),
    ]
    
    FORMAT_TYPES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    
    # Template configuration
    template_file = models.CharField(max_length=200, blank=True)
    default_format = models.CharField(max_length=10, choices=FORMAT_TYPES, default='pdf')
    
    # Data sources
    include_ndvi_data = models.BooleanField(default=True)
    include_soil_moisture = models.BooleanField(default=True)
    include_weather_data = models.BooleanField(default=True)
    include_farmer_data = models.BooleanField(default=False)
    include_alert_data = models.BooleanField(default=True)
    
    # Scheduling
    can_be_scheduled = models.BooleanField(default=True)
    default_schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('on_demand', 'On Demand Only'),
        ],
        default='on_demand'
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['report_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class GeneratedReport(models.Model):
    """
    Track generated reports
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Report parameters
    region_filter = models.ForeignKey(
        Region, 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    date_from = models.DateField()
    date_to = models.DateField()
    
    # Output
    file_format = models.CharField(max_length=10, choices=ReportTemplate.FORMAT_TYPES)
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Metadata
    report_title = models.CharField(max_length=200)
    report_parameters = models.TextField(
        blank=True,
        help_text="JSON parameters used for generation"
    )
    
    # Timing
    generation_started_at = models.DateTimeField(null=True, blank=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Access
    is_public = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report: {self.report_title} ({self.status})"
    
    @property
    def generation_duration(self):
        """Calculate report generation duration"""
        if self.generation_started_at and self.generation_completed_at:
            return self.generation_completed_at - self.generation_started_at
        return None


class NotificationSettings(models.Model):
    """
    User notification preferences for dashboard
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Email notifications
    email_daily_summary = models.BooleanField(default=False)
    email_weekly_report = models.BooleanField(default=False)
    email_high_risk_alerts = models.BooleanField(default=True)
    
    # In-app notifications
    show_risk_level_changes = models.BooleanField(default=True)
    show_new_data_available = models.BooleanField(default=True)
    show_system_messages = models.BooleanField(default=True)
    
    # Mobile notifications (for future mobile app)
    push_notifications_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification settings for {self.user.username}"