# Drought Warning System - Deployment Guide

This guide covers deploying the Drought Warning System using Docker and Docker Compose with Gunicorn and Nginx.

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM
- 20GB free disk space

### 1. Clone and Setup

```bash
git clone <your-repository-url>
cd drought-warning-system
```

### 2. Environment Configuration

```bash
# Copy the example environment file
cp .env.production.example .env

# Edit the environment variables
nano .env
```

**Required Environment Variables:**

```env
# Security
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_PASSWORD=your-secure-database-password
REDIS_PASSWORD=your-secure-redis-password

# External APIs
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
WHATSAPP_FROM_NUMBER=whatsapp:+1234567890
GOOGLE_EARTH_ENGINE_KEY=your-google-earth-engine-key
NASA_POWER_API_KEY=your-nasa-power-api-key
OPENWEATHER_API_KEY=your-openweather-api-key
```

### 3. Deploy

```bash
# Run the deployment script
./scripts/deploy.sh
```

## 🏗️ Architecture

The deployment consists of 6 services:

1. **Web (Django + Gunicorn)** - Main application server
2. **Nginx** - Reverse proxy and static file server
3. **PostgreSQL** - Database
4. **Redis** - Cache and message broker
5. **Celery Worker** - Background task processing
6. **Celery Beat** - Scheduled task scheduler

## 📊 Service Endpoints

- **Main Application:** http://localhost
- **Admin Panel:** http://localhost/admin/
- **API:** http://localhost/api/v1/
- **Health Check:** http://localhost/health/
- **Reports:** http://localhost/reports/

## 🔧 Management Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f celery_worker
```

### Service Management
```bash
# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart web

# Scale workers
docker-compose up -d --scale celery_worker=3
```

### Database Operations
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access database shell
docker-compose exec db psql -U postgres -d drought_warning_db
```

### Application Management
```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Access web container
docker-compose exec web bash
```

## 💾 Backup and Restore

### Automatic Backup
```bash
# Run backup script
./scripts/backup.sh
```

### Manual Database Backup
```bash
# Backup
docker-compose exec db pg_dump -U postgres drought_warning_db > backup.sql

# Restore
docker-compose exec -T db psql -U postgres drought_warning_db < backup.sql
```

### Media Files Backup
```bash
# Backup
docker-compose exec web tar -czf - -C /app media/ > media_backup.tar.gz

# Restore
docker-compose exec -T web tar -xzf - -C /app < media_backup.tar.gz
```

## 🔒 Security Considerations

### SSL/HTTPS Setup
1. Obtain SSL certificates (Let's Encrypt recommended)
2. Update `nginx/nginx.conf` with SSL configuration
3. Uncomment SSL server block
4. Update environment variables with certificate paths

### Firewall Configuration
```bash
# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Block direct access to other ports
sudo ufw deny 8000
sudo ufw deny 5432
sudo ufw deny 6379
```

### Security Headers
The Nginx configuration includes security headers:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

## 📈 Monitoring and Health Checks

### Health Check Endpoints
- `/health/` - Simple health check
- `/health/detailed/` - Detailed health with database and cache status

### Service Health
```bash
# Check service status
docker-compose ps

# Monitor resource usage
docker stats

# Check health endpoints
curl http://localhost/health/
curl http://localhost/health/detailed/
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database logs
docker-compose logs db

# Verify database is ready
docker-compose exec db pg_isready -U postgres
```

#### Static Files Not Loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check nginx logs
docker-compose logs nginx
```

#### Celery Tasks Not Running
```bash
# Check celery worker logs
docker-compose logs celery_worker

# Check Redis connection
docker-compose exec redis redis-cli -a your-redis-password ping
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Reduce Gunicorn workers
# Edit gunicorn.conf.py: workers = 2
docker-compose restart web
```

### Performance Tuning

#### Database Optimization
- Increase `shared_buffers` in PostgreSQL config
- Set up connection pooling
- Create appropriate indexes

#### Application Optimization
- Enable database query optimization
- Use database connection pooling
- Implement caching strategies

#### Nginx Optimization
- Enable gzip compression (already configured)
- Set appropriate cache headers
- Use HTTP/2 with SSL

## 🔄 Updates and Maintenance

### Application Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate
```

### System Maintenance
```bash
# Clean up Docker images
docker system prune -a

# Update Docker images
docker-compose pull
docker-compose up -d
```

## 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs -f`
2. Verify service health: `curl http://localhost/health/detailed/`
3. Check system resources: `docker stats`
4. Review configuration files

## 🌐 Production Checklist

- [ ] Set strong passwords for all services
- [ ] Configure SSL/HTTPS
- [ ] Set up domain name and DNS
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Test disaster recovery procedures
- [ ] Set up log rotation
- [ ] Configure email notifications
- [ ] Perform security audit
- [ ] Set up monitoring dashboards
- [ ] Configure auto-scaling (if needed)
