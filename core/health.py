"""
Health check views for monitoring and load balancing
"""
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """Simple health check endpoint"""
    return HttpResponse("healthy\n", content_type="text/plain")


def health_detailed(request):
    """Detailed health check with database and cache status"""
    health_status = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "checks": {
            "database": "unknown",
            "cache": "unknown"
        }
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    # Check cache connection
    try:
        cache.set("health_check", "test", 10)
        cache.get("health_check")
        health_status["checks"]["cache"] = "healthy"
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status["checks"]["cache"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)
