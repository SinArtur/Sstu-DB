"""
Admin configuration for materials app.
"""
from django.contrib import admin
from .models import Material, MaterialFile, MaterialRating, MaterialComment, MaterialTag


class MaterialFileInline(admin.TabularInline):
    """Inline admin for MaterialFile."""
    model = MaterialFile
    extra = 0
    readonly_fields = ['file_size', 'file_type', 'created_at']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    """Admin interface for Material model."""
    
    list_display = ['id', 'branch', 'author', 'status', 'average_rating', 'downloads_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['description', 'author__email', 'branch__name']
    readonly_fields = ['created_at', 'updated_at', 'moderated_at', 'average_rating', 'ratings_count']
    inlines = [MaterialFileInline]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('branch', 'author', 'description')
        }),
        ('Модерация', {
            'fields': ('status', 'moderator', 'moderation_comment', 'moderated_at')
        }),
        ('Статистика', {
            'fields': ('average_rating', 'ratings_count', 'downloads_count', 'views_count')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MaterialFile)
class MaterialFileAdmin(admin.ModelAdmin):
    """Admin interface for MaterialFile model."""
    
    list_display = ['original_name', 'material', 'file_size', 'file_type', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['original_name', 'material__description']
    readonly_fields = ['file_size', 'file_type', 'created_at']
    ordering = ['-created_at']


@admin.register(MaterialRating)
class MaterialRatingAdmin(admin.ModelAdmin):
    """Admin interface for MaterialRating model."""
    
    list_display = ['material', 'user', 'value', 'created_at']
    list_filter = ['value', 'created_at']
    search_fields = ['material__description', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(MaterialComment)
class MaterialCommentAdmin(admin.ModelAdmin):
    """Admin interface for MaterialComment model."""
    
    list_display = ['material', 'author', 'text_preview', 'parent', 'created_at']
    list_filter = ['created_at', 'is_deleted']
    search_fields = ['text', 'author__email', 'material__description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'


@admin.register(MaterialTag)
class MaterialTagAdmin(admin.ModelAdmin):
    """Admin interface for MaterialTag model."""
    
    list_display = ['name', 'materials_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
    filter_horizontal = ['materials']
    
    def materials_count(self, obj):
        return obj.materials.count()
    materials_count.short_description = 'Количество материалов'

