import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LogOut, 
  User, 
  Bell, 
  Menu, 
  X, 
  Home,
  Map,
  BarChart3,
  Settings,
  Calendar
} from 'lucide-react';

const Navbar = ({ user, onLogout, unreadAlertsCount = 0 }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [currentUser, setCurrentUser] = useState(user);

  useEffect(() => {
    if (!currentUser) {
      fetchUserProfile();
    }
  }, [currentUser]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get('/api/v1/users/me/', {
        headers: {
          'X-CSRFToken': window.csrfToken,
        },
        withCredentials: true
      });
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const handleLogout = () => {
    setIsLoggingOut(true);
    
    try {
      // Using session authentication, no token needed
      
      // For session auth, just redirect to logout URL
      // No need for complex CSRF handling
      

      // Logout request to Django
      // Redirect to logout URL instead of API call
      // axios.post('/dashboard/logout/', {}, {
        // headers: {
        //   'Authorization': `Token ${token}`,
        //   'X-CSRFToken': csrfToken,
        //   'Content-Type': 'application/json',
        // }
      // });

      // Clear local storage
      // No token to remove in session auth
      localStorage.removeItem('user');
      localStorage.removeItem('readAlerts');
      
      // Show success message
      if (window.showToast) {
        window.showToast('You\'ve been logged out safely.', 'success');
      } else {
        alert('You\'ve been logged out safely.');
      }
      
      // Call logout callback
      if (onLogout) {
        onLogout();
      } else {
        // Redirect to login page
        window.location.href = '/dashboard/login/';
      }
      
    } catch (error) {
      console.error('Logout error:', error);
      
      // Even if the server request fails, clear local data
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('readAlerts');
      
      if (window.showToast) {
        window.showToast('Logged out (with some issues). Please login again.', 'warning');
      }
      
      // Redirect anyway for security
      window.location.href = '/dashboard/login/';
    } finally {
      setIsLoggingOut(false);
    }
  };

  const navigationItems = [
    { name: 'Dashboard', href: '/dashboard/', icon: Home },
    { name: 'Map', href: '/dashboard/map/', icon: Map },
    { name: 'Analytics', href: '/dashboard/analytics/', icon: BarChart3 },
    { name: 'Calendar', href: '#', icon: Calendar },
  ];

  const getWelcomeMessage = () => {
    if (!currentUser) return 'Welcome';
    
    const name = currentUser.user?.first_name || currentUser.user?.username || 'Farmer';
    const hour = new Date().getHours();
    let greeting = 'Good morning';
    
    if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
    else if (hour >= 17) greeting = 'Good evening';
    
    return `${greeting}, ${name}`;
  };

  return (
    <>
      <nav className="bg-gradient-to-r from-primary-600 to-secondary-600 shadow-lg relative z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Brand */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-white">
                  🌾 Drought Monitor
                </h1>
              </div>
              
              {/* Desktop Navigation */}
              <div className="hidden md:block ml-10">
                <div className="flex items-baseline space-x-4">
                  {navigationItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <a
                        key={item.name}
                        href={item.href}
                        className="text-gray-200 hover:text-white hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center"
                      >
                        <Icon className="w-4 h-4 mr-2" />
                        {item.name}
                      </a>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right side items */}
            <div className="flex items-center space-x-4">
              {/* Welcome Message */}
              <div className="hidden sm:block text-gray-200 text-sm">
                {getWelcomeMessage()}
              </div>

              {/* Notifications Bell */}
              <div className="relative">
                <button className="text-gray-200 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors">
                  <Bell className="w-5 h-5" />
                  {unreadAlertsCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
                      {unreadAlertsCount > 99 ? '99+' : unreadAlertsCount}
                    </span>
                  )}
                </button>
              </div>

              {/* User Profile Dropdown */}
              <div className="relative">
                <button className="flex items-center text-gray-200 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors">
                  <User className="w-5 h-5 mr-2" />
                  <span className="hidden sm:block text-sm">
                    {currentUser?.user?.first_name || 'Profile'}
                  </span>
                </button>
              </div>

              {/* Logout Button */}
              <button
                onClick={handleLogout}
                disabled={isLoggingOut}
                className="flex items-center text-gray-200 hover:text-white hover:bg-red-600/20 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Logout"
              >
                <LogOut className={`w-4 h-4 mr-2 ${isLoggingOut ? 'animate-spin' : ''}`} />
                <span className="hidden sm:block">
                  {isLoggingOut ? 'Logging out...' : 'Logout'}
                </span>
              </button>

              {/* Mobile menu button */}
              <div className="md:hidden">
                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className="text-gray-200 hover:text-white p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-white/20"
                >
                  {isMenuOpen ? (
                    <X className="w-6 h-6" />
                  ) : (
                    <Menu className="w-6 h-6" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMenuOpen && (
          <div className="md:hidden absolute top-full left-0 right-0 bg-primary-700 shadow-lg z-40">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {/* Welcome message for mobile */}
              <div className="px-3 py-2 text-gray-200 text-sm border-b border-primary-600 mb-2">
                {getWelcomeMessage()}
              </div>
              
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <a
                    key={item.name}
                    href={item.href}
                    className="text-gray-200 hover:text-white hover:bg-white/10 block px-3 py-2 rounded-md text-base font-medium flex items-center"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </a>
                );
              })}
              
              {/* Mobile Profile Link */}
              <a
                href="/dashboard/profile/"
                className="text-gray-200 hover:text-white hover:bg-white/10 block px-3 py-2 rounded-md text-base font-medium flex items-center"
                onClick={() => setIsMenuOpen(false)}
              >
                <User className="w-5 h-5 mr-3" />
                Profile
              </a>
              
              {/* Mobile Settings Link */}
              <a
                href="#"
                className="text-gray-200 hover:text-white hover:bg-white/10 block px-3 py-2 rounded-md text-base font-medium flex items-center"
                onClick={() => setIsMenuOpen(false)}
              >
                <Settings className="w-5 h-5 mr-3" />
                Settings
              </a>
            </div>
          </div>
        )}
      </nav>

      {/* Backdrop for mobile menu */}
      {isMenuOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setIsMenuOpen(false)}
        />
      )}
    </>
  );
};

export default Navbar;