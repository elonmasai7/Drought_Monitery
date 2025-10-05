"""
URL configuration for reports app
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('export/csv/', views.export_csv_report, name='export_csv'),
    path('export/excel/', views.export_excel_report, name='export_excel'),
    path('export/pdf/', views.export_pdf_report, name='export_pdf'),
    path('preview/', views.preview_report_data, name='preview_data'),
]
