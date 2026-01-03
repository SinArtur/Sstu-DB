"""
Admin configuration for branches app.
"""
from django.contrib import admin
from .models import Branch, BranchRequest


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """Admin interface for Branch model."""
    
    list_display = ['name', 'type', 'parent', 'status', 'creator', 'created_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['name', 'creator__email']
    readonly_fields = ['created_at', 'updated_at', 'moderated_at']
    ordering = ['type', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('type', 'name', 'parent', 'creator')
        }),
        ('Модерация', {
            'fields': ('status', 'moderator', 'moderation_comment', 'moderated_at')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(BranchRequest)
class BranchRequestAdmin(admin.ModelAdmin):
    """Admin interface for BranchRequest model."""
    
    list_display = ['name', 'parent', 'requester', 'status', 'moderator', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'requester__email', 'parent__name']
    readonly_fields = ['created_at', 'moderated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('parent', 'name', 'requester')
        }),
        ('Модерация', {
            'fields': ('status', 'moderator', 'moderation_comment', 'moderated_at', 'created_branch')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )

