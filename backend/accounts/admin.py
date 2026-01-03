"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, InviteToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = ['email', 'username', 'role', 'is_email_verified', 'is_blocked', 'can_access_admin_panel', 'created_at']
    list_filter = ['role', 'is_email_verified', 'is_blocked', 'can_access_admin_panel', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'is_email_verified', 'email_verification_token', 'is_blocked', 'can_access_admin_panel')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'email')
        }),
    )


@admin.register(InviteToken)
class InviteTokenAdmin(admin.ModelAdmin):
    """Admin interface for InviteToken model."""
    
    list_display = ['code', 'creator', 'used', 'used_by', 'created_at', 'used_at']
    list_filter = ['used', 'created_at', 'used_at']
    search_fields = ['code', 'creator__email', 'used_by__email']
    readonly_fields = ['code', 'created_at', 'used_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'creator', 'created_at')
        }),
        ('Использование', {
            'fields': ('used', 'used_by', 'used_at')
        }),
    )

