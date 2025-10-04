from django.contrib import admin
from .models import USSDSession, USSDUser


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'phone_number', 'current_state', 'language', 'started_at', 'is_active']
    list_filter = ['current_state', 'is_active', 'language', 'started_at']
    search_fields = ['phone_number', 'session_id']
    readonly_fields = ['session_id', 'started_at', 'last_activity', 'ended_at', 'total_requests']
    ordering = ['-started_at']


@admin.register(USSDUser)
class USSDUserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'full_name', 'region', 'preferred_language', 'registration_date', 'is_active']
    list_filter = ['preferred_language', 'is_active', 'registration_date', 'region']
    search_fields = ['phone_number', 'full_name']
    readonly_fields = ['registration_date', 'last_activity']
    ordering = ['-registration_date']
