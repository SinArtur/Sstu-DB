"""
Moderation log models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class ModerationLog(models.Model):
    """Log of moderation actions."""
    
    class ActionType(models.TextChoices):
        APPROVE = 'approve', 'Одобрено'
        REJECT = 'reject', 'Отклонено'
        DELETE = 'delete', 'Удалено'
        EDIT = 'edit', 'Отредактировано'
    
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='moderation_logs',
        null=True,
        verbose_name='Модератор'
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='Тип контента'
    )
    object_id = models.PositiveIntegerField(verbose_name='ID объекта')
    content_object = GenericForeignKey('content_type', 'object_id')
    action = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name='Действие'
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий'
    )
    previous_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Предыдущий статус'
    )
    new_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Новый статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата действия'
    )
    
    class Meta:
        verbose_name = 'Лог модерации'
        verbose_name_plural = 'Логи модерации'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['moderator', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} от {self.moderator} в {self.created_at}"


class SystemSettings(models.Model):
    """System settings."""
    
    key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Ключ'
    )
    value = models.JSONField(
        verbose_name='Значение'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Обновлено пользователем'
    )
    
    class Meta:
        verbose_name = 'Системная настройка'
        verbose_name_plural = 'Системные настройки'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key} = {self.value}"
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value."""
        try:
            setting = cls.objects.get(key=key)
            return setting.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, description='', user=None):
        """Set setting value."""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description, 'updated_by': user}
        )
        if not created:
            setting.value = value
            if description:
                setting.description = description
            if user:
                setting.updated_by = user
            setting.save()
        return setting

