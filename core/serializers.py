from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Region, UserProfile


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Region
        fields = [
            'id', 'name', 'region_type', 'parent_region', 
            'latitude', 'longitude', 'area_sq_km', 'population',
            'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RegionSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for Region listings"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Region
        fields = ['id', 'name', 'region_type', 'full_name']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    user = UserSerializer(read_only=True)
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True, required=False)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_type', 'phone_number', 'region', 'region_id',
            'preferred_language', 'receive_whatsapp_alerts', 'receive_sms_alerts',
            'receive_email_alerts', 'farm_size_acres', 'primary_crops',
            'full_name', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating UserProfile with User"""
    user = UserSerializer()
    region_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'user_type', 'phone_number', 'region_id',
            'preferred_language', 'receive_whatsapp_alerts', 'receive_sms_alerts',
            'receive_email_alerts', 'farm_size_acres', 'primary_crops'
        ]
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        region_id = validated_data.pop('region_id', None)
        
        # Create user
        user = User.objects.create_user(**user_data)
        
        # Create user profile
        user_profile = UserProfile.objects.create(user=user, **validated_data)
        
        if region_id:
            try:
                region = Region.objects.get(id=region_id)
                user_profile.region = region
                user_profile.save()
            except Region.DoesNotExist:
                pass
        
        return user_profile