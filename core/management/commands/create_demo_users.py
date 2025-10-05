"""
Management command to create demo users for testing role-based authentication
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Region
from django.db import transaction


class Command(BaseCommand):
    help = 'Create demo users for testing role-based authentication'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create demo region if it doesn't exist
            region, created = Region.objects.get_or_create(
                name='Demo County',
                region_type='county',
                defaults={
                    'latitude': -1.286389,
                    'longitude': 36.817223,
                    'area_sq_km': 1000.0,
                    'population': 100000
                }
            )
            if created:
                self.stdout.write(f'Created demo region: {region.name}')

            # Create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'email': 'admin@droughtmonitor.com',
                    'is_staff': True,
                    'is_superuser': True
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
                    'phone_number': '+254700000001',
                    'region': region,
                    'preferred_language': 'en'
                }
            )
            if created:
                self.stdout.write(f'Created admin profile for: {admin_user.username}')

            # Create farmer user
            farmer_user, created = User.objects.get_or_create(
                username='farmer',
                defaults={
                    'first_name': 'John',
                    'last_name': 'Mwangi',
                    'email': 'farmer@droughtmonitor.com',
                    'is_staff': False,
                    'is_superuser': False
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
                    'phone_number': '+254700000002',
                    'region': region,
                    'preferred_language': 'en',
                    'farm_size_acres': 5.0,
                    'primary_crops': 'Maize, Beans, Vegetables',
                    'latitude': -1.290000,
                    'longitude': 36.820000
                }
            )
            if created:
                self.stdout.write(f'Created farmer profile for: {farmer_user.username}')

            # Create extension officer user
            officer_user, created = User.objects.get_or_create(
                username='officer',
                defaults={
                    'first_name': 'Mary',
                    'last_name': 'Wanjiku',
                    'email': 'officer@droughtmonitor.com',
                    'is_staff': False,
                    'is_superuser': False
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
                    'phone_number': '+254700000003',
                    'region': region,
                    'preferred_language': 'en'
                }
            )
            if created:
                self.stdout.write(f'Created extension officer profile for: {officer_user.username}')

            self.stdout.write(
                self.style.SUCCESS(
                    'Demo users created successfully!\n\n'
                    'Login credentials:\n'
                    '- Admin: admin / admin123\n'
                    '- Farmer: farmer / farmer123\n'
                    '- Extension Officer: officer / officer123\n'
                )
            )