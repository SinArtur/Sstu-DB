"""
Material models for file uploads, ratings, and comments.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import os

User = get_user_model()


def validate_file_extension(value):
    """Validate file extension."""
    from django.conf import settings
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(
            f'Файлы с расширением .{ext} не разрешены. '
            f'Разрешенные расширения: {", ".join(settings.ALLOWED_FILE_EXTENSIONS)}'
        )


def validate_file_size(value):
    """Validate file size."""
    from django.conf import settings
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(
            f'Размер файла превышает максимально допустимый ({settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB)'
        )


class Material(models.Model):
    """Material uploaded by user."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'На модерации'
        APPROVED = 'approved', 'Одобрено'
        REJECTED = 'rejected', 'Отклонено'
    
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='Ветка'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_materials',
        verbose_name='Автор'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Статус'
    )
    moderation_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий модератора'
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='moderated_materials',
        null=True,
        blank=True,
        verbose_name='Модератор'
    )
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата модерации'
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='Средняя оценка'
    )
    ratings_count = models.IntegerField(
        default=0,
        verbose_name='Количество оценок'
    )
    downloads_count = models.IntegerField(
        default=0,
        verbose_name='Количество скачиваний'
    )
    views_count = models.IntegerField(
        default=0,
        verbose_name='Количество просмотров'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['-average_rating', '-ratings_count']),
        ]
    
    def __str__(self):
        return f"Материал от {self.author.email} в {self.branch.name}"
    
    def update_rating(self):
        """Update average rating."""
        ratings = self.ratings.all()
        if ratings.exists():
            self.average_rating = ratings.aggregate(
                avg=models.Avg('value')
            )['avg'] or 0.00
            self.ratings_count = ratings.count()
        else:
            self.average_rating = 0.00
            self.ratings_count = 0
        self.save(update_fields=['average_rating', 'ratings_count'])
    
    def approve(self, moderator, comment=''):
        """Approve material."""
        self.status = self.Status.APPROVED
        self.moderator = moderator
        self.moderation_comment = comment
        from django.utils import timezone
        self.moderated_at = timezone.now()
        self.save()
    
    def reject(self, moderator, comment):
        """Reject material."""
        if not comment:
            raise ValueError("Comment is required for rejection")
        self.status = self.Status.REJECTED
        self.moderator = moderator
        self.moderation_comment = comment
        from django.utils import timezone
        self.moderated_at = timezone.now()
        self.save()


class MaterialFile(models.Model):
    """File attached to material."""
    
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='Материал'
    )
    file = models.FileField(
        upload_to='materials/%Y/%m/%d/',
        validators=[validate_file_extension, validate_file_size],
        verbose_name='Файл'
    )
    original_name = models.CharField(
        max_length=255,
        verbose_name='Оригинальное имя файла'
    )
    file_size = models.BigIntegerField(
        verbose_name='Размер файла (байты)'
    )
    file_type = models.CharField(
        max_length=50,
        verbose_name='Тип файла'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий к файлу'
    )
    upload_order = models.IntegerField(
        default=0,
        verbose_name='Порядок загрузки'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    
    class Meta:
        verbose_name = 'Файл материала'
        verbose_name_plural = 'Файлы материалов'
        ordering = ['upload_order', 'created_at']
    
    def __str__(self):
        return f"{self.original_name} ({self.material})"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = os.path.splitext(self.original_name)[1][1:].lower()
        super().save(*args, **kwargs)


class MaterialRating(models.Model):
    """Rating for material."""
    
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Материал'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='material_ratings',
        verbose_name='Пользователь'
    )
    value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка (1-5)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оценки'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Оценка материала'
        verbose_name_plural = 'Оценки материалов'
        unique_together = ['material', 'user']
        indexes = [
            models.Index(fields=['material', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.email} оценил {self.material} на {self.value}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.material.update_rating()
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.material.update_rating()


class MaterialComment(models.Model):
    """Comment on material."""
    
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Материал'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='material_comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
        verbose_name='Родительский комментарий'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Удален'
    )
    
    class Meta:
        verbose_name = 'Комментарий к материалу'
        verbose_name_plural = 'Комментарии к материалам'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['material', 'created_at']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"Комментарий от {self.author.email} к {self.material}"


class MaterialTag(models.Model):
    """Tag for material."""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Название тега'
    )
    materials = models.ManyToManyField(
        Material,
        related_name='tags',
        blank=True,
        verbose_name='Материалы'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Тег материала'
        verbose_name_plural = 'Теги материалов'
        ordering = ['name']
    
    def __str__(self):
        return self.name

