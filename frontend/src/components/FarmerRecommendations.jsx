import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Info, 
  CheckCircle, 
  Calendar,
  Droplets,
  Thermometer,
  Leaf,
  MapPin,
  ChevronRight,
  X
} from 'lucide-react';

const FarmerRecommendations = ({ userLocation, currentUser }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dismissedRecommendations, setDismissedRecommendations] = useState([]);

  useEffect(() => {
    fetchRecommendations();
  }, [userLocation, currentUser]);

  const fetchRecommendations = async () => {
    try {
      // Simulate farmer-specific recommendations based on profile and location
      const mockRecommendations = generateRecommendations();
      setRecommendations(mockRecommendations);
      
      // Simulate weather data fetch
      const mockWeatherData = {
        temperature: 24,
        humidity: 65,
        rainfall: 8.5,
        conditions: 'Partly Cloudy'
      };
      setWeatherData(mockWeatherData);
      
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendations = () => {
    const recs = [];
    const currentMonth = new Date().getMonth() + 1;
    
    // Seasonal recommendations
    if (currentMonth >= 3 && currentMonth <= 5) {
      recs.push({
        id: 'seasonal-long-rains',
        type: 'success',
        priority: 'high',
        title: 'Long Rains Season Active',
        message: 'Optimal time for planting maize, beans, and other food crops. Ensure proper land preparation.',
        icon: 'calendar',
        actionable: true,
        actions: ['Check soil preparation', 'Plan crop rotation', 'Prepare seeds']
      });
    } else if (currentMonth >= 10 && currentMonth <= 12) {
      recs.push({
        id: 'seasonal-short-rains',
        type: 'info',
        priority: 'medium',
        title: 'Short Rains Season',
        message: 'Good time for drought-tolerant crops and vegetables. Monitor rainfall patterns.',
        icon: 'droplets',
        actionable: true,
        actions: ['Plant drought-resistant varieties', 'Monitor soil moisture']
      });
    }
    
    // Drought risk recommendations
    if (Math.random() > 0.6) { // Simulate moderate risk
      recs.push({
        id: 'drought-risk',
        type: 'warning',
        priority: 'high',
        title: 'Moderate Drought Risk Detected',
        message: 'Current conditions indicate increased drought risk. Consider water conservation measures.',
        icon: 'alert-triangle',
        actionable: true,
        actions: ['Implement water conservation', 'Consider crop insurance', 'Plan irrigation']
      });
    }
    
    // Crop-specific recommendations
    if (currentUser?.primary_crops) {
      const crops = currentUser.primary_crops.toLowerCase();
      if (crops.includes('maize')) {
        recs.push({
          id: 'maize-tips',
          type: 'success',
          priority: 'medium',
          title: 'Maize Growing Tips',
          message: 'Apply nitrogen fertilizer during vegetative stage for better yields.',
          icon: 'leaf',
          actionable: true,
          actions: ['Check fertilizer schedule', 'Monitor plant health']
        });
      }
    }
    
    // Weather-based recommendations
    if (weatherData?.rainfall < 10) {
      recs.push({
        id: 'low-rainfall',
        type: 'warning',
        priority: 'high',
        title: 'Low Rainfall Alert',
        message: 'Rainfall has been below average this month. Plan irrigation carefully.',
        icon: 'droplets',
        actionable: true,
        actions: ['Check irrigation system', 'Monitor soil moisture', 'Consider mulching']
      });
    }
    
    // Location-based recommendations
    if (!userLocation) {
      recs.push({
        id: 'location-update',
        type: 'info',
        priority: 'medium',
        title: 'Update Your Location',
        message: 'Add your farm coordinates for more accurate weather and risk predictions.',
        icon: 'map-pin',
        actionable: true,
        actions: ['Update profile', 'Enable location services']
      });
    }
    
    return recs;
  };

  const getIcon = (iconName) => {
    const icons = {
      'alert-triangle': AlertTriangle,
      'info': Info,
      'success': CheckCircle,
      'calendar': Calendar,
      'droplets': Droplets,
      'thermometer': Thermometer,
      'leaf': Leaf,
      'map-pin': MapPin
    };
    return icons[iconName] || Info;
  };

  const getTypeColor = (type) => {
    const colors = {
      'warning': 'border-l-orange-500 bg-orange-50',
      'success': 'border-l-green-500 bg-green-50',
      'info': 'border-l-blue-500 bg-blue-50',
      'error': 'border-l-red-500 bg-red-50'
    };
    return colors[type] || colors.info;
  };

  const getIconColor = (type) => {
    const colors = {
      'warning': 'text-orange-600',
      'success': 'text-green-600',
      'info': 'text-blue-600',
      'error': 'text-red-600'
    };
    return colors[type] || colors.info;
  };

  const dismissRecommendation = (recommendationId) => {
    setDismissedRecommendations(prev => [...prev, recommendationId]);
  };

  const visibleRecommendations = recommendations.filter(
    rec => !dismissedRecommendations.includes(rec.id)
  );

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-300 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-300 rounded"></div>
            <div className="h-3 bg-gray-300 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Personalized Recommendations
            </h2>
            <p className="text-sm text-gray-600">
              Based on your location, crops, and current conditions
            </p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Leaf className="w-4 h-4" />
            <span>Updated now</span>
          </div>
        </div>
      </div>

      <div className="p-6">
        {visibleRecommendations.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              All Good!
            </h3>
            <p className="text-gray-600">
              No urgent recommendations at this time. Keep monitoring your crops.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {visibleRecommendations.map((recommendation) => {
              const IconComponent = getIcon(recommendation.icon);
              return (
                <div
                  key={recommendation.id}
                  className={`border-l-4 p-4 rounded-r-lg ${getTypeColor(recommendation.type)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className={`flex-shrink-0 ${getIconColor(recommendation.type)}`}>
                        <IconComponent className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="text-sm font-medium text-gray-900">
                            {recommendation.title}
                          </h3>
                          {recommendation.priority === 'high' && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              High Priority
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-700 mb-3">
                          {recommendation.message}
                        </p>
                        
                        {recommendation.actionable && recommendation.actions && (
                          <div className="space-y-1">
                            <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                              Recommended Actions:
                            </p>
                            <ul className="space-y-1">
                              {recommendation.actions.map((action, index) => (
                                <li key={index} className="flex items-center text-xs text-gray-600">
                                  <ChevronRight className="w-3 h-3 mr-1 text-gray-400" />
                                  {action}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => dismissRecommendation(recommendation.id)}
                      className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                      title="Dismiss recommendation"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Weather Summary */}
        {weatherData && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Current Conditions</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <Thermometer className="w-4 h-4 text-red-500" />
                <span className="text-gray-600">Temp:</span>
                <span className="font-medium">{weatherData.temperature}°C</span>
              </div>
              <div className="flex items-center space-x-2">
                <Droplets className="w-4 h-4 text-blue-500" />
                <span className="text-gray-600">Humidity:</span>
                <span className="font-medium">{weatherData.humidity}%</span>
              </div>
              <div className="flex items-center space-x-2">
                <Droplets className="w-4 h-4 text-blue-600" />
                <span className="text-gray-600">Rainfall:</span>
                <span className="font-medium">{weatherData.rainfall}mm</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-gray-600">Conditions:</span>
                <span className="font-medium">{weatherData.conditions}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 

export default FarmerRecommendations;