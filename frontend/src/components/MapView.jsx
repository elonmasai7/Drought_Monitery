import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import { Layers, MapPin, ToggleLeft, ToggleRight } from 'lucide-react';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom pulse marker for user location
const pulseIcon = new L.DivIcon({
  className: 'pulse-marker',
  html: `<div class="pulse-dot"></div>`,
  iconSize: [20, 20],
});

const MapView = ({ userLocation, onLocationUpdate }) => {
  const [map, setMap] = useState(null);
  const [ndviData, setNdviData] = useState([]);
  const [soilData, setSoilData] = useState([]);
  const [activeLayers, setActiveLayers] = useState({
    ndvi: true,
    soilMoisture: false,
    soilPH: false
  });
  const [loading, setLoading] = useState(false);
  const [legendVisible, setLegendVisible] = useState(true);
  
  const mapRef = useRef(null);

  // Default center for Kenya
  const defaultCenter = [-1.2921, 36.8219];
  const mapCenter = userLocation ? [userLocation.lat, userLocation.lng] : defaultCenter;

  useEffect(() => {
    if (activeLayers.ndvi) {
      fetchNDVIData();
    }
    if (activeLayers.soilMoisture || activeLayers.soilPH) {
      fetchSoilData();
    }
  }, [activeLayers]);

  const fetchNDVIData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/core/api/ndvi/', {
        headers: {
          'X-CSRFToken': window.csrfToken,
        },
        withCredentials: true
      });
      
      if (response.data.success) {
        setNdviData(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching NDVI data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSoilData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/core/api/soil_ph/', {
        headers: {
          'X-CSRFToken': window.csrfToken,
        },
        withCredentials: true
      });
      
      if (response.data.success) {
        setSoilData(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching soil data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleLayer = (layerName) => {
    setActiveLayers(prev => ({
      ...prev,
      [layerName]: !prev[layerName]
    }));
  };

  const getColorForNDVI = (ndvi) => {
    if (ndvi > 0.8) return '#006400'; // Dark green - very healthy
    if (ndvi > 0.6) return '#32CD32'; // Lime green - healthy
    if (ndvi > 0.4) return '#FFFF00'; // Yellow - moderate
    if (ndvi > 0.2) return '#FF8C00'; // Orange - poor
    return '#FF0000'; // Red - very poor
  };

  const getColorForSoilMoisture = (moisture) => {
    if (moisture > 80) return '#0000FF'; // Blue - very wet
    if (moisture > 60) return '#4169E1'; // Royal blue - wet
    if (moisture > 40) return '#FFD700'; // Gold - moderate
    if (moisture > 20) return '#FF8C00'; // Orange - dry
    return '#FF0000'; // Red - very dry
  };

  const getColorForSoilPH = (ph) => {
    if (ph >= 6.5 && ph <= 7.5) return '#00FF00'; // Green - optimal
    if (ph >= 6.0 && ph < 6.5) return '#FFFF00'; // Yellow - acceptable acidic
    if (ph > 7.5 && ph <= 8.0) return '#FFFF00'; // Yellow - acceptable alkaline
    if (ph < 6.0) return '#FF0000'; // Red - too acidic
    return '#FF4500'; // Orange red - too alkaline
  };

  const requestLocationPermission = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const newLocation = { lat: latitude, lng: longitude };
          onLocationUpdate(newLocation);
          
          if (map) {
            map.setView([latitude, longitude], 12);
          }
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please enable location services or enter coordinates manually.');
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  };

  return (
    <div className="relative w-full h-96 md:h-[600px] rounded-lg overflow-hidden shadow-lg">
      {/* Layer Controls */}
      <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-md p-3">
        <div className="flex items-center mb-2">
          <Layers className="w-4 h-4 mr-2" />
          <span className="font-semibold text-sm">Map Layers</span>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs">NDVI</span>
            <button
              onClick={() => toggleLayer('ndvi')}
              className="focus:outline-none"
            >
              {activeLayers.ndvi ? 
                <ToggleRight className="w-5 h-5 text-green-500" /> : 
                <ToggleLeft className="w-5 h-5 text-gray-400" />
              }
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs">Soil Moisture</span>
            <button
              onClick={() => toggleLayer('soilMoisture')}
              className="focus:outline-none"
            >
              {activeLayers.soilMoisture ? 
                <ToggleRight className="w-5 h-5 text-blue-500" /> : 
                <ToggleLeft className="w-5 h-5 text-gray-400" />
              }
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs">Soil pH</span>
            <button
              onClick={() => toggleLayer('soilPH')}
              className="focus:outline-none"
            >
              {activeLayers.soilPH ? 
                <ToggleRight className="w-5 h-5 text-yellow-500" /> : 
                <ToggleLeft className="w-5 h-5 text-gray-400" />
              }
            </button>
          </div>
        </div>
      </div>

      {/* Location Controls */}
      <div className="absolute top-4 left-4 z-[1000]">
        <button
          onClick={requestLocationPermission}
          className="bg-primary-500 hover:bg-primary-600 text-white px-3 py-2 rounded-lg shadow-md flex items-center text-sm"
        >
          <MapPin className="w-4 h-4 mr-1" />
          My Location
        </button>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[1000] bg-white rounded-lg px-4 py-2 shadow-md">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500 mr-2"></div>
            <span className="text-sm">Loading...</span>
          </div>
        </div>
      )}

      {/* Map */}
      <MapContainer
        center={mapCenter}
        zoom={8}
        className="w-full h-full"
        ref={setMap}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {/* User Location Marker */}
        {userLocation && (
          <Marker 
            position={[userLocation.lat, userLocation.lng]} 
            icon={pulseIcon}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-semibold">Your Location</h3>
                <p className="text-sm text-gray-600">
                  {userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}
                </p>
              </div>
            </Popup>
          </Marker>
        )}

        {/* NDVI Data Points */}
        {activeLayers.ndvi && ndviData.map((point) => {
          if (!point.region.latitude || !point.region.longitude) return null;
          
          return (
            <Marker
              key={`ndvi-${point.id}`}
              position={[point.region.latitude, point.region.longitude]}
              icon={new L.DivIcon({
                className: 'ndvi-marker',
                html: `<div style="
                  background-color: ${getColorForNDVI(point.ndvi_value)};
                  width: 20px;
                  height: 20px;
                  border-radius: 50%;
                  border: 2px solid white;
                  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                "></div>`,
                iconSize: [20, 20],
              })}
            >
              <Popup>
                <div>
                  <h3 className="font-semibold">{point.region.name}</h3>
                  <p className="text-sm">NDVI: {point.ndvi_value.toFixed(3)}</p>
                  <p className="text-xs text-gray-600">{point.date}</p>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Soil Data Points */}
        {(activeLayers.soilMoisture || activeLayers.soilPH) && soilData.map((point) => {
          if (!point.region.latitude || !point.region.longitude) return null;
          
          const color = activeLayers.soilMoisture ? 
            getColorForSoilMoisture(point.moisture_percentage) :
            getColorForSoilPH(point.soil_ph);
          
          return (
            <Marker
              key={`soil-${point.id}`}
              position={[point.region.latitude, point.region.longitude]}
              icon={new L.DivIcon({
                className: 'soil-marker',
                html: `<div style="
                  background-color: ${color};
                  width: 18px;
                  height: 18px;
                  border-radius: 3px;
                  border: 2px solid white;
                  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                "></div>`,
                iconSize: [18, 18],
              })}
            >
              <Popup>
                <div>
                  <h3 className="font-semibold">{point.region.name}</h3>
                  {activeLayers.soilMoisture && (
                    <p className="text-sm">Moisture: {point.moisture_percentage.toFixed(1)}%</p>
                  )}
                  {activeLayers.soilPH && (
                    <p className="text-sm">pH: {point.soil_ph.toFixed(1)}</p>
                  )}
                  <p className="text-xs text-gray-600">{point.date}</p>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Legend */}
      {legendVisible && (
        <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-md p-3 max-w-xs">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-sm">Legend</h4>
            <button
              onClick={() => setLegendVisible(false)}
              className="text-gray-400 hover:text-gray-600 text-xs"
            >
              ×
            </button>
          </div>
          
          {activeLayers.ndvi && (
            <div className="mb-2">
              <p className="text-xs font-medium">NDVI (Vegetation Health)</p>
              <div className="flex items-center text-xs space-x-1">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>Poor</span>
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <span>Moderate</span>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>Healthy</span>
              </div>
            </div>
          )}
          
          {activeLayers.soilMoisture && (
            <div className="mb-2">
              <p className="text-xs font-medium">Soil Moisture</p>
              <div className="flex items-center text-xs space-x-1">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span>Dry</span>
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                <span>Moderate</span>
                <div className="w-3 h-3 bg-blue-500 rounded"></div>
                <span>Wet</span>
              </div>
            </div>
          )}
          
          {activeLayers.soilPH && (
            <div>
              <p className="text-xs font-medium">Soil pH</p>
              <div className="flex items-center text-xs space-x-1">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span>Acidic</span>
                <div className="w-3 h-3 bg-green-500 rounded"></div>
                <span>Optimal</span>
                <div className="w-3 h-3 bg-orange-500 rounded"></div>
                <span>Alkaline</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Show Legend Button */}
      {!legendVisible && (
        <button
          onClick={() => setLegendVisible(true)}
          className="absolute bottom-4 left-4 z-[1000] bg-white hover:bg-gray-50 rounded-lg shadow-md px-3 py-2 text-sm font-medium"
        >
          Show Legend
        </button>
      )}

      {/* Custom CSS for pulse animation */}
      <style jsx>{`
        .pulse-marker {
          background: transparent !important;
          border: none !important;
        }
        
        .pulse-dot {
          width: 20px;
          height: 20px;
          background: #3b82f6;
          border-radius: 50%;
          position: relative;
          animation: pulse 2s infinite;
        }
        
        .pulse-dot::before {
          content: '';
          position: absolute;
          top: -10px;
          left: -10px;
          width: 40px;
          height: 40px;
          background: rgba(59, 130, 246, 0.3);
          border-radius: 50%;
          animation: pulse-ring 2s infinite;
        }
        
        @keyframes pulse {
          0% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.1);
          }
          100% {
            transform: scale(1);
          }
        }
        
        @keyframes pulse-ring {
          0% {
            transform: scale(0.5);
            opacity: 1;
          }
          100% {
            transform: scale(1.5);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default MapView;