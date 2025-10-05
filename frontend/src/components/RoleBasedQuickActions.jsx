import React from 'react';
import { 
  Users, 
  Bell, 
  BarChart3, 
  AlertTriangle,
  MapPin,
  Leaf,
  Cloud,
  Settings,
  Database,
  FileText,
  Send,
  Shield
} from 'lucide-react';

const RoleBasedQuickActions = ({ userRole = 'farmer', currentUser }) => {
  const getFarmerActions = () => [
    {
      title: 'Weather Alerts',
      description: 'View latest weather warnings',
      icon: Cloud,
      color: 'bg-blue-500',
      href: '#alerts',
      count: null
    },
    {
      title: 'Drought Risk',
      description: 'Check current drought conditions',
      icon: AlertTriangle,
      color: 'bg-orange-500',
      href: '#risk-map',
      count: null
    },
    {
      title: 'Crop Health',
      description: 'Monitor vegetation index',
      icon: Leaf,
      color: 'bg-green-500',
      href: '#ndvi',
      count: null
    },
    {
      title: 'My Location',
      description: 'Update farm coordinates',
      icon: MapPin,
      color: 'bg-purple-500',
      href: '/dashboard/profile/',
      count: null
    }
  ];

  const getAdminActions = () => [
    {
      title: 'User Management',
      description: 'Manage farmers and staff',
      icon: Users,
      color: 'bg-blue-600',
      href: '/dashboard/admin/users/',
      count: null
    },
    {
      title: 'Send Alerts',
      description: 'Broadcast emergency alerts',
      icon: Send,
      color: 'bg-red-500',
      href: '/dashboard/admin/create-alert/',
      count: null
    },
    {
      title: 'System Analytics',
      description: 'View usage statistics',
      icon: BarChart3,
      color: 'bg-indigo-500',
      href: '/dashboard/analytics/',
      count: null
    },
    {
      title: 'Data Management',
      description: 'Manage system data',
      icon: Database,
      color: 'bg-gray-600',
      href: '/dashboard/admin/data/',
      count: null
    },
    {
      title: 'Alert Management',
      description: 'Review sent alerts',
      icon: Bell,
      color: 'bg-yellow-500',
      href: '/dashboard/admin/alerts/',
      count: null
    },
    {
      title: 'Reports',
      description: 'Generate system reports',
      icon: FileText,
      color: 'bg-green-600',
      href: '/dashboard/admin/export/',
      count: null
    }
  ];

  const getExtensionOfficerActions = () => [
    {
      title: 'Farmer Support',
      description: 'Assist registered farmers',
      icon: Users,
      color: 'bg-blue-500',
      href: '/dashboard/admin/farmers/',
      count: null
    },
    {
      title: 'Send Alerts',
      description: 'Alert farmers in your region',
      icon: Send,
      color: 'bg-orange-500',
      href: '/dashboard/admin/create-alert/',
      count: null
    },
    {
      title: 'Regional Analytics',
      description: 'Monitor your region',
      icon: BarChart3,
      color: 'bg-purple-500',
      href: '/dashboard/analytics/',
      count: null
    },
    {
      title: 'Field Reports',
      description: 'Generate field reports',
      icon: FileText,
      color: 'bg-green-500',
      href: '/dashboard/admin/export/',
      count: null
    }
  ];

  const getActionsForRole = () => {
    switch (userRole) {
      case 'admin':
        return getAdminActions();
      case 'extension_officer':
        return getExtensionOfficerActions();
      case 'farmer':
      default:
        return getFarmerActions();
    }
  };

  const getRoleTitle = () => {
    switch (userRole) {
      case 'admin':
        return 'Administrator Quick Actions';
      case 'extension_officer':
        return 'Extension Officer Tools';
      case 'farmer':
      default:
        return 'Farmer Dashboard';
    }
  };

  const getRoleIcon = () => {
    switch (userRole) {
      case 'admin':
        return Shield;
      case 'extension_officer':
        return Users;
      case 'farmer':
      default:
        return Leaf;
    }
  };

  const actions = getActionsForRole();
  const RoleIcon = getRoleIcon();

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center mb-6">
        <div className="flex-shrink-0">
          <RoleIcon className="w-8 h-8 text-primary-600" />
        </div>
        <div className="ml-4">
          <h2 className="text-xl font-semibold text-gray-900">{getRoleTitle()}</h2>
          <p className="text-sm text-gray-600">
            {currentUser?.user?.first_name ? `Welcome, ${currentUser.user.first_name}` : 'Quick access to key features'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {actions.map((action, index) => {
          const IconComponent = action.icon;
          return (
            <a
              key={index}
              href={action.href}
              className="group relative p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-all duration-200"
            >
              <div className="flex items-start">
                <div className={`flex-shrink-0 p-2 rounded-lg ${action.color} text-white group-hover:scale-110 transition-transform duration-200`}>
                  <IconComponent className="w-5 h-5" />
                </div>
                <div className="ml-4 flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-900 group-hover:text-primary-700 transition-colors">
                      {action.title}
                    </h3>
                    {action.count !== null && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                        {action.count}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mt-1 group-hover:text-gray-700">
                    {action.description}
                  </p>
                </div>
              </div>
            </a>
          );
        })}
      </div>

      {/* Role-specific tips */}
      <div className="mt-6 p-4 bg-gradient-to-r from-primary-50 to-secondary-50 rounded-lg border border-primary-100">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-primary-600 text-sm font-semibold">💡</span>
            </div>
          </div>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-gray-900 mb-1">
              {userRole === 'admin' ? 'Admin Tip' : userRole === 'extension_officer' ? 'Officer Tip' : 'Farming Tip'}
            </h4>
            <p className="text-sm text-gray-600">
              {userRole === 'admin' 
                ? 'Monitor system health regularly and keep alert templates updated for better farmer engagement.'
                : userRole === 'extension_officer'
                ? 'Use regional analytics to identify at-risk areas and proactively support farmers in your zone.'
                : 'Check your alerts daily and update your location for more accurate drought predictions.'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleBasedQuickActions;