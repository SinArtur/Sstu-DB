"""
Admin configuration for moderation app.
"""
from django.contrib import admin
from .models import ModerationLog, SystemSettings


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    """Admin interface for ModerationLog model."""
    
    list_display = ['moderator', 'action', 'content_type', 'object_id', 'created_at']
    list_filter = ['action', 'content_type', 'created_at']
    search_fields = ['moderator__email', 'comment']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('moderator', 'content_type', 'object_id', 'action')
        }),
        ('Детали', {
            'fields': ('comment', 'previous_status', 'new_status')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin interface for SystemSettings model."""
    
    list_display = ['key', 'value', 'updated_by', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_at']
    ordering = ['key']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('key', 'value', 'description')
        }),
        ('Обновление', {
            'fields': ('updated_by', 'updated_at')
        }),
    )

