from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Region
from django.db import transaction


class Command(BaseCommand):
    help = 'Create demo users for testing authentication system'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Get or create a sample region
            sample_region, created = Region.objects.get_or_create(
                name='Central Kenya',
                defaults={
                    'region_type': 'county',
                    'latitude': -0.0236,
                    'longitude': 37.9062,
                    'area_sq_km': 13191.0
                }
            )
            
            # Create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@droughtwarning.org',
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write(f'Created admin user: {admin_user.username}')
            else:
                self.stdout.write(f'Admin user already exists: {admin_user.username}')
            
            # Create admin profile
            admin_profile, created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'user_type': 'admin',
                    'phone_number': '+254-700-000-001',
                    'region': sample_region,
                }
            )
            
            # Create farmer user
            farmer_user, created = User.objects.get_or_create(
                username='farmer',
                defaults={
                    'email': 'farmer@example.com',
                    'first_name': 'John',
                    'last_name': 'Kimani',
                    'is_active': True,
                }
            )
            if created:
                farmer_user.set_password('farmer123')
                farmer_user.save()
                self.stdout.write(f'Created farmer user: {farmer_user.username}')
            else:
                self.stdout.write(f'Farmer user already exists: {farmer_user.username}')
            
            # Create farmer profile
            farmer_profile, created = UserProfile.objects.get_or_create(
                user=farmer_user,
                defaults={
                    'user_type': 'farmer',
                    'phone_number': '+254-700-000-002',
                    'region': sample_region,
                }
            )
            
            # Create extension officer user
            officer_user, created = User.objects.get_or_create(
                username='officer',
                defaults={
                    'email': 'officer@agriculture.gov.ke',
                    'first_name': 'Mary',
                    'last_name': 'Wanjiku',
                    'is_active': True,
                }
            )
            if created:
                officer_user.set_password('officer123')
                officer_user.save()
                self.stdout.write(f'Created extension officer user: {officer_user.username}')
            else:
                self.stdout.write(f'Extension officer user already exists: {officer_user.username}')
            
            # Create extension officer profile
            officer_profile, created = UserProfile.objects.get_or_create(
                user=officer_user,
                defaults={
                    'user_type': 'extension_officer',
                    'phone_number': '+254-700-000-003',
                    'region': sample_region,
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    'Demo users created successfully!\n'
                    'Login credentials:\n'
                    '- Admin: admin / admin123\n'
                    '- Farmer: farmer / farmer123\n' 
                    '- Extension Officer: officer / officer123'
                )
            )