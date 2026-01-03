"""
Serializers for moderation app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ModerationLog, SystemSettings

User = get_user_model()


class ModerationLogSerializer(serializers.ModelSerializer):
    """Serializer for ModerationLog model."""
    
    moderator_email = serializers.EmailField(source='moderator.email', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = ModerationLog
        fields = [
            'id', 'moderator', 'moderator_email', 'content_type', 'content_type_name',
            'object_id', 'action', 'action_display', 'comment',
            'previous_status', 'new_status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SystemSettings model."""
    
    updated_by_email = serializers.EmailField(source='updated_by.email', read_only=True)
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'updated_by', 'updated_by_email', 'updated_at']
        read_only_fields = ['id', 'updated_at']

