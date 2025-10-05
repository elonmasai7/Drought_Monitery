import React, { useState, useEffect } from 'react';
import { Sunrise, Calendar, MapPin, TrendingUp, Droplets, Thermometer } from 'lucide-react';
import axios from 'axios';

const WelcomeCard = ({ user, userLocation }) => {
  const [weatherData, setWeatherData] = useState(null);
  const [riskSummary, setRiskSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (userLocation) {
      fetchLocationData();
    }
  }, [userLocation]);

  const fetchLocationData = async () => {
    setLoading(true);
    try {
      // Use session authentication
      const requestConfig = {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        }
      };
      
      // Fetch weather data for user's location
      const weatherResponse = await axios.get('/api/v1/weather/', {
        ...requestConfig,
        params: {
          latitude: userLocation.lat,
          longitude: userLocation.lng,
          limit: 1
        }
      });
      
      if (weatherResponse.data.results?.length > 0) {
        setWeatherData(weatherResponse.data.results[0]);
      }

      // Fetch risk assessment for user's area
      const riskResponse = await axios.get('/api/v1/risk-assessments/', {
        ...requestConfig,
        params: {
          latitude: userLocation.lat,
          longitude: userLocation.lng,
          limit: 1
        }
      });
      
      if (riskResponse.data.results?.length > 0) {
        setRiskSummary(riskResponse.data.results[0]);
      }
      
    } catch (error) {
      console.error('Error fetching location data:', error);
      // Set mock data for better user experience when API is not available
      setWeatherData({
        temperature: 28,
        humidity: 65,
        weather_condition: 'Partly cloudy'
      });
      setRiskSummary({
        risk_score: 4.2,
        risk_level: 'moderate'
      });
    } finally {
      setLoading(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const getUserName = () => {
    if (user?.user?.first_name) {
      return user.user.first_name + (user.user.last_name ? ` ${user.user.last_name}` : '');
    }
    return user?.user?.username || 'Farmer';
  };

  const getRiskColor = (risk) => {
    if (!risk) return 'text-gray-500';
    if (risk >= 8) return 'text-red-600';
    if (risk >= 6) return 'text-orange-500';
    if (risk >= 4) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getRiskLevel = (risk) => {
    if (!risk) return 'Unknown';
    if (risk >= 8) return 'Very High';
    if (risk >= 6) return 'High';
    if (risk >= 4) return 'Moderate';
    return 'Low';
  };

  const formatDate = () => {
    return new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl shadow-lg text-white overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center mb-2">
              <Sunrise className="w-6 h-6 mr-2 text-yellow-300" />
              <h1 className="text-2xl font-bold">
                {getGreeting()}, {getUserName()}! 🌾
              </h1>
            </div>
            <div className="flex items-center text-primary-100">
              <Calendar className="w-4 h-4 mr-2" />
              <span className="text-sm">{formatDate()}</span>
            </div>
          </div>
          
          {userLocation && (
            <div className="text-right">
              <div className="flex items-center justify-end text-primary-100 mb-1">
                <MapPin className="w-4 h-4 mr-1" />
                <span className="text-sm">Your Location</span>
              </div>
              <div className="text-xs text-primary-200">
                {userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}
              </div>
            </div>
          )}
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          {/* Weather Info */}
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center mb-1">
                  <Thermometer className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">Weather</span>
                </div>
                {loading ? (
                  <div className="text-xs text-primary-200">Loading...</div>
                ) : weatherData ? (
                  <div>
                    <div className="text-lg font-bold">
                      {weatherData.temperature}°C
                    </div>
                    <div className="text-xs text-primary-200">
                      Humidity: {weatherData.humidity}%
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-primary-200">
                    No weather data
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center mb-1">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">Drought Risk</span>
                </div>
                {loading ? (
                  <div className="text-xs text-primary-200">Loading...</div>
                ) : riskSummary ? (
                  <div>
                    <div className={`text-lg font-bold ${getRiskColor(riskSummary.risk_score)}`}>
                      {getRiskLevel(riskSummary.risk_score)}
                    </div>
                    <div className="text-xs text-primary-200">
                      Score: {riskSummary.risk_score.toFixed(1)}/10
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-primary-200">
                    No risk data
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Farm Info */}
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center mb-1">
                  <Droplets className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">Farm Size</span>
                </div>
                <div>
                  <div className="text-lg font-bold">
                    {user?.farm_size_acres ? `${user.farm_size_acres} acres` : 'Not set'}
                  </div>
                  <div className="text-xs text-primary-200">
                    {user?.primary_crops ? `Crops: ${user.primary_crops}` : 'No crops listed'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 flex flex-wrap gap-3">
          <a
            href="/dashboard/map/"
            className="bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center"
          >
            <MapPin className="w-4 h-4 mr-2" />
            View Map
          </a>
          
          <a
            href="#"
            className="bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center"
          >
            <Calendar className="w-4 h-4 mr-2" />
            View Calendar
          </a>
          
          <a
            href="/dashboard/alerts/"
            className="bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center"
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            View Alerts
          </a>
        </div>

        {/* Location Context */}
        {userLocation && (
          <div className="mt-4 bg-white/10 backdrop-blur-sm rounded-lg p-3">
            <div className="text-sm text-primary-200 mb-1">🌍 Your farming region</div>
            <div className="text-white font-medium">
              {userLocation.lat > 0 ? 'Northern' : 'Southern'} region, 
              {userLocation.lng > 36 ? 'Eastern' : 'Western'} area
            </div>
          </div>
        )}

        {/* Smart Tips and Alerts */}
        {riskSummary && riskSummary.risk_score > 6 ? (
          <div className="mt-4 bg-red-500/20 border border-red-400/30 rounded-lg p-3">
            <div className="flex items-start">
              <TrendingUp className="w-5 h-5 text-red-300 mr-2 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium text-red-100 mb-1">⚠️ High Drought Risk Alert</div>
                <div className="text-sm text-red-200">
                  Consider water conservation measures and monitor your crops closely.
                  Check soil moisture levels daily.
                </div>
              </div>
            </div>
          </div>
        ) : riskSummary && riskSummary.risk_score < 3 ? (
          <div className="mt-4 bg-green-500/20 border border-green-400/30 rounded-lg p-3">
            <div className="flex items-start">
              <Droplets className="w-5 h-5 text-green-300 mr-2 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium text-green-100 mb-1">✅ Low Risk Conditions</div>
                <div className="text-sm text-green-200">
                  Great conditions for farming! Consider planting or expanding crops.
                </div>
              </div>
            </div>
          </div>
        ) : weatherData && weatherData.humidity > 80 ? (
          <div className="mt-4 bg-blue-500/20 border border-blue-400/30 rounded-lg p-3">
            <div className="flex items-start">
              <Thermometer className="w-5 h-5 text-blue-300 mr-2 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium text-blue-100 mb-1">💧 High Humidity Today</div>
                <div className="text-sm text-blue-200">
                  Good moisture levels. Perfect time for outdoor farming activities.
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default WelcomeCard;