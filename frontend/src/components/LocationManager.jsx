import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  MapPin, 
  Navigation, 
  AlertCircle, 
  CheckCircle, 
  X, 
  Edit3,
  Loader
} from 'lucide-react';

const LocationManager = ({ onLocationUpdate, initialLocation }) => {
  const [location, setLocation] = useState(initialLocation);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const [error, setError] = useState(null);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualCoords, setManualCoords] = useState({ lat: '', lng: '' });
  const [permissionStatus, setPermissionStatus] = useState('unknown'); // unknown, granted, denied, prompt
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    checkLocationPermission();
    if (!initialLocation) {
      requestLocationOnMount();
    }
  }, []);

  const checkLocationPermission = async () => {
    if ('permissions' in navigator) {
      try {
        const permission = await navigator.permissions.query({ name: 'geolocation' });
        setPermissionStatus(permission.state);
        
        permission.addEventListener('change', () => {
          setPermissionStatus(permission.state);
        });
      } catch (error) {
        console.log('Permission API not supported');
      }
    }
  };

  const requestLocationOnMount = () => {
    // Auto-request location on component mount if no location is set
    if ('geolocation' in navigator && !location) {
      // Don't show loading immediately, wait a bit
      setTimeout(() => {
        requestLocation(false);
      }, 1000);
    }
  };

  const requestLocation = (showLoading = true) => {
    if (!('geolocation' in navigator)) {
      setError('Geolocation is not supported by this browser.');
      setShowManualEntry(true);
      return;
    }

    if (showLoading) {
      setIsGettingLocation(true);
    }
    setError(null);

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000 // Cache for 1 minute
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        const newLocation = { lat: latitude, lng: longitude };
        
        setLocation(newLocation);
        setIsGettingLocation(false);
        setError(null);
        setShowManualEntry(false);
        
        // Send to parent component
        if (onLocationUpdate) {
          onLocationUpdate(newLocation);
        }
        
        // Send to backend
        saveLocationToBackend(newLocation);
      },
      (error) => {
        setIsGettingLocation(false);
        let errorMessage = 'Unable to get your location.';
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location access denied. Please enable location services or enter coordinates manually.';
            setPermissionStatus('denied');
            setShowManualEntry(true);
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information is unavailable. Please try again or enter coordinates manually.';
            setShowManualEntry(true);
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out. Please try again or enter coordinates manually.';
            setShowManualEntry(true);
            break;
          default:
            errorMessage = 'An unknown error occurred while getting location.';
            setShowManualEntry(true);
            break;
        }
        
        setError(errorMessage);
      },
      options
    );
  };

  const saveLocationToBackend = async (locationData) => {
    setIsSaving(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('/core/api/location/', {
        latitude: locationData.lat,
        longitude: locationData.lng
      }, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      if (response.data.success) {
        console.log('Location saved successfully');
      }
    } catch (error) {
      console.error('Error saving location:', error);
      // Don't show error to user for backend save failures
    } finally {
      setIsSaving(false);
    }
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    
    const lat = parseFloat(manualCoords.lat);
    const lng = parseFloat(manualCoords.lng);
    
    if (isNaN(lat) || isNaN(lng)) {
      setError('Please enter valid coordinates.');
      return;
    }
    
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      setError('Please enter valid coordinates (latitude: -90 to 90, longitude: -180 to 180).');
      return;
    }
    
    const newLocation = { lat, lng };
    setLocation(newLocation);
    setError(null);
    setShowManualEntry(false);
    
    if (onLocationUpdate) {
      onLocationUpdate(newLocation);
    }
    
    saveLocationToBackend(newLocation);
  };

  const getLocationStatusColor = () => {
    if (location) return 'text-green-600';
    if (error) return 'text-red-600';
    if (isGettingLocation) return 'text-blue-600';
    return 'text-gray-600';
  };

  const getLocationStatusIcon = () => {
    if (location) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (error) return <AlertCircle className="w-5 h-5 text-red-600" />;
    if (isGettingLocation) return <Loader className="w-5 h-5 text-blue-600 animate-spin" />;
    return <MapPin className="w-5 h-5 text-gray-600" />;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          {getLocationStatusIcon()}
          <h3 className={`ml-2 font-semibold ${getLocationStatusColor()}`}>
            Location Services
          </h3>
          {isSaving && (
            <Loader className="w-4 h-4 ml-2 animate-spin text-gray-400" />
          )}
        </div>
        
        {location && (
          <button
            onClick={() => setShowManualEntry(!showManualEntry)}
            className="text-gray-500 hover:text-gray-700 p-1"
            title="Edit location manually"
          >
            <Edit3 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Current Location Display */}
      {location && !showManualEntry && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-800">Location Set</p>
              <p className="text-xs text-green-600">
                {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
              </p>
            </div>
            <button
              onClick={() => requestLocation()}
              disabled={isGettingLocation}
              className="text-green-600 hover:text-green-800 text-sm underline disabled:opacity-50"
            >
              Update
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-red-800">{error}</p>
              {permissionStatus === 'denied' && (
                <p className="text-xs text-red-600 mt-1">
                  To enable location access, please check your browser settings and allow location permissions for this site.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Manual Entry Form */}
      {showManualEntry && (
        <div className="border border-gray-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-800">Enter Coordinates Manually</h4>
            <button
              onClick={() => setShowManualEntry(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <form onSubmit={handleManualSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  step="any"
                  value={manualCoords.lat}
                  onChange={(e) => setManualCoords(prev => ({ ...prev, lat: e.target.value }))}
                  placeholder="-1.2921"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  step="any"
                  value={manualCoords.lng}
                  onChange={(e) => setManualCoords(prev => ({ ...prev, lng: e.target.value }))}
                  placeholder="36.8219"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>
            </div>
            
            <button
              type="submit"
              className="w-full bg-primary-500 hover:bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium transition-colors"
            >
              Set Location
            </button>
          </form>
          
          <p className="text-xs text-gray-500 mt-2">
            Tip: You can find your coordinates using Google Maps or similar services.
          </p>
        </div>
      )}

      {/* Action Buttons */}
      {!location && !showManualEntry && (
        <div className="space-y-2">
          <button
            onClick={() => requestLocation()}
            disabled={isGettingLocation}
            className="w-full bg-primary-500 hover:bg-primary-600 disabled:bg-gray-400 text-white py-2 px-4 rounded-md font-medium transition-colors flex items-center justify-center"
          >
            <Navigation className="w-4 h-4 mr-2" />
            {isGettingLocation ? 'Getting Location...' : 'Get My Location'}
          </button>
          
          <button
            onClick={() => setShowManualEntry(true)}
            className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-md font-medium transition-colors flex items-center justify-center"
          >
            <Edit3 className="w-4 h-4 mr-2" />
            Enter Manually
          </button>
        </div>
      )}

      {/* Permission Status Indicator */}
      {permissionStatus !== 'unknown' && (
        <div className="mt-3 text-xs text-gray-500">
          Location permission: 
          <span className={`ml-1 ${
            permissionStatus === 'granted' ? 'text-green-600' : 
            permissionStatus === 'denied' ? 'text-red-600' : 'text-yellow-600'
          }`}>
            {permissionStatus}
          </span>
        </div>
      )}
    </div>
  );
};

export default LocationManager;