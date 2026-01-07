"""Admin configuration for schedule app."""
from django.contrib import admin
from .models import Institute, Group, Teacher, Subject, Lesson, ScheduleUpdate


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('name', 'sstu_id', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'institute', 'education_form', 'degree_type', 'course_number', 'sstu_id')
    search_fields = ('name',)
    list_filter = ('institute', 'education_form', 'degree_type', 'course_number')
    ordering = ('name',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'sstu_id', 'created_at')
    search_fields = ('full_name',)
    list_filter = ('created_at',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('group', 'subject', 'teacher', 'weekday', 'lesson_number', 'lesson_type', 'room', 'is_active')
    search_fields = ('group__name', 'subject__name', 'teacher__full_name', 'room')
    list_filter = ('weekday', 'lesson_type', 'lesson_number', 'is_active', 'group__institute')
    ordering = ('group', 'weekday', 'lesson_number')


@admin.register(ScheduleUpdate)
class ScheduleUpdateAdmin(admin.ModelAdmin):
    list_display = ('started_at', 'finished_at', 'status', 'groups_updated', 'lessons_added', 'lessons_removed')
    list_filter = ('status', 'started_at')
    readonly_fields = ('started_at', 'finished_at', 'status', 'groups_updated', 'lessons_added', 'lessons_removed', 'error_message')

