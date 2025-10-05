import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Bell, 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  CheckCircle, 
  Filter,
  X,
  RefreshCw,
  Clock,
  MapPin
} from 'lucide-react';

const AlertsPanel = ({ userLocation, isVisible = true }) => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all'); // all, critical, medium, low
  const [unreadCount, setUnreadCount] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [userLocation]);

  useEffect(() => {
    filterAlerts();
  }, [alerts, filter]);

  useEffect(() => {
    // Calculate unread alerts count
    const unread = alerts.filter(alert => !isAlertRead(alert.id)).length;
    setUnreadCount(unread);
  }, [alerts]);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let url = '/api/v1/alerts/';
      
      // Add location parameters if available
      if (userLocation) {
        url += `?lat=${userLocation.lat}&lon=${userLocation.lng}`;
      }
      
      const response = await axios.get(url, {
        headers: {
          'X-CSRFToken': window.csrfToken,
        },
        withCredentials: true
      });
      
      if (response.data.results) {
        setAlerts(response.data.results);
      } else {
        setAlerts(response.data);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
      setError('Failed to load alerts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filterAlerts = () => {
    let filtered = [...alerts];
    
    if (filter !== 'all') {
      filtered = filtered.filter(alert => 
        alert.severity_level?.toLowerCase() === filter.toLowerCase()
      );
    }
    
    // Sort by date (newest first) and severity
    filtered.sort((a, b) => {
      const severityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3 };
      const severityA = severityOrder[a.severity_level?.toLowerCase()] ?? 4;
      const severityB = severityOrder[b.severity_level?.toLowerCase()] ?? 4;
      
      if (severityA !== severityB) {
        return severityA - severityB;
      }
      
      return new Date(b.created_at) - new Date(a.created_at);
    });
    
    setFilteredAlerts(filtered);
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'high':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'medium':
        return <Info className="w-5 h-5 text-yellow-500" />;
      case 'low':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      default:
        return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'medium':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'low':
        return 'bg-green-50 text-green-700 border-green-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const isAlertRead = (alertId) => {
    const readAlerts = JSON.parse(localStorage.getItem('readAlerts') || '[]');
    return readAlerts.includes(alertId);
  };

  const markAsRead = (alertId) => {
    const readAlerts = JSON.parse(localStorage.getItem('readAlerts') || '[]');
    if (!readAlerts.includes(alertId)) {
      readAlerts.push(alertId);
      localStorage.setItem('readAlerts', JSON.stringify(readAlerts));
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Radius of the Earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return (R * c).toFixed(1);
  };

  if (!isVisible) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center">
          <Bell className="w-5 h-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-800">Alerts</h2>
          {unreadCount > 0 && (
            <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
              {unreadCount}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchAlerts}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh alerts"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {[
          { key: 'all', label: 'All', count: alerts.length },
          { key: 'critical', label: 'Critical', count: alerts.filter(a => a.severity_level?.toLowerCase() === 'critical').length },
          { key: 'medium', label: 'Medium', count: alerts.filter(a => a.severity_level?.toLowerCase() === 'medium').length },
          { key: 'low', label: 'Low', count: alerts.filter(a => a.severity_level?.toLowerCase() === 'low').length }
        ].map(({ key, label, count }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
              filter === key
                ? 'text-primary-600 border-b-2 border-primary-600 bg-white'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
            }`}
          >
            {label}
            {count > 0 && (
              <span className="ml-1 text-xs bg-gray-200 text-gray-600 rounded-full px-1.5 py-0.5">
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-400">
            <div className="flex">
              <AlertTriangle className="w-5 h-5 text-red-400 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-red-700">{error}</p>
                <button
                  onClick={fetchAlerts}
                  className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        )}

        {loading && alerts.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-500 text-sm">Loading alerts...</p>
            </div>
          </div>
        )}

        {!loading && filteredAlerts.length === 0 && !error && (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">No alerts found</p>
              <p className="text-gray-400 text-sm">
                {filter === 'all' ? 'All clear!' : `No ${filter} alerts at the moment`}
              </p>
            </div>
          </div>
        )}

        {filteredAlerts.length > 0 && (
          <div className="h-full overflow-y-auto">
            <div className="space-y-1 p-2">
              {filteredAlerts.map((alert) => {
                const isRead = isAlertRead(alert.id);
                const distance = userLocation && alert.region?.latitude && alert.region?.longitude
                  ? calculateDistance(
                      userLocation.lat, 
                      userLocation.lng, 
                      parseFloat(alert.region.latitude), 
                      parseFloat(alert.region.longitude)
                    )
                  : null;

                return (
                  <div
                    key={alert.id}
                    className={`p-3 rounded-lg border transition-all hover:shadow-md cursor-pointer ${
                      isRead 
                        ? 'bg-gray-50 border-gray-200' 
                        : `${getSeverityColor(alert.severity_level)} border-l-4`
                    }`}
                    onClick={() => markAsRead(alert.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {getSeverityIcon(alert.severity_level)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className={`text-sm font-semibold truncate ${isRead ? 'text-gray-600' : 'text-gray-900'}`}>
                            {alert.title}
                          </h3>
                          {!isRead && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 ml-2"></div>
                          )}
                        </div>
                        
                        <p className={`text-sm mb-2 line-clamp-2 ${isRead ? 'text-gray-500' : 'text-gray-700'}`}>
                          {alert.message}
                        </p>
                        
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <div className="flex items-center space-x-3">
                            <div className="flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {formatTimeAgo(alert.created_at)}
                            </div>
                            
                            {alert.region && (
                              <div className="flex items-center">
                                <MapPin className="w-3 h-3 mr-1" />
                                <span className="truncate max-w-20">{alert.region.name}</span>
                                {distance && (
                                  <span className="ml-1">({distance}km)</span>
                                )}
                              </div>
                            )}
                          </div>
                          
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity_level)}`}>
                            {alert.severity_level}
                          </span>
                        </div>
                        
                        {alert.recommended_action && (
                          <div className="mt-2 p-2 bg-blue-50 rounded text-xs">
                            <strong>Recommended action:</strong> {alert.recommended_action}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsPanel;