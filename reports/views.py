"""
Views for report generation and export
"""
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .generators import DroughtReportGenerator


def is_admin_or_extension_officer(user):
    """Check if user is admin or extension officer"""
    if not user.is_authenticated:
        return False
    return user.is_superuser or hasattr(user, 'userprofile') and user.userprofile.role in ['admin', 'extension_officer']


@login_required
@user_passes_test(is_admin_or_extension_officer)
def reports_dashboard(request):
    """Reports dashboard view"""
    context = {
        'title': 'Reports Dashboard',
        'current_date': timezone.now().date(),
        'default_start_date': (timezone.now() - timedelta(days=30)).date(),
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_extension_officer)
@require_http_methods(["POST"])
def export_csv_report(request):
    """Export CSV report"""
    try:
        # Get parameters from request
        report_type = request.POST.get('report_type', 'summary')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Generate report
        generator = DroughtReportGenerator(start_date=start_date, end_date=end_date)
        response = generator.generate_csv_report(report_type=report_type)
        
        return response
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to generate CSV report: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_extension_officer)
@require_http_methods(["POST"])
def export_excel_report(request):
    """Export Excel report"""
    try:
        # Get parameters from request
        report_type = request.POST.get('report_type', 'full')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Generate report
        generator = DroughtReportGenerator(start_date=start_date, end_date=end_date)
        response = generator.generate_excel_report(report_type=report_type)
        
        return response
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to generate Excel report: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_extension_officer)
@require_http_methods(["POST"])
def export_pdf_report(request):
    """Export PDF report"""
    try:
        # Get parameters from request
        report_type = request.POST.get('report_type', 'summary')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Generate report
        generator = DroughtReportGenerator(start_date=start_date, end_date=end_date)
        response = generator.generate_pdf_report(report_type=report_type)
        
        return response
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to generate PDF report: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_extension_officer)
def preview_report_data(request):
    """Preview report data before export"""
    try:
        # Get parameters from request
        report_type = request.GET.get('report_type', 'summary')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Create generator to get data counts
        generator = DroughtReportGenerator(start_date=start_date, end_date=end_date)
        
        from core.models import Region
        from alerts.models import Alert
        from drought_data.models import DroughtRiskAssessment, WeatherData
        from farmers.models import FarmerProfile
        
        # Get counts for preview
        regions_count = Region.objects.filter(region_type='county').count()
        assessments_count = DroughtRiskAssessment.objects.filter(
            assessment_date__range=[generator.start_date, generator.end_date]
        ).count()
        alerts_count = Alert.objects.filter(
            created_at__date__range=[generator.start_date, generator.end_date]
        ).count()
        weather_count = WeatherData.objects.filter(
            timestamp__date__range=[generator.start_date, generator.end_date]
        ).count()
        farmers_count = FarmerProfile.objects.filter(
            user__date_joined__date__range=[generator.start_date, generator.end_date]
        ).count()
        
        return JsonResponse({
            'success': True,
            'data': {
                'period': f'{generator.start_date} to {generator.end_date}',
                'regions_count': regions_count,
                'assessments_count': assessments_count,
                'alerts_count': alerts_count,
                'weather_records_count': weather_count,
                'new_farmers_count': farmers_count,
                'report_type': report_type
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to preview report data: {str(e)}'
        }, status=500)
