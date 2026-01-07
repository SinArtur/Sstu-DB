"""Serializers for schedule app."""
from rest_framework import serializers
from .models import Institute, Group, Teacher, Subject, Lesson, ScheduleUpdate


class InstituteSerializer(serializers.ModelSerializer):
    """Institute serializer."""
    
    class Meta:
        model = Institute
        fields = ['id', 'name', 'sstu_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeacherSerializer(serializers.ModelSerializer):
    """Teacher serializer."""
    
    class Meta:
        model = Teacher
        fields = ['id', 'full_name', 'sstu_id', 'sstu_profile_url']
        read_only_fields = ['id']


class SubjectSerializer(serializers.ModelSerializer):
    """Subject serializer."""
    
    class Meta:
        model = Subject
        fields = ['id', 'name']
        read_only_fields = ['id']


class GroupListSerializer(serializers.ModelSerializer):
    """Group serializer for list views."""
    
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'sstu_id', 'institute', 'institute_name',
            'education_form', 'degree_type', 'course_number'
        ]
        read_only_fields = ['id']


class GroupDetailSerializer(serializers.ModelSerializer):
    """Group serializer for detail views."""
    
    institute = InstituteSerializer(read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'sstu_id', 'institute',
            'education_form', 'degree_type', 'course_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LessonSerializer(serializers.ModelSerializer):
    """Lesson serializer."""
    
    group_name = serializers.CharField(source='group.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True, allow_null=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    lesson_type_display = serializers.CharField(source='get_lesson_type_display', read_only=True)
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'group', 'group_name', 'subject', 'subject_name',
            'teacher', 'teacher_name', 'lesson_type', 'lesson_type_display',
            'room', 'weekday', 'weekday_display', 'lesson_number',
            'start_time', 'end_time', 'specific_date', 'week_number',
            'is_active', 'additional_info'
        ]
        read_only_fields = ['id']


class LessonDetailSerializer(serializers.ModelSerializer):
    """Lesson serializer with full details."""
    
    group = GroupListSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    teacher = TeacherSerializer(read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    lesson_type_display = serializers.CharField(source='get_lesson_type_display', read_only=True)
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'group', 'subject', 'teacher', 'lesson_type', 'lesson_type_display',
            'room', 'weekday', 'weekday_display', 'lesson_number',
            'start_time', 'end_time', 'specific_date', 'week_number',
            'is_active', 'additional_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScheduleUpdateSerializer(serializers.ModelSerializer):
    """Schedule update serializer."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ScheduleUpdate
        fields = [
            'id', 'started_at', 'finished_at', 'status', 'status_display',
            'groups_updated', 'lessons_added', 'lessons_removed', 'error_message'
        ]
        read_only_fields = ['id', 'started_at', 'finished_at', 'status', 
                           'groups_updated', 'lessons_added', 'lessons_removed', 'error_message']

