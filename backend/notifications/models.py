"""
Notification models.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """User notification."""
    
    class NotificationType(models.TextChoices):
        MODERATION_APPROVED = 'moderation_approved', 'Модерация: одобрено'
        MODERATION_REJECTED = 'moderation_rejected', 'Модерация: отклонено'
        NEW_MATERIAL = 'new_material', 'Новый материал'
        NEW_COMMENT = 'new_comment', 'Новый комментарий'
        SYSTEM = 'system', 'Системное уведомление'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        verbose_name='Тип уведомления'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    message = models.TextField(
        verbose_name='Сообщение'
    )
    link = models.URLField(
        blank=True,
        null=True,
        verbose_name='Ссылка'
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Прочитано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} для {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])

