from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import Region


class Command(BaseCommand):
    help = 'Calculate drought risk assessments for all regions or a specific region'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region-id',
            type=int,
            help='Calculate risk for a specific region ID only',
        )
        parser.add_argument(
            '--region-name',
            type=str,
            help='Calculate risk for a specific region by name',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run calculation asynchronously using Celery',
        )

    def handle(self, *args, **options):
        region_id = options.get('region_id')
        region_name = options.get('region_name')
        use_async = options.get('async', False)
        
        # Resolve region name to ID if provided
        if region_name and not region_id:
            try:
                region = Region.objects.get(name__icontains=region_name, region_type='county')
                region_id = region.id
                self.stdout.write(f"Found region: {region.name} (ID: {region.id})")
            except Region.DoesNotExist:
                raise CommandError(f'Region with name "{region_name}" not found')
            except Region.MultipleObjectsReturned:
                regions = Region.objects.filter(name__icontains=region_name, region_type='county')
                self.stdout.write(self.style.ERROR(f'Multiple regions found matching "{region_name}":'))
                for r in regions:
                    self.stdout.write(f"  - {r.name} (ID: {r.id})")
                raise CommandError('Please specify the exact region name or use --region-id')
        
        self.stdout.write(self.style.SUCCESS('Starting drought risk calculation...'))
        
        if use_async:
            # Use Celery task
            
            task = calculate_daily_drought_risk.delay(region_id)
            self.stdout.write(f"Task queued with ID: {task.id}")
            self.stdout.write("Use 'celery -A drought_warning_system flower' to monitor progress")
        else:
            # Run synchronously
            try:
                from drought_data.automated_tasks import calculate_daily_drought_risk
                results = calculate_daily_drought_risk(region_id)
                
                self.stdout.write(self.style.SUCCESS('\n=== DROUGHT RISK CALCULATION RESULTS ==='))
                self.stdout.write(f"Processed regions: {results['processed_regions']}")
                self.stdout.write(f"Assessments created: {results['assessments_created']}")
                self.stdout.write(f"Errors: {results['errors']}")
                
                if results['region_results']:
                    self.stdout.write('\n=== REGION DETAILS ===')
                    for result in results['region_results']:
                        status_style = self.style.SUCCESS if result['status'] == 'success' else self.style.WARNING
                        self.stdout.write(status_style(f"\nRegion: {result['region']}"))
                        self.stdout.write(f"Status: {result['status']}")
                        
                        if result['status'] == 'success':
                            self.stdout.write(f"Risk Score: {result['risk_score']:.1f}/100")
                            self.stdout.write(f"Risk Level: {result['risk_level']}")
                            self.stdout.write(f"Assessment ID: {result['assessment_id']}")
                        else:
                            self.stdout.write(f"Message: {result.get('message', 'No details')}")
                
                if results['errors'] > 0:
                    self.stdout.write(self.style.WARNING(f'\nCompleted with {results["errors"]} errors'))
                else:
                    self.stdout.write(self.style.SUCCESS('\nCompleted successfully!'))
                    
            except Exception as e:
                raise CommandError(f'Error running drought risk calculation: {str(e)}')
