from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, Max
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import json

from core.models import Region, UserProfile
from core.permissions import (
    admin_required, farmer_required, extension_officer_required,
    role_required, api_role_required, get_user_role, 
    smart_redirect_after_login
)
from drought_data.models import NDVIData, SoilMoistureData, WeatherData, DroughtRiskAssessment
from farmers.models import FarmerProfile
from alerts.models import Alert, AlertDelivery


@login_required
def react_dashboard(request):
    """
    React-based enhanced dashboard view with role-specific features
    """
    from .farmer_utils import get_farmer_dashboard_data
    
    # Get user role
    user_role = 'farmer'  # default
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.user_type
    elif request.user.is_staff or request.user.is_superuser:
        user_role = 'admin'
    
    # Get role-specific dashboard data
    dashboard_data = {}
    if user_role == 'farmer':
        dashboard_data = get_farmer_dashboard_data(request.user)
    
    context = {
        'user_role': user_role,
        'dashboard_data': dashboard_data,
    }
    
    return render(request, 'dashboard/react_dashboard.html', context)


@login_required
def dashboard_home(request):
    """
    Main dashboard view with overview metrics and charts
    """
    # Get date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Overall metrics
    total_regions = Region.objects.filter(region_type='county').count()
    total_farmers = FarmerProfile.objects.count()
    recent_alerts = Alert.objects.filter(created_at__date__gte=week_ago).count()
    
    # Risk assessments by level (latest for each region)
    latest_assessments = DroughtRiskAssessment.objects.filter(
        assessment_date__gte=month_ago
    ).values('region').annotate(
        latest_date=Max('assessment_date')
    ).values_list('region', 'latest_date')
    
    risk_summary = {}
    for region_id, latest_date in latest_assessments:
        try:
            assessment = DroughtRiskAssessment.objects.get(
                region_id=region_id,
                assessment_date=latest_date
            )
            risk_level = assessment.risk_level
            risk_summary[risk_level] = risk_summary.get(risk_level, 0) + 1
        except DroughtRiskAssessment.DoesNotExist:
            continue
    
    # Recent alerts
    recent_alert_list = Alert.objects.filter(
        created_at__date__gte=week_ago
    ).select_related('region').order_by('-created_at')[:5]
    
    # High risk regions
    high_risk_regions = DroughtRiskAssessment.objects.filter(
        assessment_date__gte=week_ago,
        risk_level__in=['high', 'very_high', 'extreme']
    ).select_related('region').order_by('-risk_score')[:5]
    
    context = {
        'total_regions': total_regions,
        'total_farmers': total_farmers,
        'recent_alerts': recent_alerts,
        'risk_summary': risk_summary,
        'recent_alert_list': recent_alert_list,
        'high_risk_regions': high_risk_regions,
        'today': today,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def risk_map(request):
    """
    Interactive map showing drought risk levels across regions
    """
    # Get latest assessments for all regions
    regions_data = []
    regions = Region.objects.filter(region_type='county')
    
    for region in regions:
        latest_assessment = DroughtRiskAssessment.objects.filter(
            region=region
        ).order_by('-assessment_date').first()
        
        region_data = {
            'id': region.id,
            'name': region.name,
            'latitude': float(region.latitude) if region.latitude else 0,
            'longitude': float(region.longitude) if region.longitude else 0,
            'risk_level': latest_assessment.risk_level if latest_assessment else 'unknown',
            'risk_score': float(latest_assessment.risk_score) if latest_assessment else 0,
            'assessment_date': latest_assessment.assessment_date.isoformat() if latest_assessment else None,
        }
        regions_data.append(region_data)
    
    context = {
        'regions_data': json.dumps(regions_data),
    }
    
    return render(request, 'dashboard/map.html', context)


@login_required
def analytics(request):
    """
    Analytics dashboard with detailed charts and trends
    """
    # Get date range from request or default to last 30 days
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    context = {
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'dashboard/analytics.html', context)


@login_required
def alerts_dashboard(request):
    """
    Alerts management dashboard
    """
    # Filter parameters
    status_filter = request.GET.get('status', 'all')
    region_filter = request.GET.get('region', 'all')
    
    # Base queryset
    alerts = Alert.objects.select_related('region').order_by('-created_at')
    
    # Apply filters
    if status_filter != 'all':
        alerts = alerts.filter(alert_type=status_filter)
    
    if region_filter != 'all':
        alerts = alerts.filter(region_id=region_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(alerts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get regions for filter dropdown
    regions = Region.objects.filter(region_type='county').order_by('name')
    
    # Alert statistics
    total_alerts = Alert.objects.count()
    alerts_today = Alert.objects.filter(created_at__date=timezone.now().date()).count()
    pending_deliveries = AlertDelivery.objects.filter(
        delivery_status='pending'
    ).count()
    
    context = {
        'page_obj': page_obj,
        'regions': regions,
        'status_filter': status_filter,
        'region_filter': region_filter,
        'total_alerts': total_alerts,
        'alerts_today': alerts_today,
        'pending_deliveries': pending_deliveries,
    }
    
    return render(request, 'dashboard/alerts.html', context)


# API endpoints for dashboard data
@login_required
def api_risk_trends(request):
    """
    API endpoint for risk trend data
    """
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get daily risk assessments
    assessments = DroughtRiskAssessment.objects.filter(
        assessment_date__range=[start_date, end_date]
    ).values('assessment_date', 'risk_level').annotate(
        count=Count('id')
    ).order_by('assessment_date')
    
    # Group by date and risk level
    risk_trends = {}
    for assessment in assessments:
        date_str = assessment['assessment_date'].isoformat()
        risk_level = assessment['risk_level']
        count = assessment['count']
        
        if date_str not in risk_trends:
            risk_trends[date_str] = {}
        
        risk_trends[date_str][risk_level] = count
    
    return JsonResponse({
        'risk_trends': risk_trends,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


@login_required
def api_ndvi_trends(request):
    """
    API endpoint for NDVI trend data
    """
    region_id = request.GET.get('region')
    days = int(request.GET.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    queryset = NDVIData.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    if region_id:
        queryset = queryset.filter(region_id=region_id)
    
    # Get average NDVI by date
    ndvi_data = queryset.values('date').annotate(
        avg_ndvi=Avg('ndvi_value')
    ).order_by('date')
    
    trends = []
    for item in ndvi_data:
        trends.append({
            'date': item['date'].isoformat(),
            'value': round(float(item['avg_ndvi']), 3)
        })
    
    return JsonResponse({
        'trends': trends,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


@login_required
def api_soil_moisture_trends(request):
    """
    API endpoint for soil moisture trend data
    """
    region_id = request.GET.get('region')
    days = int(request.GET.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    queryset = SoilMoistureData.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    if region_id:
        queryset = queryset.filter(region_id=region_id)
    
    # Get average soil moisture by date
    moisture_data = queryset.values('date').annotate(
        avg_moisture=Avg('moisture_percent')
    ).order_by('date')
    
    trends = []
    for item in moisture_data:
        trends.append({
            'date': item['date'].isoformat(),
            'value': round(float(item['avg_moisture']), 1)
        })
    
    return JsonResponse({
        'trends': trends,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


@login_required
def api_weather_data(request):
    """
    API endpoint for weather data
    """
    region_id = request.GET.get('region')
    days = int(request.GET.get('days', 7))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    queryset = WeatherData.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    if region_id:
        queryset = queryset.filter(region_id=region_id)
    
    weather_data = queryset.values(
        'date', 'temperature_avg', 'precipitation_mm', 'humidity_percent'
    )
    
    data = []
    for item in weather_data:
        data.append({
            'date': item['date'].isoformat(),
            'temperature': float(item['temperature_avg']) if item['temperature_avg'] else 0,
            'precipitation': float(item['precipitation_mm']) if item['precipitation_mm'] else 0,
            'humidity': float(item['humidity_percent']) if item['humidity_percent'] else 0,
        })
    
    return JsonResponse({
        'weather_data': data,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


@login_required
def api_regional_summary(request):
    """
    API endpoint for regional summary data
    """
    regions = Region.objects.filter(region_type='county')
    summary_data = []
    
    for region in regions:
        # Latest risk assessment
        latest_assessment = DroughtRiskAssessment.objects.filter(
            region=region
        ).order_by('-assessment_date').first()
        
        # Count of farmers in this region
        farmer_count = FarmerProfile.objects.filter(
            user_profile__region=region
        ).count()
        
        # Recent alerts
        recent_alerts = Alert.objects.filter(
            region=region,
            created_at__date__gte=timezone.now().date() - timedelta(days=7)
        ).count()
        
        summary_data.append({
            'region_id': region.id,
            'region_name': region.name,
            'risk_level': latest_assessment.risk_level if latest_assessment else 'unknown',
            'risk_score': float(latest_assessment.risk_score) if latest_assessment else 0,
            'farmer_count': farmer_count,
            'recent_alerts': recent_alerts,
            'assessment_date': latest_assessment.assessment_date.isoformat() if latest_assessment else None,
        })
    
    return JsonResponse({
        'regional_summary': summary_data
    })


# Authentication Helper Functions
def is_admin_user(user):
    """
    Check if user is admin (staff or superuser)
    """
    return user.is_staff or user.is_superuser


def is_farmer_user(user):
    """
    Check if user is a farmer
    """
    try:
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.user_type == 'farmer'
    except UserProfile.DoesNotExist:
        return False


def is_extension_officer(user):
    """
    Check if user is an extension officer  
    """
    try:
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.user_type == 'extension_officer'
    except UserProfile.DoesNotExist:
        return False


def redirect_based_on_role(user):
    """
    Redirect user to appropriate dashboard based on their role
    """
    if user.is_staff or user.is_superuser:
        return redirect('dashboard:admin_dashboard')
    
    try:
        user_profile = UserProfile.objects.get(user=user)
        if user_profile.user_type == 'admin':
            return redirect('dashboard:admin_dashboard')
        elif user_profile.user_type == 'extension_officer':
            return redirect('dashboard:admin_dashboard')  # Extension officers use admin dashboard
        else:
            return redirect('dashboard:react_dashboard')  # Farmers use React dashboard
    except UserProfile.DoesNotExist:
        # Default to farmer dashboard if no profile exists
        return redirect('dashboard:react_dashboard')


# Authentication Views
def login_view(request):
    """
    Custom role-based login view
    """
    if request.user.is_authenticated:
        # Redirect based on user role
        return redirect_based_on_role(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_role = request.POST.get('user_role', 'farmer')  # Default to farmer
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Verify user role matches the selected role
            user_profile = getattr(user, 'userprofile', None)
            
            # For admin role, check if user is staff or has admin profile
            if user_role == 'admin':
                if not (user.is_staff or user.is_superuser or 
                       (user_profile and user_profile.user_type == 'admin')):
                    messages.error(request, 'You do not have admin privileges. Please use the farmer login.')
                    return render(request, 'registration/role_based_login.html')
            
            # For farmer role
            elif user_role == 'farmer':
                if user.is_staff or user.is_superuser:
                    messages.info(request, 'Admin users should use the admin login.')
                    return render(request, 'registration/role_based_login.html')
            
            login(request, user)
            
            # Redirect based on role or next parameter
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect(smart_redirect_after_login(user))
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/role_based_login.html')


def logout_view(request):
    """
    Custom logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('dashboard:login')


@login_required
def profile_view(request):
    """
    User profile view
    """
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'user_type': 'farmer',  # Default to farmer
            'phone_number': '',
        }
    )
    
    if request.method == 'POST':
        # Update profile
        user_profile.phone_number = request.POST.get('phone_number', '')
        user_profile.user_type = request.POST.get('user_type', user_profile.user_type)
        
        # Update region if provided
        region_id = request.POST.get('region')
        if region_id:
            try:
                user_profile.region = Region.objects.get(id=region_id)
            except Region.DoesNotExist:
                pass
        
        user_profile.save()
        
        # Update user info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    regions = Region.objects.filter(region_type='county').order_by('name')
    
    context = {
        'user_profile': user_profile,
        'regions': regions,
    }
    
    return render(request, 'dashboard/profile.html', context)


@admin_required
def admin_user_management(request):
    """
    Admin view for managing users
    """
    users = User.objects.select_related('userprofile').order_by('-date_joined')
    
    # Get user statistics
    total_users = users.count()
    admin_users = users.filter(Q(is_staff=True) | Q(is_superuser=True)).count()
    farmer_users = users.filter(userprofile__user_type='farmer').count()
    extension_officers = users.filter(userprofile__user_type='extension_officer').count()
    
    context = {
        'users': users,
        'total_users': total_users,
        'admin_users': admin_users,
        'farmer_users': farmer_users,
        'extension_officers': extension_officers,
    }
    
    return render(request, 'dashboard/admin_users.html', context)


@admin_required
def create_alert(request):
    """
    Create and send a new alert
    """
    if request.method == 'POST':
        try:
            from alerts.models import Alert, AlertDelivery
            from alerts.tasks import send_alert
            
            # Get form data
            region_id = request.POST.get('region')
            alert_type = request.POST.get('alert_type', 'drought_warning')
            severity_level = request.POST.get('severity_level', 'info')
            title = request.POST.get('title')
            message = request.POST.get('message')
            
            # Get delivery methods
            send_whatsapp = request.POST.get('send_whatsapp') == 'on'
            send_sms = request.POST.get('send_sms') == 'on'
            send_email = request.POST.get('send_email') == 'on'
            
            # Validate required fields
            if not all([region_id, title, message]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('dashboard:alerts')
            
            # Get region
            try:
                region = Region.objects.get(id=region_id)
            except Region.DoesNotExist:
                messages.error(request, 'Invalid region selected.')
                return redirect('dashboard:alerts')
            
            # Create alert
            alert = Alert.objects.create(
                region=region,
                alert_type=alert_type,
                severity_level=severity_level,
                title=title,
                message=message,
                sms_message=message[:160] if len(message) > 160 else message,  # Truncate for SMS
                priority='high' if severity_level in ['warning', 'danger'] else 'normal',
                status='sending',
                created_by=request.user
            )
            
            # Set delivery preferences (if none selected, default to WhatsApp)
            if not any([send_whatsapp, send_sms, send_email]):
                send_whatsapp = True
            
            # Store delivery preferences in alert metadata
            alert.metadata = {
                'send_whatsapp': send_whatsapp,
                'send_sms': send_sms,
                'send_email': send_email
            }
            alert.save()
            
            # Send alert asynchronously
            send_alert.delay(alert.id)
            
            messages.success(request, f'Alert "{title}" has been created and is being sent to users in {region.name}.')
            return redirect('dashboard:alerts')
            
        except Exception as e:
            logger.error(f'Error creating alert: {str(e)}')
            messages.error(request, 'Failed to create alert. Please try again.')
            return redirect('dashboard:alerts')
    
    # GET request - redirect to alerts page
    return redirect('dashboard:alerts')


@admin_required
def test_alert_services(request):
    """
    Test alert messaging services
    """
    if request.method == 'POST':
        try:
            from alerts.services import whatsapp_service, sms_service, email_service
            
            phone_number = request.POST.get('phone_number')
            email_address = request.POST.get('email_address')
            test_service = request.POST.get('test_service', 'all')
            
            # Use current user's contact info if not provided
            if not phone_number:
                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                    phone_number = user_profile.phone_number
                except UserProfile.DoesNotExist:
                    phone_number = '+254700000000'  # Default test number
            
            if not email_address:
                email_address = request.user.email or 'test@example.com'
            
            # Test messages
            test_title = "Test Alert from Drought Warning System"
            test_message = f"""This is a test alert sent by {request.user.get_full_name() or request.user.username} from the Drought Warning System dashboard.
            
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: System operational
            
This is a test message to verify alert delivery systems are working correctly."""
            
            results = []
            
            # Test WhatsApp
            if test_service in ['whatsapp', 'all']:
                result = whatsapp_service.send_message(phone_number, test_message, test_title)
                results.append(('WhatsApp', result))
            
            # Test SMS
            if test_service in ['sms', 'all']:
                sms_message = f"TEST: {test_title}. {test_message[:100]}..."
                result = sms_service.send_message(phone_number, sms_message)
                results.append(('SMS', result))
            
            # Test Email
            if test_service in ['email', 'all']:
                result = email_service.send_message(email_address, test_title, test_message)
                results.append(('Email', result))
            
            # Process results
            success_count = sum(1 for _, result in results if result.get('success', False))
            total_count = len(results)
            
            if success_count == total_count:
                messages.success(request, f'All {total_count} messaging services tested successfully!')
            elif success_count > 0:
                messages.warning(request, f'{success_count}/{total_count} messaging services working. Check logs for details.')
            else:
                messages.error(request, 'All messaging services failed. Check configuration and logs.')
            
            # Add individual service results
            for service_name, result in results:
                if result.get('success', False):
                    messages.info(request, f'{service_name}: ✅ Success (ID: {result.get("message_id", "N/A")})')
                else:
                    messages.error(request, f'{service_name}: ❌ Failed - {result.get("error", "Unknown error")}')
            
        except Exception as e:
            logger.error(f'Error testing alert services: {str(e)}')
            messages.error(request, f'Error testing services: {str(e)}')
    
    return redirect('dashboard:alerts')

@admin_required
def admin_dashboard(request):
    """
    Enhanced admin dashboard with comprehensive system overview
    """
    from .admin_utils import get_system_overview, get_data_quality_report
    from django.contrib.auth.models import User
    from alerts.models import Alert
    
    overview = get_system_overview()
    data_quality = get_data_quality_report()
    
    # Get recent users for activity display
    recent_users = User.objects.select_related('userprofile').filter(
        last_login__isnull=False
    ).order_by('-last_login')[:10]
    
    # Get recent alerts
    recent_alerts = Alert.objects.select_related('region').order_by('-created_at')[:10]
    
    context = {
        'overview': overview,
        'data_quality': data_quality,
        'recent_users': recent_users,
        'recent_alerts': recent_alerts,
        'page_title': 'Admin Dashboard',
    }
    
    # Use enhanced template for better admin experience
    return render(request, 'dashboard/enhanced_admin_dashboard.html', context)


@admin_required
def admin_alert_management(request):
    """
    Comprehensive alert management interface
    """
    from .admin_utils import get_alert_management_data
    
    data = get_alert_management_data()
    
    context = {
        'alerts': data['alerts'],
        'status_counts': data['status_counts'],
        'priority_counts': data['priority_counts'],
        'delivery_stats': data['delivery_stats'],
        'regions': data['regions'],
        'page_title': 'Alert Management',
    }
    
    return render(request, 'dashboard/admin_alerts.html', context)


@admin_required
def admin_farmer_management(request):
    """
    Comprehensive farmer and user management interface
    """
    from .admin_utils import get_farmer_management_data
    
    data = get_farmer_management_data()
    
    context = {
        'farmers': data['farmers'],
        'farmer_regions': data['farmer_regions'],
        'registration_trend': data['registration_trend'],
        'ussd_farmers': data['ussd_farmers'],
        'total_farmers': data['total_farmers'],
        'regions': data['regions'],
        'page_title': 'Farmer Management',
    }
    
    return render(request, 'dashboard/admin_farmers.html', context)


@admin_required
def admin_ussd_analytics(request):
    """
    USSD system analytics and management
    """
    from .admin_utils import get_ussd_analytics
    
    analytics = get_ussd_analytics()
    
    # Get recent USSD sessions for detailed view
    recent_sessions = USSDSession.objects.select_related('user').order_by('-started_at')[:50]
    
    context = {
        'analytics': analytics,
        'recent_sessions': recent_sessions,
        'page_title': 'USSD Analytics',
    }
    
    return render(request, 'dashboard/admin_ussd.html', context)


@admin_required
def admin_data_management(request):
    """
    Data management and system health monitoring
    """
    from .admin_utils import get_data_quality_report
    
    data_quality = get_data_quality_report()
    
    # Get latest data samples
    latest_weather = WeatherData.objects.select_related('region').order_by('-date')[:10]
    latest_ndvi = NDVIData.objects.select_related('region').order_by('-date')[:10]
    latest_assessments = DroughtRiskAssessment.objects.select_related('region').order_by('-assessment_date')[:10]
    
    context = {
        'data_quality': data_quality,
        'latest_weather': latest_weather,
        'latest_ndvi': latest_ndvi,
        'latest_assessments': latest_assessments,
        'page_title': 'Data Management',
    }
    
    return render(request, 'dashboard/admin_data.html', context)


@admin_required
def admin_bulk_alert(request):
    """
    Create and send bulk alerts to multiple regions
    """
    if request.method == 'POST':
        try:
            from alerts.models import Alert
            from alerts.tasks import send_alert
            
            # Get form data
            selected_regions = request.POST.getlist('regions')
            alert_type = request.POST.get('alert_type', 'drought_warning')
            severity_level = request.POST.get('severity_level', 'info')
            title = request.POST.get('title')
            message = request.POST.get('message')
            
            # Delivery methods
            send_whatsapp = request.POST.get('send_whatsapp') == 'on'
            send_sms = request.POST.get('send_sms') == 'on'
            send_email = request.POST.get('send_email') == 'on'
            
            # Validate required fields
            if not all([selected_regions, title, message]):
                messages.error(request, 'Please fill in all required fields and select at least one region.')
                return redirect('dashboard:admin_alerts')
            
            # Create alerts for each selected region
            created_alerts = []
            for region_id in selected_regions:
                try:
                    region = Region.objects.get(id=region_id)
                    
                    alert = Alert.objects.create(
                        region=region,
                        alert_type=alert_type,
                        severity_level=severity_level,
                        title=title,
                        message=message,
                        sms_message=message[:160] if len(message) > 160 else message,
                        priority='high' if severity_level in ['warning', 'danger'] else 'normal',
                        status='sending',
                        created_by=request.user
                    )
                    
                    # Store delivery preferences
                    alert.metadata = {
                        'send_whatsapp': send_whatsapp,
                        'send_sms': send_sms,
                        'send_email': send_email
                    }
                    alert.save()
                    
                    created_alerts.append(alert)
                    
                except Region.DoesNotExist:
                    continue
            
            # Send all alerts asynchronously
            for alert in created_alerts:
                send_alert.delay(alert.id)
            
            messages.success(request, f'Bulk alert "{title}" has been created and is being sent to {len(created_alerts)} regions.')
            return redirect('dashboard:admin_alerts')
            
        except Exception as e:
            logger.error(f'Error creating bulk alert: {str(e)}')
            messages.error(request, 'Failed to create bulk alert. Please try again.')
            return redirect('dashboard:admin_alerts')
    
    return redirect('dashboard:admin_alerts')


@admin_required
def admin_export_data(request):
    """
    Export system data to CSV/Excel
    """
    export_type = request.GET.get('type', 'users')
    format_type = request.GET.get('format', 'csv')
    
    import csv
    from django.http import HttpResponse
    
    # Set up the HTTP response
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_export.csv"'
        writer = csv.writer(response)
    else:
        # For Excel format (would need openpyxl)
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_export.csv"'
        writer = csv.writer(response)
    
    if export_type == 'users':
        # Export user data
        writer.writerow(['Username', 'Email', 'Full Name', 'User Type', 'Region', 'Phone', 'Date Joined', 'Last Login'])
        
        users = User.objects.select_related('userprofile').order_by('-date_joined')
        for user in users:
            profile = getattr(user, 'userprofile', None)
            writer.writerow([
                user.username,
                user.email,
                user.get_full_name(),
                profile.user_type if profile else 'N/A',
                profile.region.name if profile and profile.region else 'N/A',
                profile.phone_number if profile else 'N/A',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
            ])
    
    elif export_type == 'alerts':
        # Export alert data
        writer.writerow(['Alert ID', 'Title', 'Region', 'Type', 'Severity', 'Status', 'Created By', 'Created At', 'Sent At'])
        
        alerts = Alert.objects.select_related('region', 'created_by').order_by('-created_at')
        for alert in alerts:
            writer.writerow([
                alert.alert_id,
                alert.title,
                alert.region.name,
                alert.alert_type,
                alert.severity_level,
                alert.status,
                alert.created_by.username,
                alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                alert.sent_at.strftime('%Y-%m-%d %H:%M:%S') if alert.sent_at else 'Not sent'
            ])
    
    elif export_type == 'ussd_users':
        # Export USSD user data
        writer.writerow(['Phone Number', 'Full Name', 'Region', 'Farm Size', 'Primary Crops', 'Registration Date', 'Last Activity'])
        
        ussd_users = USSDUser.objects.select_related('region').order_by('-registration_date')
        for user in ussd_users:
            writer.writerow([
                user.phone_number,
                user.full_name,
                user.region.name if user.region else 'N/A',
                user.farm_size_acres or 'N/A',
                user.primary_crops,
                user.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_activity.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    return response
