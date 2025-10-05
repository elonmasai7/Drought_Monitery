from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import AlertTemplate, Alert, AlertDelivery, AlertSubscription, AlertFeedback
from .serializers import (
    AlertTemplateSerializer, AlertSerializer, AlertCreateSerializer,
    AlertDeliverySerializer, AlertSubscriptionSerializer, AlertFeedbackSerializer,
    AlertSummarySerializer, AlertPerformanceSerializer, BulkAlertCreateSerializer
)
from core.models import UserProfile, Region


class AlertTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alert templates
    """
    queryset = AlertTemplate.objects.all()
    serializer_class = AlertTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['alert_type', 'severity_level', 'language', 'is_active']
    search_fields = ['name', 'title_template']
    ordering_fields = ['name', 'alert_type', 'severity_level', 'created_at']
    ordering = ['alert_type', 'severity_level', 'name']
    
    def get_permissions(self):
        """Only admin users can modify templates"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get templates grouped by alert type"""
        alert_type = request.query_params.get('type')
        language = request.query_params.get('language', 'en')
        
        queryset = self.queryset.filter(is_active=True, language=language)
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        templates = {}
        for template in queryset:
            if template.alert_type not in templates:
                templates[template.alert_type] = []
            templates[template.alert_type].append(
                AlertTemplateSerializer(template).data
            )
        
        return Response(templates)


class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alerts
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'status', 'priority', 'template__alert_type']
    search_fields = ['title', 'alert_id']
    ordering_fields = ['created_at', 'sent_at', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AlertCreateSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # If user is not admin, only show alerts for their region
        if not user.is_staff:
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.user_type not in ['admin', 'extension_officer']:
                    if user_profile.region:
                        queryset = queryset.filter(region=user_profile.region)
                    else:
                        queryset = queryset.none()
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        """Send an alert immediately"""
        alert = self.get_object()
        
        if alert.status != 'draft':
            return Response(
                {'error': 'Only draft alerts can be sent'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        alert.status = 'sending'
        alert.sent_at = timezone.now()
        alert.save()
        
        # Here you would trigger the actual sending process
        # This could be a Celery task
        
        return Response({'message': 'Alert sending initiated'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled alert"""
        alert = self.get_object()
        
        if alert.status not in ['draft', 'scheduled']:
            return Response(
                {'error': 'Only draft or scheduled alerts can be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.status = 'cancelled'
        alert.save()
        
        return Response({'message': 'Alert cancelled'})
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent alerts for current user's region"""
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            sent_at__gte=start_date,
            sent_at__lte=end_date,
            status='sent'
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get alert statistics"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        queryset = self.get_queryset()
        
        total_alerts = queryset.count()
        alerts_today = queryset.filter(sent_at__date=today).count()
        alerts_week = queryset.filter(sent_at__date__gte=week_ago).count()
        alerts_month = queryset.filter(sent_at__date__gte=month_ago).count()
        
        # Status distribution
        status_dist = dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        
        # Priority distribution
        priority_dist = dict(queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count'))
        
        # Alert type distribution
        type_dist = dict(queryset.values('template__alert_type').annotate(count=Count('id')).values_list('template__alert_type', 'count'))
        
        # Delivery statistics
        deliveries = AlertDelivery.objects.filter(alert__in=queryset)
        total_deliveries = deliveries.count()
        successful_deliveries = deliveries.filter(status='delivered').count()
        failed_deliveries = deliveries.filter(status='failed').count()
        
        delivery_success_rate = 0
        if total_deliveries > 0:
            delivery_success_rate = successful_deliveries / total_deliveries
        
        # Delivery method distribution
        method_dist = dict(deliveries.values('delivery_method').annotate(count=Count('id')).values_list('delivery_method', 'count'))
        
        # Recent alerts
        recent_alerts = queryset.filter(sent_at__isnull=False).order_by('-sent_at')[:5]
        
        stats = {
            'total_alerts': total_alerts,
            'alerts_sent_today': alerts_today,
            'alerts_sent_this_week': alerts_week,
            'alerts_sent_this_month': alerts_month,
            'status_distribution': status_dist,
            'priority_distribution': priority_dist,
            'alert_type_distribution': type_dist,
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'delivery_success_rate': delivery_success_rate,
            'delivery_method_distribution': method_dist,
            'recent_alerts': recent_alerts
        }
        
        serializer = AlertSummarySerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create alerts for multiple regions"""
        serializer = BulkAlertCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            template_id = data['template_id']
            region_ids = data['region_ids']
            
            created_alerts = []
            
            for region_id in region_ids:
                alert_data = {
                    'template_id': template_id,
                    'region_id': region_id,
                    'title': data['title'],
                    'message': data['message'],
                    'sms_message': data.get('sms_message', ''),
                    'priority': data.get('priority', 'normal'),
                    'scheduled_send_time': data.get('scheduled_send_time'),
                }
                
                create_serializer = AlertCreateSerializer(
                    data=alert_data,
                    context={'request': request}
                )
                
                if create_serializer.is_valid():
                    alert = create_serializer.save()
                    created_alerts.append(alert)
            
            response_serializer = AlertSerializer(created_alerts, many=True)
            return Response({
                'message': f'Created {len(created_alerts)} alerts',
                'alerts': response_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlertDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing alert deliveries (read-only)
    """
    queryset = AlertDelivery.objects.all()
    serializer_class = AlertDeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['alert', 'recipient', 'delivery_method', 'status']
    ordering_fields = ['sent_at', 'delivered_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # If user is not admin, only show their own deliveries
        if not user.is_staff:
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.user_type not in ['admin', 'extension_officer']:
                    queryset = queryset.filter(recipient__user=user)
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get delivery performance metrics"""
        alert_id = request.query_params.get('alert_id')
        
        if not alert_id:
            return Response(
                {'error': 'alert_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            alert = Alert.objects.get(alert_id=alert_id)
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alert not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        deliveries = AlertDelivery.objects.filter(alert=alert)
        
        total_recipients = deliveries.count()
        delivered_count = deliveries.filter(status='delivered').count()
        read_count = deliveries.filter(status='read').count()
        failed_count = deliveries.filter(status='failed').count()
        
        delivery_rate = delivered_count / total_recipients if total_recipients > 0 else 0
        read_rate = read_count / delivered_count if delivered_count > 0 else 0
        failure_rate = failed_count / total_recipients if total_recipients > 0 else 0
        
        # Feedback metrics
        feedback = AlertFeedback.objects.filter(alert=alert)
        feedback_count = feedback.count()
        average_rating = feedback.aggregate(avg_rating=Avg('rating'))['avg_rating']
        action_taken_count = feedback.filter(action_taken=True).count()
        action_taken_rate = action_taken_count / feedback_count if feedback_count > 0 else 0
        
        performance = {
            'alert_id': alert.alert_id,
            'alert_title': alert.title,
            'sent_at': alert.sent_at,
            'total_recipients': total_recipients,
            'delivered_count': delivered_count,
            'read_count': read_count,
            'failed_count': failed_count,
            'delivery_rate': delivery_rate,
            'read_rate': read_rate,
            'failure_rate': failure_rate,
            'feedback_count': feedback_count,
            'average_rating': average_rating,
            'action_taken_count': action_taken_count,
            'action_taken_rate': action_taken_rate,
            'average_delivery_time': None  # Would calculate from timestamps
        }
        
        serializer = AlertPerformanceSerializer(performance)
        return Response(serializer.data)


class AlertSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alert subscriptions
    """
    queryset = AlertSubscription.objects.all()
    serializer_class = AlertSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user_profile', 'alert_type', 'is_subscribed']
    ordering_fields = ['created_at', 'alert_type']
    ordering = ['user_profile', 'alert_type']
    
    def get_queryset(self):
        """Filter to current user's subscriptions unless admin"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_staff:
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.user_type not in ['admin', 'extension_officer']:
                    queryset = queryset.filter(user_profile__user=user)
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """Get current user's subscriptions"""
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            subscriptions = AlertSubscription.objects.filter(user_profile=user_profile)
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Update multiple subscriptions at once"""
        subscriptions_data = request.data.get('subscriptions', [])
        
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            
            for sub_data in subscriptions_data:
                alert_type = sub_data.get('alert_type')
                is_subscribed = sub_data.get('is_subscribed', True)
                min_severity = sub_data.get('min_severity_level', 'moderate')
                
                subscription, created = AlertSubscription.objects.get_or_create(
                    user_profile=user_profile,
                    alert_type=alert_type,
                    defaults={
                        'is_subscribed': is_subscribed,
                        'min_severity_level': min_severity
                    }
                )
                
                if not created:
                    subscription.is_subscribed = is_subscribed
                    subscription.min_severity_level = min_severity
                    subscription.save()
            
            # Return updated subscriptions
            subscriptions = AlertSubscription.objects.filter(user_profile=user_profile)
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class AlertFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alert feedback
    """
    queryset = AlertFeedback.objects.all()
    serializer_class = AlertFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['alert', 'feedback_type', 'rating', 'action_taken']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter to current user's feedback unless admin"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_staff:
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.user_type not in ['admin', 'extension_officer']:
                    queryset = queryset.filter(user_profile__user=user)
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get feedback summary statistics"""
        alert_id = request.query_params.get('alert_id')
        
        queryset = self.get_queryset()
        if alert_id:
            queryset = queryset.filter(alert__alert_id=alert_id)
        
        total_feedback = queryset.count()
        
        # Rating distribution
        rating_dist = dict(queryset.filter(rating__isnull=False).values('rating').annotate(count=Count('id')).values_list('rating', 'count'))
        
        # Feedback type distribution
        type_dist = dict(queryset.values('feedback_type').annotate(count=Count('id')).values_list('feedback_type', 'count'))
        
        # Action taken
        action_taken = queryset.filter(action_taken=True).count()
        action_rate = action_taken / total_feedback if total_feedback > 0 else 0
        
        # Average rating
        avg_rating = queryset.aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        summary = {
            'total_feedback': total_feedback,
            'rating_distribution': rating_dist,
            'feedback_type_distribution': type_dist,
            'action_taken_count': action_taken,
            'action_taken_rate': action_rate,
            'average_rating': avg_rating
        }
        
        return Response(summary)