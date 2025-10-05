from rest_framework import serializers
from core.serializers import UserProfileSerializer, RegionSummarySerializer
from drought_data.serializers import DroughtRiskAssessmentSerializer
from .models import (
    AlertTemplate, Alert, AlertDelivery, AlertSubscription, AlertFeedback
)


class AlertTemplateSerializer(serializers.ModelSerializer):
    """Serializer for AlertTemplate model"""
    
    class Meta:
        model = AlertTemplate
        fields = [
            'id', 'name', 'alert_type', 'severity_level', 'title_template',
            'message_template', 'sms_template', 'language', 'is_active',
            'auto_send', 'trigger_risk_threshold', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model"""
    template = AlertTemplateSerializer(read_only=True)
    template_id = serializers.IntegerField(write_only=True)
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    drought_assessment = DroughtRiskAssessmentSerializer(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'alert_id', 'template', 'template_id', 'region', 'region_id',
            'title', 'message', 'sms_message', 'priority', 'status',
            'drought_assessment', 'scheduled_send_time', 'sent_at',
            'created_by', 'created_by_name', 'total_recipients',
            'successfully_sent', 'failed_sends', 'created_at', 'updated_at'
        ]
        read_only_fields = ['alert_id', 'created_at', 'updated_at', 'sent_at', 'created_by']


class AlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alerts"""
    template_id = serializers.IntegerField()
    region_id = serializers.IntegerField()
    target_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Optional list of specific user profile IDs to target"
    )
    
    class Meta:
        model = Alert
        fields = [
            'template_id', 'region_id', 'title', 'message', 'sms_message',
            'priority', 'scheduled_send_time', 'target_user_ids'
        ]
    
    def validate_template_id(self, value):
        try:
            AlertTemplate.objects.get(id=value, is_active=True)
        except AlertTemplate.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive template")
        return value
    
    def create(self, validated_data):
        target_user_ids = validated_data.pop('target_user_ids', [])
        
        # Create the alert
        alert = Alert.objects.create(
            created_by=self.context['request'].user,
            **validated_data
        )
        
        # Add target users if specified
        if target_user_ids:
            from core.models import UserProfile
            target_users = UserProfile.objects.filter(id__in=target_user_ids)
            alert.target_users.set(target_users)
        
        return alert


class AlertDeliverySerializer(serializers.ModelSerializer):
    """Serializer for AlertDelivery model"""
    alert = AlertSerializer(read_only=True)
    recipient = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = AlertDelivery
        fields = [
            'id', 'alert', 'recipient', 'delivery_method', 'status',
            'phone_number', 'email_address', 'sent_at', 'delivered_at',
            'read_at', 'error_message', 'retry_count', 'max_retries',
            'external_message_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AlertSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for AlertSubscription model"""
    user_profile = UserProfileSerializer(read_only=True)
    user_profile_id = serializers.IntegerField(write_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    min_severity_display = serializers.CharField(source='get_min_severity_level_display', read_only=True)
    
    class Meta:
        model = AlertSubscription
        fields = [
            'id', 'user_profile', 'user_profile_id', 'alert_type', 'alert_type_display',
            'is_subscribed', 'min_severity_level', 'min_severity_display',
            'prefer_whatsapp', 'prefer_sms', 'prefer_email',
            'quiet_hours_start', 'quiet_hours_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AlertFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for AlertFeedback model"""
    alert = AlertSerializer(read_only=True)
    alert_id = serializers.CharField(write_only=True)
    user_profile = UserProfileSerializer(read_only=True)
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    
    class Meta:
        model = AlertFeedback
        fields = [
            'id', 'alert', 'alert_id', 'user_profile', 'feedback_type',
            'feedback_type_display', 'rating', 'comment', 'action_taken',
            'action_description', 'created_at'
        ]
        read_only_fields = ['created_at', 'user_profile']
    
    def validate_alert_id(self, value):
        try:
            Alert.objects.get(alert_id=value)
        except Alert.DoesNotExist:
            raise serializers.ValidationError("Alert not found")
        return value
    
    def create(self, validated_data):
        alert_id = validated_data.pop('alert_id')
        alert = Alert.objects.get(alert_id=alert_id)
        
        # Get user profile
        from core.models import UserProfile
        user_profile = UserProfile.objects.get(user=self.context['request'].user)
        
        feedback = AlertFeedback.objects.create(
            alert=alert,
            user_profile=user_profile,
            **validated_data
        )
        
        return feedback


class AlertSummarySerializer(serializers.Serializer):
    """Serializer for alert summary statistics"""
    total_alerts = serializers.IntegerField()
    alerts_sent_today = serializers.IntegerField()
    alerts_sent_this_week = serializers.IntegerField()
    alerts_sent_this_month = serializers.IntegerField()
    
    # By status
    status_distribution = serializers.DictField()
    
    # By priority
    priority_distribution = serializers.DictField()
    
    # By alert type
    alert_type_distribution = serializers.DictField()
    
    # Delivery statistics
    total_deliveries = serializers.IntegerField()
    successful_deliveries = serializers.IntegerField()
    failed_deliveries = serializers.IntegerField()
    delivery_success_rate = serializers.FloatField()
    
    # By delivery method
    delivery_method_distribution = serializers.DictField()
    
    # Recent activity
    recent_alerts = AlertSerializer(many=True, read_only=True)


class AlertPerformanceSerializer(serializers.Serializer):
    """Serializer for alert performance metrics"""
    alert_id = serializers.CharField()
    alert_title = serializers.CharField()
    sent_at = serializers.DateTimeField()
    
    # Delivery metrics
    total_recipients = serializers.IntegerField()
    delivered_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    
    # Rates
    delivery_rate = serializers.FloatField()
    read_rate = serializers.FloatField()
    failure_rate = serializers.FloatField()
    
    # Response metrics
    feedback_count = serializers.IntegerField()
    average_rating = serializers.FloatField(allow_null=True)
    action_taken_count = serializers.IntegerField()
    action_taken_rate = serializers.FloatField()
    
    # Timing
    average_delivery_time = serializers.FloatField(allow_null=True)  # in minutes


class BulkAlertCreateSerializer(serializers.Serializer):
    """Serializer for creating bulk alerts"""
    template_id = serializers.IntegerField()
    region_ids = serializers.ListField(child=serializers.IntegerField())
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    sms_message = serializers.CharField(max_length=160, required=False)
    priority = serializers.ChoiceField(choices=Alert.PRIORITY_LEVELS, default='normal')
    scheduled_send_time = serializers.DateTimeField(required=False)
    
    # Filtering options
    user_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Filter by user types: farmer, admin, extension_officer"
    )
    
    min_risk_level = serializers.CharField(required=False)
    
    def validate_template_id(self, value):
        try:
            AlertTemplate.objects.get(id=value, is_active=True)
        except AlertTemplate.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive template")
        return value
    
    def validate_region_ids(self, value):
        from core.models import Region
        existing_count = Region.objects.filter(id__in=value).count()
        if existing_count != len(value):
            raise serializers.ValidationError("One or more invalid region IDs")
        return value