#!/bin/bash

# Drought Warning System Deployment Script
set -e

echo "🚀 Starting deployment of Drought Warning System..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create one based on .env.production.example"
    echo "cp .env.production.example .env"
    echo "Then edit .env with your actual configuration values."
    exit 1
fi

# Load environment variables
source .env

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p backups

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker-compose pull

# Build the application
echo "🔨 Building application containers..."
docker-compose build --no-cache

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T web python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser (if needed)..."
docker-compose exec -T web python manage.py shell << 'PYTHON'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created: admin/admin123")
else:
    print("Superuser already exists")
PYTHON

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

# Check service health
echo "🏥 Checking service health..."
sleep 5

# Test health endpoints
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service URLs:"
echo "  Main Application: http://localhost"
echo "  Admin Panel: http://localhost/admin/"
echo "  API Documentation: http://localhost/api/v1/"
echo "  Health Check: http://localhost/health/"
echo ""
echo "🔧 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Access web container: docker-compose exec web bash"
echo ""
echo "⚠️  Don't forget to:"
echo "  1. Set up SSL certificates for production"
echo "  2. Configure your domain name"
echo "  3. Set up monitoring and backups"
echo "  4. Update the admin password"
