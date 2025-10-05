from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone



class Command(BaseCommand):
    help = 'Trigger drought alerts based on recent risk assessments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=float,
            default=50.0,
            help='Minimum risk score threshold for triggering alerts (default: 50.0)',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run alert triggering asynchronously using Celery',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which alerts would be triggered without actually creating them',
        )

    def handle(self, *args, **options):
        threshold = options.get('threshold', 50.0)
        use_async = options.get('async', False)
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No alerts will be created'))
        
        self.stdout.write(self.style.SUCCESS(f'Starting drought alert triggering (threshold: {threshold})...'))
        
        if use_async and not dry_run:
            # Use Celery task
            
            task = trigger_drought_alerts.delay(threshold)
            self.stdout.write(f"Task queued with ID: {task.id}")
            self.stdout.write("Use 'celery -A drought_warning_system flower' to monitor progress")
        else:
            # Run synchronously or dry run
            try:
                if dry_run:
                    # Simulate what would happen
                    from drought_data.models import DroughtRiskAssessment
                    from datetime import timedelta
                    
                    today = timezone.now().date()
                    yesterday = today - timedelta(days=1)
                    
                    high_risk_assessments = DroughtRiskAssessment.objects.filter(
                        assessment_date__gte=yesterday,
                        risk_score__gte=threshold
                    ).select_related('region')
                    
                    self.stdout.write(f"\n=== DRY RUN RESULTS ===")
                    self.stdout.write(f"Found {high_risk_assessments.count()} high-risk assessments")
                    
                    for assessment in high_risk_assessments:
                        if assessment.risk_score >= 80:
                            severity = 'CRITICAL'
                        elif assessment.risk_score >= 65:
                            severity = 'HIGH'
                        else:
                            severity = 'MODERATE'
                        
                        self.stdout.write(f"\nRegion: {assessment.region.name}")
                        self.stdout.write(f"Risk Score: {assessment.risk_score:.1f}")
                        self.stdout.write(f"Risk Level: {assessment.risk_level}")
                        self.stdout.write(f"Alert Severity: {severity}")
                        self.stdout.write(f"Assessment Date: {assessment.assessment_date}")
                    
                    if high_risk_assessments.count() == 0:
                        self.stdout.write("No alerts would be triggered.")
                else:
                    from drought_data.automated_tasks import trigger_drought_alerts
                    results = trigger_drought_alerts(threshold)
                    
                    self.stdout.write(self.style.SUCCESS('\n=== DROUGHT ALERT TRIGGERING RESULTS ==='))
                    self.stdout.write(f"Alerts triggered: {results['alerts_triggered']}")
                    self.stdout.write(f"Errors: {results['errors']}")
                    
                    if results['alert_results']:
                        self.stdout.write('\n=== ALERT DETAILS ===')
                        for result in results['alert_results']:
                            status_style = self.style.SUCCESS if result['status'] == 'success' else self.style.WARNING
                            self.stdout.write(status_style(f"\nRegion: {result['region']}"))
                            self.stdout.write(f"Status: {result['status']}")
                            
                            if result['status'] == 'success':
                                self.stdout.write(f"Alert ID: {result['alert_id']}")
                                self.stdout.write(f"Severity: {result['severity']}")
                                self.stdout.write(f"Risk Score: {result['risk_score']:.1f}")
                            else:
                                self.stdout.write(f"Message: {result.get('message', 'No details')}")
                    
                    if results['errors'] > 0:
                        self.stdout.write(self.style.WARNING(f'\nCompleted with {results["errors"]} errors'))
                    else:
                        self.stdout.write(self.style.SUCCESS('\nCompleted successfully!'))
                        
            except Exception as e:
                raise CommandError(f'Error running drought alert triggering: {str(e)}')
