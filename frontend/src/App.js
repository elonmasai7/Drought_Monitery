import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navbar from './components/Navbar';
import WelcomeCard from './components/WelcomeCard';
import MapView from './components/MapView';
import AlertsPanel from './components/AlertsPanel';
import LocationManager from './components/LocationManager';
import RoleBasedQuickActions from './components/RoleBasedQuickActions';
import FarmerRecommendations from './components/FarmerRecommendations';
import './App.css';

// Configure axios defaults
axios.defaults.baseURL = window.location.origin;
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

function App() {
  const [user, setUser] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard'); // dashboard, map, alerts

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      await fetchUserProfile();
      setLoading(false);
    } catch (error) {
      console.error('Failed to initialize app:', error);
      setError('Failed to load user data');
      setLoading(false);
    }
  };

  const fetchUserProfile = async () => {
    try {
      // Use session authentication
      const response = await axios.get('/api/v1/users/me/', {
        headers: {
          'X-CSRFToken': window.csrfToken,
        },
        withCredentials: true
      });
      
      setUser(response.data);
      
      // Set user location if available
      if (response.data.latitude && response.data.longitude) {
        setUserLocation({
          lat: parseFloat(response.data.latitude),
          lng: parseFloat(response.data.longitude)
        });
      }
      
    } catch (error) {
      console.error('Error fetching user profile:', error);
      if (error.response?.status === 401) {
        // Unauthorized, redirect to login
        localStorage.clear();
        window.location.href = '/dashboard/login/';
      }
    }
  };

  const handleLocationUpdate = (location) => {
    setUserLocation(location);
  };

  const handleLogout = () => {
    setUser(null);
    setUserLocation(null);
    localStorage.clear();
    window.location.href = '/dashboard/login/';
  };

  const handleAlertsCountUpdate = (count) => {
    setUnreadAlertsCount(count);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Dashboard</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-primary-500 hover:bg-primary-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar 
        user={user} 
        onLogout={handleLogout} 
        unreadAlertsCount={unreadAlertsCount}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Welcome Section */}
        <div className="mb-6">
          <WelcomeCard user={user} userLocation={userLocation} />
        </div>

        {/* Role-based Quick Actions */}
        <div className="mb-6">
          <RoleBasedQuickActions userRole={user?.user_type} currentUser={user} />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Location Manager */}
          <div className="lg:col-span-1">
            <div className="space-y-6">
              <LocationManager 
                onLocationUpdate={handleLocationUpdate}
                initialLocation={userLocation}
              />
              
              {/* View Toggle Buttons */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <h3 className="font-semibold text-gray-800 mb-3">Quick Navigation</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => setCurrentView('dashboard')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      currentView === 'dashboard'
                        ? 'bg-primary-100 text-primary-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    🏠 Dashboard
                  </button>
                  <button
                    onClick={() => setCurrentView('map')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      currentView === 'map'
                        ? 'bg-primary-100 text-primary-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    🗺️ Heat Maps
                  </button>
                  <button
                    onClick={() => setCurrentView('alerts')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      currentView === 'alerts'
                        ? 'bg-primary-100 text-primary-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    🚨 Alerts
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2">
            {currentView === 'dashboard' && (
              <div className="space-y-6">
                {/* Farm Overview Metrics */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Farm Overview</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="metric-card">
                      <div className="text-3xl font-bold text-green-600 mb-2">Good</div>
                      <div className="text-gray-600">Crop Health</div>
                    </div>
                    <div className="metric-card">
                      <div className="text-3xl font-bold text-blue-600 mb-2">65%</div>
                      <div className="text-gray-600">Soil Moisture</div>
                    </div>
                    <div className="metric-card">
                      <div className="text-3xl font-bold text-yellow-600 mb-2">Medium</div>
                      <div className="text-gray-600">Drought Risk</div>
                    </div>
                    <div className="metric-card">
                      <div className="text-3xl font-bold text-purple-600 mb-2">7.2</div>
                      <div className="text-gray-600">Soil pH</div>
                    </div>
                  </div>
                  
                  {/* Quick Map Preview */}
                  <div className="mb-4">
                    <h3 className="font-semibold text-gray-800 mb-3">Location Map</h3>
                    <div className="h-64">
                      <MapView 
                        userLocation={userLocation} 
                        onLocationUpdate={handleLocationUpdate}
                      />
                    </div>
                  </div>
                </div>

                {/* Farmer-specific Recommendations (only for farmers) */}
                {user?.user_type === 'farmer' && (
                  <FarmerRecommendations 
                    userLocation={userLocation}
                    currentUser={user}
                  />
                )}
              </div>
            )}

            {currentView === 'map' && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Regional Heat Maps</h2>
                <MapView 
                  userLocation={userLocation} 
                  onLocationUpdate={handleLocationUpdate}
                />
              </div>
            )}

            {currentView === 'alerts' && (
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b">
                  <h2 className="text-xl font-bold text-gray-800">Drought & Agricultural Alerts</h2>
                </div>
                <div className="h-96">
                  <AlertsPanel 
                    userLocation={userLocation}
                    isVisible={true}
                    onUnreadCountChange={handleAlertsCountUpdate}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Alerts Panel */}
          <div className="lg:col-span-1">
            <div className="h-96">
              <AlertsPanel 
                userLocation={userLocation}
                isVisible={true}
                onUnreadCountChange={handleAlertsCountUpdate}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-600">
            <p>&copy; 2025 Drought Warning System. Built for farmers, by farmers. 🌾</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
