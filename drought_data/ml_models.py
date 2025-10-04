"""
Machine Learning models for drought risk prediction using scikit-learn
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from django.utils import timezone
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline
import joblib
import os
import logging
from django.conf import settings

from .models import NDVIData, SoilMoistureData, WeatherData, DroughtRiskAssessment
from core.models import Region

logger = logging.getLogger(__name__)


class DroughtRiskPredictor:
    """
    Machine Learning model for predicting drought risk using various environmental indicators
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'ndvi_value', 'soil_moisture_percent', 'temperature_avg',
            'precipitation_mm', 'humidity_percent', 'wind_speed_kmh',
            'days_since_last_rain', 'temp_trend_7day', 'ndvi_trend_7day',
            'moisture_trend_7day', 'season_numeric', 'region_aridity_index'
        ]
        self.model_path = os.path.join(settings.BASE_DIR, 'models', 'drought_risk_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'models', 'drought_risk_scaler.pkl')
        
        # Ensure models directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def prepare_training_data(self, regions: List[Region] = None) -> pd.DataFrame:
        """
        Prepare training data by combining NDVI, soil moisture, and weather data
        
        Args:
            regions: List of regions to include (if None, includes all regions)
            
        Returns:
            Prepared DataFrame for training
        """
        # Get all regions if none specified
        if regions is None:
            regions = Region.objects.filter(region_type='county')
        
        data_rows = []
        
        for region in regions:
            # Get data for the last 6 months
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=180)
            
            # Get NDVI data
            ndvi_data = NDVIData.objects.filter(
                region=region,
                date__range=[start_date, end_date]
            ).order_by('date')
            
            # Get soil moisture data
            soil_data = SoilMoistureData.objects.filter(
                region=region,
                date__range=[start_date, end_date]
            ).order_by('date')
            
            # Get weather data
            weather_data = WeatherData.objects.filter(
                region=region,
                date__range=[start_date, end_date]
            ).order_by('date')
            
            # Get existing risk assessments for training
            risk_data = DroughtRiskAssessment.objects.filter(
                region=region,
                assessment_date__range=[start_date, end_date]
            ).order_by('assessment_date')
            
            # Create date-based mapping
            ndvi_by_date = {n.date: n for n in ndvi_data}
            soil_by_date = {s.date: s for s in soil_data}
            weather_by_date = {w.date: w for w in weather_data}
            risk_by_date = {r.assessment_date: r for r in risk_data}
            
            # Generate training samples
            for date in pd.date_range(start_date, end_date, freq='D'):
                date_obj = date.date()
                
                # Skip if we don't have minimum required data
                if (date_obj not in ndvi_by_date or 
                    date_obj not in soil_by_date or 
                    date_obj not in weather_by_date):
                    continue
                
                # Get data for this date
                ndvi = ndvi_by_date[date_obj]
                soil = soil_by_date[date_obj]
                weather = weather_by_date[date_obj]
                
                # Calculate features
                features = self._calculate_features(
                    region, date_obj, ndvi, soil, weather,
                    ndvi_by_date, soil_by_date, weather_by_date
                )
                
                # Use existing risk assessment if available, otherwise calculate target
                if date_obj in risk_by_date:
                    target_risk = risk_by_date[date_obj].risk_score
                else:
                    # Calculate risk based on existing logic for training
                    target_risk = self._calculate_baseline_risk(ndvi, soil, weather)
                
                # Add to training data
                row = features.copy()
                row['target_risk_score'] = target_risk
                row['region_id'] = region.id
                row['date'] = date_obj
                data_rows.append(row)
        
        if not data_rows:
            logger.warning("No training data available")
            return pd.DataFrame()
        
        df = pd.DataFrame(data_rows)
        logger.info(f"Prepared {len(df)} training samples from {len(regions)} regions")
        return df
    
    def _calculate_features(self, region: Region, date: datetime, 
                          ndvi: NDVIData, soil: SoilMoistureData, weather: WeatherData,
                          ndvi_by_date: Dict, soil_by_date: Dict, weather_by_date: Dict) -> Dict[str, float]:
        """
        Calculate features for ML model
        """
        features = {}
        
        # Basic indicators
        features['ndvi_value'] = ndvi.ndvi_value
        features['soil_moisture_percent'] = soil.moisture_percent
        features['temperature_avg'] = weather.temperature_avg
        features['precipitation_mm'] = weather.precipitation_mm
        features['humidity_percent'] = weather.humidity_percent
        features['wind_speed_kmh'] = weather.wind_speed_kmh
        
        # Days since last significant rain (>5mm)
        days_since_rain = self._days_since_last_rain(date, weather_by_date)
        features['days_since_last_rain'] = days_since_rain
        
        # Calculate trends (7-day)
        features['temp_trend_7day'] = self._calculate_trend(
            date, weather_by_date, 'temperature_avg', days=7
        )
        features['ndvi_trend_7day'] = self._calculate_trend(
            date, ndvi_by_date, 'ndvi_value', days=7
        )
        features['moisture_trend_7day'] = self._calculate_trend(
            date, soil_by_date, 'moisture_percent', days=7
        )
        
        # Seasonal information
        features['season_numeric'] = self._get_season_numeric(date)
        
        # Regional aridity index (simplified)
        features['region_aridity_index'] = self._get_region_aridity_index(region)
        
        return features
    
    def _days_since_last_rain(self, date: datetime, weather_by_date: Dict) -> int:
        """Calculate days since last significant rainfall"""
        days = 0
        current_date = date
        
        for i in range(30):  # Look back up to 30 days
            if current_date in weather_by_date:
                if weather_by_date[current_date].precipitation_mm > 5.0:
                    return days
            days += 1
            current_date = current_date - timedelta(days=1)
        
        return 30  # Cap at 30 days
    
    def _calculate_trend(self, date: datetime, data_by_date: Dict, 
                        field: str, days: int = 7) -> float:
        """Calculate trend over specified number of days"""
        values = []
        current_date = date
        
        for i in range(days):
            if current_date in data_by_date:
                if hasattr(data_by_date[current_date], field):
                    values.append(getattr(data_by_date[current_date], field))
            current_date = current_date - timedelta(days=1)
        
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        x = np.arange(len(values))
        y = np.array(values[::-1])  # Reverse to get chronological order
        
        if np.std(y) == 0:
            return 0.0
        
        correlation = np.corrcoef(x, y)[0, 1]
        return correlation if not np.isnan(correlation) else 0.0
    
    def _get_season_numeric(self, date: datetime) -> float:
        """Convert date to seasonal numeric value (0-1)"""
        day_of_year = date.timetuple().tm_yday
        # Convert to seasonal cycle (0-1, where 0.5 is mid-year)
        return np.sin(2 * np.pi * day_of_year / 365.25) * 0.5 + 0.5
    
    def _get_region_aridity_index(self, region: Region) -> float:
        """Get simplified aridity index for region"""
        # Simplified aridity index based on region characteristics
        # In a real implementation, this would use actual climate data
        
        aridity_map = {
            'Nairobi': 0.3,    # Semi-arid
            'Kiambu': 0.5,     # Sub-humid
            'Machakos': 0.2,   # Semi-arid
            'Kitui': 0.1,      # Arid
            'Makueni': 0.15,   # Semi-arid
            'Embu': 0.6,       # Humid
            'Meru': 0.7,       # Humid
            'Nyeri': 0.8,      # Humid
        }
        
        return aridity_map.get(region.name, 0.3)  # Default to semi-arid
    
    def _calculate_baseline_risk(self, ndvi: NDVIData, soil: SoilMoistureData, 
                               weather: WeatherData) -> float:
        """
        Calculate baseline drought risk for training when no assessment exists
        This uses the same logic as the model to create training targets
        """
        # NDVI component (40% weight)
        if ndvi.ndvi_value < 0.2:
            ndvi_score = 90
        elif ndvi.ndvi_value < 0.3:
            ndvi_score = 70
        elif ndvi.ndvi_value < 0.5:
            ndvi_score = 50
        elif ndvi.ndvi_value < 0.7:
            ndvi_score = 30
        else:
            ndvi_score = 10
        
        # Soil moisture component (35% weight)
        if soil.moisture_percent < 20:
            moisture_score = 95
        elif soil.moisture_percent < 30:
            moisture_score = 80
        elif soil.moisture_percent < 40:
            moisture_score = 60
        elif soil.moisture_percent < 50:
            moisture_score = 40
        else:
            moisture_score = 20
        
        # Weather component (25% weight)
        weather_score = 0
        if weather.precipitation_mm < 1:
            weather_score += 30
        elif weather.precipitation_mm < 5:
            weather_score += 20
        else:
            weather_score += 5
        
        if weather.temperature_avg > 35:
            weather_score += 25
        elif weather.temperature_avg > 30:
            weather_score += 15
        else:
            weather_score += 5
        
        if weather.humidity_percent < 40:
            weather_score += 20
        elif weather.humidity_percent < 60:
            weather_score += 10
        else:
            weather_score += 0
        
        # Combine scores
        risk_score = (ndvi_score * 0.4 + moisture_score * 0.35 + weather_score * 0.25)
        return min(100, max(0, risk_score))
    
    def train_model(self, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
        """
        Train the drought risk prediction model
        
        Args:
            test_size: Proportion of data to use for testing
            random_state: Random state for reproducibility
            
        Returns:
            Training results and metrics
        """
        logger.info("Starting model training...")
        
        # Prepare training data
        df = self.prepare_training_data()
        
        if df.empty:
            raise ValueError("No training data available")
        
        # Prepare features and target
        X = df[self.feature_columns]
        y = df['target_risk_score']
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Create model pipeline
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state
            ))
        ])
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Make predictions
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        # Calculate metrics
        train_metrics = {
            'mse': mean_squared_error(y_train, y_pred_train),
            'rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'mae': mean_absolute_error(y_train, y_pred_train),
            'r2': r2_score(y_train, y_pred_train)
        }
        
        test_metrics = {
            'mse': mean_squared_error(y_test, y_pred_test),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'mae': mean_absolute_error(y_test, y_pred_test),
            'r2': r2_score(y_test, y_pred_test)
        }
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5)
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_columns,
            self.model.named_steps['regressor'].feature_importances_
        ))
        
        # Save model
        self.save_model()
        self.is_trained = True
        
        results = {
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'cv_mean_score': cv_scores.mean(),
            'cv_std_score': cv_scores.std(),
            'feature_importance': feature_importance
        }
        
        logger.info(f"Model training completed. Test R²: {test_metrics['r2']:.3f}")
        return results
    
    def predict_risk(self, region: Region, date: datetime = None) -> Dict[str, Any]:
        """
        Predict drought risk for a specific region and date
        
        Args:
            region: Region to predict for
            date: Date for prediction (defaults to today)
            
        Returns:
            Prediction results
        """
        if not self.is_trained and not self.load_model():
            raise ValueError("Model is not trained. Please train the model first.")
        
        if date is None:
            date = timezone.now().date()
        
        # Get required data
        try:
            ndvi = NDVIData.objects.filter(region=region, date=date).latest('created_at')
            soil = SoilMoistureData.objects.filter(region=region, date=date).latest('created_at')
            weather = WeatherData.objects.filter(region=region, date=date).latest('created_at')
        except (NDVIData.DoesNotExist, SoilMoistureData.DoesNotExist, WeatherData.DoesNotExist):
            raise ValueError(f"Required data not available for {region.name} on {date}")
        
        # Get historical data for trend calculations
        start_date = date - timedelta(days=30)
        ndvi_data = NDVIData.objects.filter(
            region=region, date__range=[start_date, date]
        ).order_by('date')
        soil_data = SoilMoistureData.objects.filter(
            region=region, date__range=[start_date, date]
        ).order_by('date')
        weather_data = WeatherData.objects.filter(
            region=region, date__range=[start_date, date]
        ).order_by('date')
        
        # Create mappings
        ndvi_by_date = {n.date: n for n in ndvi_data}
        soil_by_date = {s.date: s for s in soil_data}
        weather_by_date = {w.date: w for w in weather_data}
        
        # Calculate features
        features = self._calculate_features(
            region, date, ndvi, soil, weather,
            ndvi_by_date, soil_by_date, weather_by_date
        )
        
        # Prepare features for prediction
        X = pd.DataFrame([features])[self.feature_columns]
        X = X.fillna(X.mean())
        
        # Make prediction
        risk_score = self.model.predict(X)[0]
        risk_score = min(100, max(0, risk_score))  # Clamp to 0-100
        
        # Determine risk level (matching model choices)
        if risk_score >= 80:
            risk_level = 'extreme'
        elif risk_score >= 65:
            risk_level = 'very_high'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 35:
            risk_level = 'moderate'
        elif risk_score >= 20:
            risk_level = 'low'
        else:
            risk_level = 'very_low'
        
        return {
            'region': region.name,
            'date': date,
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'features_used': features,
            'model_version': 'v1.0'
        }
    
    def save_model(self) -> bool:
        """Save trained model to disk"""
        try:
            joblib.dump(self.model, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def load_model(self) -> bool:
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info(f"Model loaded from {self.model_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
        
        return False


class DroughtEarlyWarningSystem:
    """
    Early warning system that combines ML predictions with rule-based alerts
    """
    
    def __init__(self):
        self.predictor = DroughtRiskPredictor()
        
    def assess_drought_risk(self, region: Region, date: datetime = None) -> DroughtRiskAssessment:
        """
        Assess drought risk for a region using ML model and create/update assessment
        
        Args:
            region: Region to assess
            date: Date for assessment (defaults to today)
            
        Returns:
            DroughtRiskAssessment object
        """
        if date is None:
            date = timezone.now().date()
        
        try:
            # Get ML prediction
            prediction = self.predictor.predict_risk(region, date)
            risk_score = prediction['risk_score']
            risk_level = prediction['risk_level']
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_level, prediction)
            
            # Calculate component scores from the prediction features
            features = prediction['features_used']
            
            # Calculate component scores (simplified)
            ndvi_component = (1 - features.get('ndvi_value', 0.5)) * 100
            moisture_component = max(0, (50 - features.get('soil_moisture_percent', 50)) * 2)
            weather_component = min(100, features.get('temperature_avg', 25) * 2 + 
                                  max(0, 14 - features.get('days_since_last_rain', 0)) * 5)
            
            # Create or update assessment
            assessment, created = DroughtRiskAssessment.objects.update_or_create(
                region=region,
                assessment_date=date,
                defaults={
                    'risk_score': risk_score,
                    'risk_level': risk_level,
                    'ndvi_component_score': max(0, min(100, ndvi_component)),
                    'soil_moisture_component_score': max(0, min(100, moisture_component)),
                    'weather_component_score': max(0, min(100, weather_component)),
                    'confidence_score': 0.8,  # Default confidence for ML model
                    'recommended_actions': recommendations,
                    'model_version': prediction['model_version']
                }
            )
            
            logger.info(
                f"{'Created' if created else 'Updated'} drought assessment for {region.name}: "
                f"{risk_level} risk (score: {risk_score})"
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to assess drought risk for {region.name}: {e}")
            # Fallback to rule-based assessment
            return self._fallback_assessment(region, date)
    
    def _generate_recommendations(self, risk_level: str, prediction: Dict) -> str:
        """Generate recommendations based on risk level and features"""
        features = prediction['features_used']
        recommendations = []
        
        if risk_level == 'extreme':
            recommendations.extend([
                "URGENT: Implement emergency water conservation measures",
                "Consider livestock destocking if applicable",
                "Activate drought emergency response protocols",
                "Distribute water supplies to affected communities"
            ])
        elif risk_level == 'very_high':
            recommendations.extend([
                "Implement strict water conservation measures",
                "Monitor livestock health very closely",
                "Prepare emergency response protocols",
                "Consider emergency water supply distribution"
            ])
        elif risk_level == 'high':
            recommendations.extend([
                "Implement water conservation measures",
                "Monitor livestock health closely",
                "Prepare emergency water supplies",
                "Consider early harvest of vulnerable crops"
            ])
        elif risk_level == 'moderate':
            recommendations.extend([
                "Monitor water levels and usage",
                "Prepare drought contingency plans",
                "Consider drought-resistant crop varieties for next season"
            ])
        elif risk_level == 'low':
            recommendations.extend([
                "Continue normal agricultural activities",
                "Monitor weather conditions regularly"
            ])
        else:  # very_low
            recommendations.extend([
                "No immediate drought concerns",
                "Maintain regular monitoring"
            ])
        
        # Add feature-specific recommendations
        if features.get('days_since_last_rain', 0) > 14:
            recommendations.append("Long dry period detected - prioritize irrigation")
        
        if features.get('ndvi_trend_7day', 0) < -0.3:
            recommendations.append("Vegetation stress detected - monitor crop health")
        
        if features.get('soil_moisture_percent', 50) < 25:
            recommendations.append("Low soil moisture - consider supplemental irrigation")
        
        return " | ".join(recommendations)
    
    def _fallback_assessment(self, region: Region, date: datetime) -> DroughtRiskAssessment:
        """Fallback rule-based assessment when ML model fails"""
        try:
            # Use existing rule-based logic from the model
            ndvi = NDVIData.objects.filter(region=region, date=date).latest('created_at')
            soil = SoilMoistureData.objects.filter(region=region, date=date).latest('created_at')
            weather = WeatherData.objects.filter(region=region, date=date).latest('created_at')
            
            # Calculate risk using simple rules
            risk_score = self.predictor._calculate_baseline_risk(ndvi, soil, weather)
            
            if risk_score >= 80:
                risk_level = 'extreme'
            elif risk_score >= 65:
                risk_level = 'very_high'
            elif risk_score >= 50:
                risk_level = 'high'
            elif risk_score >= 35:
                risk_level = 'moderate'
            elif risk_score >= 20:
                risk_level = 'low'
            else:
                risk_level = 'very_low'
            
            # Calculate component scores for fallback
            ndvi_component = (1 - ndvi.ndvi_value) * 100
            moisture_component = max(0, (50 - soil.moisture_percent) * 2)
            weather_component = min(100, weather.temperature_avg * 2)
            
            assessment, _ = DroughtRiskAssessment.objects.update_or_create(
                region=region,
                assessment_date=date,
                defaults={
                    'risk_score': risk_score,
                    'risk_level': risk_level,
                    'ndvi_component_score': max(0, min(100, ndvi_component)),
                    'soil_moisture_component_score': max(0, min(100, moisture_component)),
                    'weather_component_score': max(0, min(100, weather_component)),
                    'confidence_score': 0.6,  # Lower confidence for rule-based
                    'recommended_actions': "Rule-based assessment - ML model unavailable",
                    'model_version': 'fallback_v1.0'
                }
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Fallback assessment also failed: {e}")
            raise