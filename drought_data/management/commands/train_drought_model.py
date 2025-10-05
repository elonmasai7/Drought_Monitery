from django.core.management.base import BaseCommand
from django.utils import timezone
from drought_data.ml_models import DroughtRiskPredictor, DroughtEarlyWarningSystem
from drought_data.tasks import fetch_ndvi_data_for_region, fetch_soil_moisture_data_for_region, fetch_weather_data_for_region
from core.models import Region
import json


class Command(BaseCommand):
    help = 'Train the drought risk prediction machine learning model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Proportion of data to use for testing (default: 0.2)'
        )
        parser.add_argument(
            '--generate-data',
            action='store_true',
            help='Generate additional sample data before training'
        )
        parser.add_argument(
            '--create-assessments',
            action='store_true',
            help='Create drought risk assessments after training'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting drought risk model training...'))
        
        # Generate additional data if requested
        if options['generate_data']:
            self.generate_sample_data()
        
        # Initialize predictor
        predictor = DroughtRiskPredictor()
        
        try:
            # Train the model
            self.stdout.write('Training machine learning model...')
            results = predictor.train_model(test_size=options['test_size'])
            
            # Display results
            self.display_training_results(results)
            
            # Create assessments if requested
            if options['create_assessments']:
                self.create_sample_assessments()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Drought risk model training completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Training failed: {str(e)}')
            )
    
    def generate_sample_data(self):
        """Generate additional sample data for training"""
        self.stdout.write('Generating additional sample data...')
        
        regions = Region.objects.filter(region_type='county')
        data_count = 0
        
        for region in regions:
            # Generate data for the last 30 days
            for days_back in range(30):
                date = (timezone.now().date() - timezone.timedelta(days=days_back))
                date_str = date.strftime('%Y-%m-%d')
                
                try:
                    # Fetch NDVI data
                    fetch_ndvi_data_for_region.delay(region.id, date_str)
                    
                    # Fetch soil moisture data
                    fetch_soil_moisture_data_for_region.delay(region.id, date_str)
                    
                    # Fetch weather data
                    fetch_weather_data_for_region.delay(region.id, date_str)
                    
                    data_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Warning: Failed to generate data for {region.name} on {date}: {e}')
                    )
        
        self.stdout.write(f'  ✓ Submitted {data_count} data generation tasks')
    
    def display_training_results(self, results):
        """Display training results in a formatted way"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('TRAINING RESULTS'))
        self.stdout.write('='*50)
        
        # Basic info
        self.stdout.write(f"Training samples: {results['training_samples']}")
        self.stdout.write(f"Test samples: {results['test_samples']}")
        
        # Training metrics
        self.stdout.write('\nTRAINING METRICS:')
        train_metrics = results['train_metrics']
        self.stdout.write(f"  RMSE: {train_metrics['rmse']:.3f}")
        self.stdout.write(f"  MAE:  {train_metrics['mae']:.3f}")
        self.stdout.write(f"  R²:   {train_metrics['r2']:.3f}")
        
        # Test metrics
        self.stdout.write('\nTEST METRICS:')
        test_metrics = results['test_metrics']
        self.stdout.write(f"  RMSE: {test_metrics['rmse']:.3f}")
        self.stdout.write(f"  MAE:  {test_metrics['mae']:.3f}")
        self.stdout.write(f"  R²:   {test_metrics['r2']:.3f}")
        
        # Cross-validation
        self.stdout.write('\nCROSS-VALIDATION:')
        self.stdout.write(f"  Mean CV Score: {results['cv_mean_score']:.3f}")
        self.stdout.write(f"  Std CV Score:  {results['cv_std_score']:.3f}")
        
        # Feature importance
        self.stdout.write('\nFEATURE IMPORTANCE:')
        importance = sorted(
            results['feature_importance'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for feature, importance_score in importance[:10]:  # Top 10 features
            self.stdout.write(f"  {feature:<25}: {importance_score:.3f}")
        
        # Model quality assessment
        self.stdout.write('\nMODEL QUALITY ASSESSMENT:')
        test_r2 = test_metrics['r2']
        if test_r2 > 0.8:
            quality = self.style.SUCCESS("Excellent")
        elif test_r2 > 0.6:
            quality = self.style.SUCCESS("Good")
        elif test_r2 > 0.4:
            quality = self.style.WARNING("Fair")
        else:
            quality = self.style.ERROR("Poor")
        
        self.stdout.write(f"  Overall Model Quality: {quality}")
        
        # Recommendations
        self.stdout.write('\nRECOMMENDATIONS:')
        if test_r2 < 0.6:
            self.stdout.write("  • Consider collecting more training data")
            self.stdout.write("  • Review feature engineering")
            self.stdout.write("  • Try different model algorithms")
        elif test_metrics['rmse'] > 20:
            self.stdout.write("  • Model predictions may have high variance")
            self.stdout.write("  • Consider regularization or ensemble methods")
        else:
            self.stdout.write("  • Model performance is acceptable")
            self.stdout.write("  • Ready for production use")
        
        self.stdout.write('='*50 + '\n')
    
    def create_sample_assessments(self):
        """Create sample drought risk assessments using the trained model"""
        self.stdout.write('Creating sample drought risk assessments...')
        
        # Initialize early warning system
        ews = DroughtEarlyWarningSystem()
        
        # Get all county regions
        regions = Region.objects.filter(region_type='county')
        
        assessments_created = 0
        for region in regions:
            try:
                # Create assessment for today
                assessment = ews.assess_drought_risk(region)
                
                self.stdout.write(
                    f"  ✓ {region.name}: {assessment.risk_level.upper()} risk "
                    f"(score: {assessment.risk_score})"
                )
                assessments_created += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Failed to create assessment for {region.name}: {e}"
                    )
                )
        
        self.stdout.write(f'  ✓ Created {assessments_created} drought risk assessments')