# 🌦️ Drought Warning System

A comprehensive **Farmer-Centric Drought & Water Stress Early Warning System** built with Django that integrates satellite data, weather information, and AI/ML models to provide timely drought alerts through multiple channels including web dashboard,USSD service and WhatsApp notifications.

## 🎯 Features

### 🔍 Core Monitoring System
- **Multi-Source Data Integration**: NDVI satellite data, weather data, soil moisture monitoring
- **AI/ML Risk Assessment**: Automated drought risk calculations using scikit-learn
- **Real-time Monitoring**: Continuous assessment of drought conditions across regions
- **Predictive Analytics**: 7-day and 30-day drought risk predictions

### 📱 Multi-Channel Communication
- **Web Dashboard**: Interactive maps and charts with Leaflet.js and Chart.js
- **USSD Service**: Feature phone compatibility for rural farmers
- **WhatsApp Integration**: Automated alerts via Twilio WhatsApp API
- **SMS Notifications**: Backup communication channel
- **Email Alerts**: Professional notifications for administrators

### 👥 User Management
- **Role-Based Access**: Admin, Extension Officer, and Farmer roles
- **Farmer Profiles**: Comprehensive farmer registration and profile management
- **Admin Panel**: Advanced management interface for alerts and users
- **Authentication System**: Secure login and token-based API access

### 📊 Data & Analytics
- **Interactive Dashboard**: Real-time visualization of drought conditions
- **Report Generation**: PDF and Excel export functionality
- **Historical Data**: Trend analysis and historical drought patterns
- **API Access**: RESTful API for third-party integrations

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Django App    │    │   Outputs       │
│                 │    │                 │    │                 │
│ • Satellite     │────│ • ML Models     │────│ • Web Dashboard │
│ • Weather APIs  │    │ • Risk Calc     │    │ • USSD Service  │
│ • Soil Sensors  │    │ • Alert System  │    │ • WhatsApp      │
│ • NDVI Data     │    │ • Task Queue    │    │ • SMS/Email     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for deployment)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/elonmasai7/Drought_Monitery.git
cd Drought_Monitery
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.production.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python manage.py migrate
python manage.py setup_initial_data
python manage.py createsuperuser
```

6. **Run the development server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## 💻 VS Code Development Setup

For the best development experience in VS Code:

### 1. **Recommended Extensions**
Install these extensions from the VS Code marketplace:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.django",
    "ms-python.pylint",
    "ms-toolsai.jupyter",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "eamodio.gitlens",
    "ms-vscode-remote.remote-containers",
    "humao.rest-client",
    "formulahendry.auto-rename-tag",
    "ms-python.black-formatter"
  ]
}
```

### 2. **VS Code Settings**
Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "files.associations": {
    "*.html": "django-html"
  },
  "emmet.includeLanguages": {
    "django-html": "html"
  }
}
```

### 3. **Launch Configuration**
Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/manage.py",
      "args": ["runserver"],
      "django": true,
      "justMyCode": true
    },
    {
      "name": "Django Tests",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/manage.py",
      "args": ["test"],
      "django": true,
      "justMyCode": true
    }
  ]
}
```

### 4. **Terminal Commands for VS Code**

Open the integrated terminal (`Ctrl+` ` or `Cmd+` `) and run:

#### **Initial Setup**
```bash
# Clone repository
git clone https://github.com/elonmasai7/Drought_Monitery.git
cd Drought_Monitery

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### **Environment Configuration**
```bash
# Copy environment template
cp .env.production.example .env

# Edit environment variables (use VS Code)
code .env
```

#### **Database Setup**
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Load sample data
python manage.py load_sample_data

# Create superuser
python manage.py createsuperuser
```

#### **Running the Application**
```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Start Redis (required for background tasks)
# Windows: Download Redis from https://redis.io/docs/getting-started/installation/install-redis-on-windows/
# macOS: brew install redis && redis-server
# Linux: sudo systemctl start redis

# Terminal 3: Celery worker (background tasks)
celery -A drought_warning_system worker -l info

# Terminal 4: Celery beat (task scheduler)
celery -A drought_warning_system beat -l info
```

### 5. **Testing Commands**

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core
python manage.py test alerts
python manage.py test drought_data

# Test USSD functionality
python manage.py test_ussd

# Test WhatsApp integration
python manage.py test_whatsapp

# Manual drought risk calculation
python manage.py calculate_drought_risk

# Create demo users
python manage.py create_demo_users
```

### 6. **API Testing with REST Client**

Create `api_tests.http` file for API testing:

```http
### Login to get token
POST http://127.0.0.1:8000/api/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}

### Get regions (replace YOUR_TOKEN)
GET http://127.0.0.1:8000/api/regions/
Authorization: Token YOUR_TOKEN

### Get drought data
GET http://127.0.0.1:8000/api/drought-data/
Authorization: Token YOUR_TOKEN

### Get alerts
GET http://127.0.0.1:8000/api/alerts/
Authorization: Token YOUR_TOKEN

### Health check
GET http://127.0.0.1:8000/health/detailed/
```

### 7. **Key URLs for Development**

- **Main Dashboard**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **API Root**: http://127.0.0.1:8000/api/
- **Reports Dashboard**: http://127.0.0.1:8000/reports/
- **Health Check**: http://127.0.0.1:8000/health/
- **USSD Endpoint**: http://127.0.0.1:8000/ussd/

### 8. **Development Workflow**

1. **Start all services**: Django server, Redis, Celery worker, Celery beat
2. **Access admin panel**: Create test data and configure settings
3. **Test API endpoints**: Use REST Client or Postman
4. **Monitor logs**: Check terminal outputs for errors
5. **Debug**: Use VS Code debugger with launch configurations

### 9. **Troubleshooting Common Issues**

```bash
# Port already in use
python manage.py runserver 8001

# Redis connection error
# Check if Redis is running: redis-cli ping

# Database connection issues
python manage.py migrate --run-syncdb

# Missing environment variables
# Check .env file and compare with .env.production.example

# Module import errors
pip install -r requirements.txt --upgrade

# Static files not loading
python manage.py collectstatic
```

### 10. **Production Testing**

```bash
# Test with production settings
export DJANGO_SETTINGS_MODULE=drought_warning_system.settings
DEBUG=False python manage.py runserver

# Run production checks
python manage.py check --deploy

# Test Docker build locally
docker-compose up --build
```

## 🐳 Docker Deployment

For production deployment using Docker:

```bash
# Copy and configure environment
cp .env.production.example .env
nano .env  # Configure your production settings

# Deploy using Docker Compose
./scripts/deploy.sh
```

The deployment includes:
- Django application with Gunicorn
- PostgreSQL database
- Redis cache and message broker
- Nginx reverse proxy
- Celery workers for background tasks

## 📋 API Documentation

### Authentication
All API endpoints require token authentication:

```bash
# Get token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'

# Use token in requests
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/regions/
```

### Main Endpoints

- **Regions**: `/api/v1/regions/` - Geographic regions management
- **Weather Data**: `/api/v1/weather/` - Weather information
- **Risk Assessments**: `/api/v1/risk-assessments/` - Drought risk data
- **Alerts**: `/api/v1/alerts/` - Alert management
- **Farmer Profiles**: `/api/v1/farmer-profiles/` - Farmer information

## 🔧 Configuration

### External APIs Required

1. **Twilio** (WhatsApp & SMS)
   - Account SID and Auth Token
   - WhatsApp Business Account

2. **Google Earth Engine** (Satellite Data)
   - Service Account Key
   - API Access

3. **NASA POWER** (Weather Data)
   - API Key

4. **OpenWeatherMap** (Additional Weather)
   - API Key

### Environment Variables

Key configuration variables in `.env`:

```env
# Security
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=drought_warning_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PASSWORD=your-redis-password

# External APIs
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
WHATSAPP_FROM_NUMBER=whatsapp:+1234567890
GOOGLE_EARTH_ENGINE_KEY=your-gee-key
NASA_POWER_API_KEY=your-nasa-key
OPENWEATHER_API_KEY=your-openweather-key
```

## 📱 USSD Service

The system includes a USSD service compatible with Africa's Talking and Twilio:

- **Main Menu**: Weather info, drought alerts, crop advice
- **Weather Information**: Real-time weather data by region
- **Drought Alerts**: Current drought warnings
- **User Registration**: Farmer profile creation via USSD

## 🔄 Background Tasks

Automated daily tasks powered by Celery:

- **Risk Calculations**: Daily drought risk assessment for all regions
- **Alert Generation**: Automatic alert creation for high-risk areas
- **Data Synchronization**: External API data fetching
- **Report Generation**: Scheduled report creation

## 📊 Monitoring & Health Checks

- **Health Endpoints**: `/health/` and `/health/detailed/`
- **System Monitoring**: Database, cache, and service status
- **Performance Metrics**: Response times and system resource usage
- **Error Logging**: Comprehensive error tracking and reporting

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test drought_data

# Test USSD service
python manage.py test_ussd

# Test automated tasks
python manage.py calculate_drought_risk --region-name="Test Region"
```

## 📈 Data Flow

1. **Data Collection**: External APIs fetch weather, satellite, and soil data
2. **Risk Assessment**: ML models process data to calculate drought risk scores
3. **Alert Generation**: High-risk areas trigger automated alerts
4. **Multi-Channel Delivery**: Alerts sent via web, USSD, WhatsApp, SMS
5. **Farmer Response**: Farmers receive actionable information and recommendations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- **Documentation**: Check the `DEPLOYMENT.md` and `TESTING_RESULTS.md` files
- **Issues**: Open an issue on GitHub
- **Health Check**: Visit `/health/detailed/` for system status

## 🙏 Acknowledgments

- **Django Community** for the excellent web framework
- **Leaflet.js** for interactive mapping capabilities
- **Chart.js** for data visualization
- **Twilio** for communication APIs
- **Google Earth Engine** for satellite data access
- **NASA POWER** for weather data
- **OpenWeatherMap** for additional weather information

---

**Built with ❤️ for farmers and agricultural communities worldwide.**

## 🌟 System Status

- ✅ **Core System**: Fully operational
- ✅ **API Endpoints**: All endpoints functional
- ✅ **Database**: PostgreSQL with sample data
- ✅ **Background Tasks**: Celery workers active
- ✅ **Health Monitoring**: Real-time status available
- ✅ **Docker Deployment**: Production-ready configuration
- ✅ **Multi-Channel Alerts**: Web, USSD, WhatsApp, SMS
- ✅ **Security**: Authentication and authorization implemented

**Last Updated**: October 4, 2025  
**Version**: 1.0.0  

