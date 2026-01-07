"""Views for schedule app."""
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from accounts.permissions import IsAdmin
from .models import Institute, Group, Teacher, Subject, Lesson, ScheduleUpdate
from .serializers import (
    InstituteSerializer, GroupListSerializer, GroupDetailSerializer,
    TeacherSerializer, SubjectSerializer, LessonSerializer,
    LessonDetailSerializer, ScheduleUpdateSerializer
)
from .tasks import sync_all_schedules, sync_single_group
from .services import ScheduleSyncService


class InstituteViewSet(viewsets.ReadOnlyModelViewSet):
    """Institute viewset."""
    
    queryset = Institute.objects.all()
    serializer_class = InstituteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """Group viewset."""
    
    queryset = Group.objects.select_related('institute').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['institute', 'education_form', 'degree_type', 'course_number']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    pagination_class = None  # Отключаем пагинацию для групп
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return GroupListSerializer
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Trigger schedule sync for specific group."""
        group = self.get_object()
        
        if not group.sstu_id:
            return Response(
                {'error': 'Group does not have SSTU ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task
        sync_single_group.delay(group.sstu_id)
        
        return Response({
            'message': f'Schedule sync started for group {group.name}',
            'group_id': group.id
        })
    
    @action(detail=False, methods=['get'])
    def my_group(self, request):
        """Get current user's group schedule."""
        user = request.user
        
        if not hasattr(user, 'group') or not user.group:
            return Response(
                {'error': 'User has no group assigned'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(user.group)
        return Response(serializer.data)


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    """Teacher viewset."""
    
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['full_name', 'created_at']
    ordering = ['full_name']
    pagination_class = None  # Отключаем пагинацию для преподавателей
    
    def list(self, request, *args, **kwargs):
        """Override list to do Python-level case-insensitive search for Cyrillic."""
        queryset = self.get_queryset()
        search = request.query_params.get('search', '').strip()
        
        if search:
            # Python-level filtering for proper Cyrillic case-insensitive search
            search_lower = search.lower()
            filtered_teachers = [
                teacher for teacher in queryset
                if search_lower in teacher.full_name.lower()
            ]
            serializer = self.get_serializer(filtered_teachers, many=True)
            return Response(serializer.data)
        
        return super().list(request, *args, **kwargs)


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """Subject viewset."""
    
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """Lesson viewset."""
    
    queryset = Lesson.objects.select_related(
        'group', 'group__institute', 'subject', 'teacher'
    ).filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group', 'subject', 'teacher', 'weekday', 'lesson_type', 'lesson_number']
    search_fields = ['subject__name', 'teacher__full_name', 'room']
    ordering_fields = ['weekday', 'lesson_number', 'start_time']
    ordering = ['weekday', 'lesson_number']
    pagination_class = None  # Отключаем пагинацию для занятий
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonSerializer
    
    def get_queryset(self):
        """Filter lessons based on query params."""
        queryset = super().get_queryset()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(
                Q(specific_date__gte=date_from) | Q(specific_date__isnull=True)
            )
        
        if date_to:
            queryset = queryset.filter(
                Q(specific_date__lte=date_to) | Q(specific_date__isnull=True)
            )
        
        # Filter by institute
        institute_id = self.request.query_params.get('institute')
        if institute_id:
            queryset = queryset.filter(group__institute_id=institute_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_schedule(self, request):
        """Get current user's schedule."""
        user = request.user
        
        if not hasattr(user, 'group') or not user.group:
            return Response(
                {'error': 'User has no group assigned'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get lessons for user's group
        lessons = self.get_queryset().filter(group=user.group)
        
        # Apply additional filters
        weekday = request.query_params.get('weekday')
        if weekday:
            lessons = lessons.filter(weekday=weekday)
        
        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get weekly schedule for a group."""
        group_id = request.query_params.get('group')
        
        if not group_id:
            return Response(
                {'error': 'group parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all lessons for the week, grouped by day
        lessons = self.get_queryset().filter(group=group).order_by('weekday', 'lesson_number')
        
        # Group by weekday
        weekly_schedule = {}
        for lesson in lessons:
            day = lesson.get_weekday_display()
            if day not in weekly_schedule:
                weekly_schedule[day] = []
            weekly_schedule[day].append(LessonSerializer(lesson).data)
        
        return Response({
            'group': GroupListSerializer(group).data,
            'schedule': weekly_schedule
        })


class ScheduleUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    """Schedule update viewset."""
    
    queryset = ScheduleUpdate.objects.all()
    serializer_class = ScheduleUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['status']
    ordering_fields = ['started_at', 'finished_at']
    ordering = ['-started_at']
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def trigger_sync(self, request):
        """Trigger full schedule synchronization (admin only)."""
        # Check if sync is already in progress
        in_progress = ScheduleUpdate.objects.filter(status=ScheduleUpdate.Status.IN_PROGRESS).exists()
        if in_progress:
            return Response(
                {'error': 'Schedule synchronization is already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task
        task = sync_all_schedules.delay()
        
        return Response({
            'message': 'Schedule synchronization started',
            'task_id': task.id
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def trigger_sync_sync(self, request):
        """Trigger full schedule synchronization synchronously (admin only)."""
        # Check if sync is already in progress
        in_progress = ScheduleUpdate.objects.filter(status=ScheduleUpdate.Status.IN_PROGRESS).exists()
        if in_progress:
            return Response(
                {'error': 'Schedule synchronization is already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Run sync synchronously
        try:
            service = ScheduleSyncService()
            update = service.sync_all()
            
            if update.status == ScheduleUpdate.Status.SUCCESS:
                return Response({
                    'message': 'Schedule synchronization completed successfully',
                    'groups_updated': update.groups_updated,
                    'lessons_added': update.lessons_added,
                    'lessons_removed': update.lessons_removed,
                    'update_id': update.id
                })
            else:
                return Response({
                    'error': update.error_message or 'Schedule synchronization failed',
                    'update_id': update.id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest schedule update."""
        latest = self.get_queryset().first()
        
        if not latest:
            return Response(
                {'error': 'No updates found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(latest)
        return Response(serializer.data)

