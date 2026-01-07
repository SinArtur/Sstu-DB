"""
Schedule models for storing parsed schedule data from SSTU website.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator

User = get_user_model()


class Institute(models.Model):
    """Institute (faculty) in SSTU."""
    
    name = models.CharField(
        max_length=300,
        unique=True,
        verbose_name='Название института'
    )
    sstu_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='ID в системе СГТУ'
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
        verbose_name = 'Институт'
        verbose_name_plural = 'Институты'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Group(models.Model):
    """Student group."""
    
    class EducationForm(models.TextChoices):
        FULL_TIME = 'full_time', 'Очная'
        PART_TIME = 'part_time', 'Заочная'
        EVENING = 'evening', 'Очно-заочная'
    
    class DegreeType(models.TextChoices):
        BACHELOR = 'bachelor', 'Бакалавриат'
        MASTER = 'master', 'Магистратура'
        SPECIALTY = 'specialty', 'Специалитет'
        POSTGRADUATE = 'postgraduate', 'Аспирантура'
    
    name = models.CharField(
        max_length=50,
        unique=True,
        validators=[MinLengthValidator(2)],
        verbose_name='Название группы'
    )
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='groups',
        null=True,
        blank=True,
        verbose_name='Институт'
    )
    sstu_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='ID в системе СГТУ'
    )
    education_form = models.CharField(
        max_length=20,
        choices=EducationForm.choices,
        default=EducationForm.FULL_TIME,
        verbose_name='Форма обучения'
    )
    degree_type = models.CharField(
        max_length=20,
        choices=DegreeType.choices,
        default=DegreeType.BACHELOR,
        verbose_name='Тип обучения'
    )
    course_number = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Курс'
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
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['name']
        indexes = [
            models.Index(fields=['institute', 'name']),
            models.Index(fields=['sstu_id']),
        ]
    
    def __str__(self):
        return self.name


class Teacher(models.Model):
    """Teacher."""
    
    full_name = models.CharField(
        max_length=200,
        verbose_name='ФИО преподавателя'
    )
    sstu_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='ID в системе СГТУ'
    )
    sstu_profile_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Ссылка на профиль СГТУ'
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
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['sstu_id']),
        ]
    
    def __str__(self):
        return self.full_name


class Subject(models.Model):
    """Subject/course."""
    
    name = models.CharField(
        max_length=300,
        verbose_name='Название предмета'
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
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Lesson(models.Model):
    """Single lesson in the schedule."""
    
    class LessonType(models.TextChoices):
        LECTURE = 'лек', 'Лекция'
        PRACTICE = 'пр', 'Практика'
        LAB = 'лаб', 'Лабораторная'
        EXAM = 'экз', 'Экзамен'
        CONSULTATION = 'конс', 'Консультация'
        OTHER = 'other', 'Другое'
    
    class Weekday(models.IntegerChoices):
        MONDAY = 1, 'Понедельник'
        TUESDAY = 2, 'Вторник'
        WEDNESDAY = 3, 'Среда'
        THURSDAY = 4, 'Четверг'
        FRIDAY = 5, 'Пятница'
        SATURDAY = 6, 'Суббота'
        SUNDAY = 7, 'Воскресенье'
    
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Группа'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Предмет'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        related_name='lessons',
        null=True,
        blank=True,
        verbose_name='Преподаватель'
    )
    lesson_type = models.CharField(
        max_length=10,
        choices=LessonType.choices,
        default=LessonType.LECTURE,
        verbose_name='Тип занятия'
    )
    room = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Аудитория'
    )
    weekday = models.IntegerField(
        choices=Weekday.choices,
        verbose_name='День недели'
    )
    lesson_number = models.IntegerField(
        verbose_name='Номер пары (1-6)'
    )
    start_time = models.TimeField(
        verbose_name='Время начала'
    )
    end_time = models.TimeField(
        verbose_name='Время окончания'
    )
    specific_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Конкретная дата (для экзаменов)'
    )
    week_number = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Номер недели'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    additional_info = models.TextField(
        blank=True,
        verbose_name='Дополнительная информация'
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
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['weekday', 'lesson_number', 'start_time']
        indexes = [
            models.Index(fields=['group', 'weekday', 'is_active']),
            models.Index(fields=['teacher', 'weekday']),
            models.Index(fields=['specific_date']),
            models.Index(fields=['week_number', 'weekday']),
        ]
    
    def __str__(self):
        return f"{self.group.name} - {self.subject.name} ({self.get_weekday_display()}, пара {self.lesson_number})"


class ScheduleUpdate(models.Model):
    """Track schedule parsing updates."""
    
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Успешно'
        FAILED = 'failed', 'Ошибка'
        IN_PROGRESS = 'in_progress', 'В процессе'
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Начало обновления'
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Окончание обновления'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        verbose_name='Статус'
    )
    groups_updated = models.IntegerField(
        default=0,
        verbose_name='Обновлено групп'
    )
    lessons_added = models.IntegerField(
        default=0,
        verbose_name='Добавлено занятий'
    )
    lessons_removed = models.IntegerField(
        default=0,
        verbose_name='Удалено занятий'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Сообщение об ошибке'
    )
    
    class Meta:
        verbose_name = 'Обновление расписания'
        verbose_name_plural = 'Обновления расписания'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Обновление от {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}"

