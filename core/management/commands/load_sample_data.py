from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Region, UserProfile
from farmers.models import FarmerProfile, CropCalendar
from alerts.models import AlertTemplate


class Command(BaseCommand):
    help = 'Load sample data for testing the drought warning system'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')
        
        # Create regions
        self.create_regions()
        
        # Create users and profiles
        self.create_users()
        
        # Create crop calendars
        self.create_crop_calendars()
        
        # Create alert templates
        self.create_alert_templates()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded sample data')
        )
    
    def create_regions(self):
        """Create sample regions for Kenya"""
        self.stdout.write('Creating regions...')
        
        # Counties in Kenya (sample)
        counties_data = [
            {'name': 'Nairobi', 'lat': -1.2921, 'lon': 36.8219, 'area': 696},
            {'name': 'Kiambu', 'lat': -1.1714, 'lon': 36.8344, 'area': 2449},
            {'name': 'Machakos', 'lat': -1.5177, 'lon': 37.2634, 'area': 5952},
            {'name': 'Kitui', 'lat': -1.3669, 'lon': 38.0106, 'area': 24385},
            {'name': 'Makueni', 'lat': -1.8040, 'lon': 37.6238, 'area': 8008},
            {'name': 'Embu', 'lat': -0.5297, 'lon': 37.4547, 'area': 2555},
            {'name': 'Meru', 'lat': 0.0500, 'lon': 37.6500, 'area': 6936},
            {'name': 'Nyeri', 'lat': -0.4167, 'lon': 36.9500, 'area': 3356},
        ]
        
        for county_data in counties_data:
            county, created = Region.objects.get_or_create(
                name=county_data['name'],
                region_type='county',
                defaults={
                    'latitude': county_data['lat'],
                    'longitude': county_data['lon'],
                    'area_sq_km': county_data['area'],
                    'population': None
                }
            )
            
            if created:
                self.stdout.write(f'  Created county: {county.name}')
                
                # Create some wards for each county
                for i in range(1, 4):
                    ward, ward_created = Region.objects.get_or_create(
                        name=f'{county.name} Ward {i}',
                        region_type='ward',
                        parent_region=county,
                        defaults={
                            'latitude': county.latitude + (i * 0.01),
                            'longitude': county.longitude + (i * 0.01),
                            'area_sq_km': county.area_sq_km / 10,
                        }
                    )
                    
                    if ward_created:
                        self.stdout.write(f'    Created ward: {ward.name}')
    
    def create_users(self):
        """Create sample users and profiles"""
        self.stdout.write('Creating users and profiles...')
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='system_admin',
            defaults={
                'email': 'admin@droughtwarning.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': False
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            
            admin_profile = UserProfile.objects.create(
                user=admin_user,
                user_type='admin',
                phone_number='+254700000001',
                preferred_language='en',
                receive_whatsapp_alerts=True,
                receive_sms_alerts=True,
                receive_email_alerts=True
            )
            self.stdout.write('  Created admin user and profile')
        
        # Create extension officer
        officer_user, created = User.objects.get_or_create(
            username='extension_officer',
            defaults={
                'email': 'officer@droughtwarning.com',
                'first_name': 'John',
                'last_name': 'Kamau',
                'is_staff': False
            }
        )
        
        if created:
            officer_user.set_password('officer123')
            officer_user.save()
            
            kitui_region = Region.objects.filter(name='Kitui', region_type='county').first()
            officer_profile = UserProfile.objects.create(
                user=officer_user,
                user_type='extension_officer',
                phone_number='+254700000002',
                region=kitui_region,
                preferred_language='en',
                receive_whatsapp_alerts=True,
                receive_sms_alerts=True,
                receive_email_alerts=True
            )
            self.stdout.write('  Created extension officer user and profile')
        
        # Create sample farmers
        farmer_data = [
            {
                'username': 'farmer_mary',
                'first_name': 'Mary',
                'last_name': 'Wanjiku',
                'phone': '+254700000010',
                'region': 'Kiambu',
                'farming_type': 'crop',
                'crops': 'Maize, Beans, Potatoes'
            },
            {
                'username': 'farmer_peter',
                'first_name': 'Peter',
                'last_name': 'Mwangi',
                'phone': '+254700000011',
                'region': 'Machakos',
                'farming_type': 'mixed',
                'crops': 'Maize, Sorghum'
            },
            {
                'username': 'farmer_grace',
                'first_name': 'Grace',
                'last_name': 'Mutindi',
                'phone': '+254700000012',
                'region': 'Kitui',
                'farming_type': 'crop',
                'crops': 'Millet, Cassava, Cowpeas'
            }
        ]
        
        for farmer_info in farmer_data:
            user, created = User.objects.get_or_create(
                username=farmer_info['username'],
                defaults={
                    'first_name': farmer_info['first_name'],
                    'last_name': farmer_info['last_name'],
                    'email': f"{farmer_info['username']}@example.com"
                }
            )
            
            if created:
                user.set_password('farmer123')
                user.save()
                
                region = Region.objects.filter(
                    name=farmer_info['region'], 
                    region_type='county'
                ).first()
                
                user_profile = UserProfile.objects.create(
                    user=user,
                    user_type='farmer',
                    phone_number=farmer_info['phone'],
                    region=region,
                    preferred_language='en',
                    receive_whatsapp_alerts=True,
                    receive_sms_alerts=True,
                    primary_crops=farmer_info['crops'],
                    farm_size_acres=5.0
                )
                
                # Create farmer profile
                farmer_profile = FarmerProfile.objects.create(
                    user_profile=user_profile,
                    farm_name=f"{farmer_info['first_name']}'s Farm",
                    farming_type=farmer_info['farming_type'],
                    irrigation_type='rain_fed',
                    main_crops=farmer_info['crops'],
                    years_farming=10,
                    has_smartphone=True
                )
                
                self.stdout.write(f"  Created farmer: {farmer_info['first_name']} {farmer_info['last_name']}")
    
    def create_crop_calendars(self):
        """Create crop calendar data"""
        self.stdout.write('Creating crop calendars...')
        
        crop_data = [
            {
                'crop': 'Maize',
                'planting_start': '2024-03-01',
                'planting_end': '2024-05-31',
                'growing_days_min': 90,
                'growing_days_max': 120,
                'water_requirement': 500
            },
            {
                'crop': 'Beans',
                'planting_start': '2024-03-15',
                'planting_end': '2024-05-15',
                'growing_days_min': 60,
                'growing_days_max': 90,
                'water_requirement': 300
            },
            {
                'crop': 'Sorghum',
                'planting_start': '2024-02-15',
                'planting_end': '2024-05-31',
                'growing_days_min': 100,
                'growing_days_max': 140,
                'water_requirement': 400
            },
            {
                'crop': 'Millet',
                'planting_start': '2024-03-01',
                'planting_end': '2024-06-30',
                'growing_days_min': 75,
                'growing_days_max': 100,
                'water_requirement': 250
            }
        ]
        
        kitui_region = Region.objects.filter(name='Kitui', region_type='county').first()
        
        for crop_info in crop_data:
            calendar, created = CropCalendar.objects.get_or_create(
                crop_name=crop_info['crop'],
                region=kitui_region,
                defaults={
                    'optimal_planting_start': crop_info['planting_start'],
                    'optimal_planting_end': crop_info['planting_end'],
                    'growing_days_min': crop_info['growing_days_min'],
                    'growing_days_max': crop_info['growing_days_max'],
                    'water_requirement_mm': crop_info['water_requirement']
                }
            )
            
            if created:
                self.stdout.write(f"  Created crop calendar for {crop_info['crop']}")
    
    def create_alert_templates(self):
        """Create alert templates"""
        self.stdout.write('Creating alert templates...')
        
        templates_data = [
            {
                'name': 'High Drought Risk Warning',
                'alert_type': 'drought_warning',
                'severity': 'high',
                'title': '⚠️ High Drought Risk Alert - {region_name}',
                'message': 'DROUGHT WARNING: {region_name} is experiencing HIGH drought risk (Risk Level: {risk_level}). Current risk score: {risk_score}. Recommendations: {recommendations}',
                'sms': 'DROUGHT ALERT: High risk in {region_name}. Score: {risk_score}. Take water conservation measures immediately.',
                'auto_send': True,
                'threshold': 70.0
            },
            {
                'name': 'Water Stress Alert',
                'alert_type': 'water_stress',
                'severity': 'moderate',
                'title': '💧 Water Stress Alert - {region_name}',
                'message': 'WATER STRESS ALERT: Soil moisture levels are low in {region_name}. Consider irrigation if available. Monitor crops closely.',
                'sms': 'WATER STRESS: Low soil moisture in {region_name}. Consider irrigation.',
                'auto_send': True,
                'threshold': 50.0
            },
            {
                'name': 'Planting Advisory',
                'alert_type': 'planting_advisory',
                'severity': 'info',
                'title': '🌱 Planting Advisory - {region_name}',
                'message': 'PLANTING ADVISORY: Current conditions in {region_name} show {risk_level} drought risk. Consider drought-resistant varieties if risk is high.',
                'sms': 'PLANTING: {risk_level} drought risk in {region_name}. Choose crops accordingly.',
                'auto_send': False,
                'threshold': None
            }
        ]
        
        for template_info in templates_data:
            template, created = AlertTemplate.objects.get_or_create(
                name=template_info['name'],
                language='en',
                defaults={
                    'alert_type': template_info['alert_type'],
                    'severity_level': template_info['severity'],
                    'title_template': template_info['title'],
                    'message_template': template_info['message'],
                    'sms_template': template_info['sms'],
                    'auto_send': template_info['auto_send'],
                    'trigger_risk_threshold': template_info['threshold'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f"  Created alert template: {template_info['name']}")