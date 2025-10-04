from django.db import models
from django.contrib.auth.models import User
from core.models import Region, UserProfile


class FarmerProfile(models.Model):
    """
    Extended farmer profile with agricultural-specific information
    """
    FARMING_TYPES = [
        ('crop', 'Crop Farming'),
        ('livestock', 'Livestock'),
        ('mixed', 'Mixed Farming'),
        ('horticulture', 'Horticulture'),
        ('dairy', 'Dairy Farming'),
    ]
    
    IRRIGATION_TYPES = [
        ('rain_fed', 'Rain-fed'),
        ('drip', 'Drip Irrigation'),
        ('sprinkler', 'Sprinkler'),
        ('furrow', 'Furrow Irrigation'),
        ('mixed', 'Mixed Systems'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    
    # Farm details
    farm_name = models.CharField(max_length=100, blank=True)
    farming_type = models.CharField(max_length=20, choices=FARMING_TYPES, default='crop')
    irrigation_type = models.CharField(max_length=20, choices=IRRIGATION_TYPES, default='rain_fed')
    
    # Crops grown (JSON field would be better but keeping it simple)
    main_crops = models.TextField(
        blank=True,
        help_text="List main crops grown, separated by commas"
    )
    
    # Livestock information
    livestock_count = models.IntegerField(
        default=0,
        help_text="Total number of livestock (cattle, goats, sheep, etc.)"
    )
    
    # Farm coordinates (if different from user region)
    farm_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    farm_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    
    # Economic information
    annual_income_bracket = models.CharField(
        max_length=20,
        choices=[
            ('below_50k', 'Below 50,000 KSH'),
            ('50k_100k', '50,000 - 100,000 KSH'),
            ('100k_200k', '100,000 - 200,000 KSH'),
            ('200k_500k', '200,000 - 500,000 KSH'),
            ('above_500k', 'Above 500,000 KSH'),
        ],
        blank=True
    )
    
    # Experience
    years_farming = models.IntegerField(null=True, blank=True)
    
    # Technology adoption
    has_smartphone = models.BooleanField(default=False)
    uses_weather_apps = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user_profile__user__first_name']
    
    def __str__(self):
        return f"Farmer: {self.user_profile.full_name}"
    
    @property
    def crops_list(self):
        """Return list of crops"""
        if self.main_crops:
            return [crop.strip() for crop in self.main_crops.split(',')]
        return []


class FarmField(models.Model):
    """
    Individual farm fields for more granular tracking
    """
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100)
    
    # Field location
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Field details
    area_acres = models.FloatField(help_text="Field area in acres")
    soil_type = models.CharField(
        max_length=30,
        choices=[
            ('clay', 'Clay'),
            ('sandy', 'Sandy'),
            ('loam', 'Loam'),
            ('clay_loam', 'Clay Loam'),
            ('sandy_loam', 'Sandy Loam'),
            ('rocky', 'Rocky'),
        ],
        blank=True
    )
    
    # Current crop
    current_crop = models.CharField(max_length=50, blank=True)
    planting_date = models.DateField(null=True, blank=True)
    expected_harvest_date = models.DateField(null=True, blank=True)
    
    # Field status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['farmer', 'field_name']
        unique_together = ['farmer', 'field_name']
    
    def __str__(self):
        return f"{self.farmer.user_profile.full_name} - {self.field_name}"


class CropCalendar(models.Model):
    """
    Crop planting and harvesting calendar
    """
    crop_name = models.CharField(max_length=50)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    
    # Planting windows
    optimal_planting_start = models.DateField()
    optimal_planting_end = models.DateField()
    
    # Growing period
    growing_days_min = models.IntegerField(help_text="Minimum days to maturity")
    growing_days_max = models.IntegerField(help_text="Maximum days to maturity")
    
    # Water requirements
    water_requirement_mm = models.FloatField(
        help_text="Total water requirement in mm for full season"
    )
    
    # Critical growth stages
    critical_stages = models.TextField(
        blank=True,
        help_text="JSON or comma-separated critical growth stages"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['crop_name', 'region']
        unique_together = ['crop_name', 'region']
    
    def __str__(self):
        return f"{self.crop_name} - {self.region.name}"


class FarmerGroup(models.Model):
    """
    Farmer groups/cooperatives for collective communication
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    
    # Group leadership
    chairman = models.ForeignKey(
        FarmerProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='chaired_groups'
    )
    
    members = models.ManyToManyField(FarmerProfile, related_name='farmer_groups')
    
    # Group details
    registration_number = models.CharField(max_length=50, blank=True)
    formation_date = models.DateField(null=True, blank=True)
    
    # Contact information
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"
    
    @property
    def member_count(self):
        return self.members.count()