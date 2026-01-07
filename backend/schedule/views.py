"""Views for schedule app."""
from datetime import datetime, date as date_type, time as time_type
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

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def import_group(self, request):
        """
        Import one group's schedule from a client (admin only).
        This endpoint is meant for **client-side parsing**: the server will NOT fetch rasp.sstu.ru.

        Payload:
        {
          "institute": {"name": "...", "sstu_id": 1},
          "group": {"name": "...", "sstu_id": 123, "education_form": "...", "degree_type": "...", "course_number": 3},
          "lessons": [
            {
              "subject_name": "...",
              "teacher_name": "...",
              "teacher_id": 456,
              "teacher_url": "https://...",
              "lesson_type": "лек",
              "room": "7/006",
              "weekday": 1,
              "lesson_number": 1,
              "start_time": "08:00:00",
              "end_time": "09:30:00",
              "specific_date": "2026-01-12",
              "week_number": 1,
              "additional_info": ""
            }
          ]
        }
        """
        payload = request.data or {}
        institute_data = payload.get('institute') or {}
        group_data = payload.get('group') or {}
        lessons_data = payload.get('lessons') or []

        if not institute_data.get('name'):
            return Response({'error': 'Missing institute.name'}, status=status.HTTP_400_BAD_REQUEST)
        if not group_data.get('sstu_id') or not group_data.get('name'):
            return Response({'error': 'Missing group.sstu_id or group.name'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(lessons_data, list):
            return Response({'error': 'lessons must be a list'}, status=status.HTTP_400_BAD_REQUEST)

        def _parse_date(value):
            if value in (None, '', 'null'):
                return None
            if isinstance(value, date_type):
                return value
            return datetime.strptime(str(value), '%Y-%m-%d').date()

        def _parse_time(value):
            if value in (None, '', 'null'):
                return None
            if isinstance(value, time_type):
                return value
            s = str(value)
            for fmt in ('%H:%M:%S', '%H:%M'):
                try:
                    return datetime.strptime(s, fmt).time()
                except ValueError:
                    continue
            raise ValueError(f"Invalid time format: {s}")

        # Upsert institute
        inst_sstu_id = institute_data.get('sstu_id')
        if inst_sstu_id is not None:
            institute, _ = Institute.objects.get_or_create(
                sstu_id=inst_sstu_id,
                defaults={'name': institute_data['name']}
            )
            if institute.name != institute_data['name']:
                institute.name = institute_data['name']
                institute.save(update_fields=['name'])
        else:
            institute, _ = Institute.objects.get_or_create(
                name=institute_data['name'],
                defaults={'sstu_id': None}
            )

        # Upsert group
        defaults = {
            'name': group_data['name'],
            'institute': institute,
            'education_form': group_data.get('education_form') or Group.EducationForm.FULL_TIME,
            'degree_type': group_data.get('degree_type') or Group.DegreeType.BACHELOR,
            'course_number': group_data.get('course_number'),
        }
        group, created = Group.objects.get_or_create(
            sstu_id=group_data['sstu_id'],
            defaults=defaults
        )
        if not created:
            changed = False
            for k, v in defaults.items():
                if getattr(group, k) != v:
                    setattr(group, k, v)
                    changed = True
            if changed:
                group.save()

        # Mark old lessons inactive
        Lesson.objects.filter(group=group, is_active=True).update(is_active=False)

        created_count = 0
        updated_count = 0

        # De-dupe incoming lessons to reduce duplicates from parsing glitches
        seen = set()
        normalized_lessons = []
        for l in lessons_data:
            if not isinstance(l, dict):
                continue
            key = (
                l.get('specific_date'),
                l.get('weekday'),
                l.get('lesson_number'),
                (l.get('subject_name') or '').strip(),
                (l.get('teacher_name') or '').strip(),
                (l.get('room') or '').strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            normalized_lessons.append(l)

        for lesson_data in normalized_lessons:
            try:
                subject_name = (lesson_data.get('subject_name') or '').strip()
                if not subject_name:
                    continue

                subject, _ = Subject.objects.get_or_create(name=subject_name)

                teacher = None
                teacher_name = (lesson_data.get('teacher_name') or '').strip()
                teacher_id = lesson_data.get('teacher_id')
                teacher_url = lesson_data.get('teacher_url')
                if teacher_name:
                    teacher_defaults = {'full_name': teacher_name}
                    if teacher_url:
                        teacher_defaults['sstu_profile_url'] = teacher_url
                    if teacher_id is not None:
                        teacher, _ = Teacher.objects.get_or_create(
                            sstu_id=teacher_id,
                            defaults=teacher_defaults
                        )
                        # keep name/url in sync
                        if teacher.full_name != teacher_name or (teacher_url and teacher.sstu_profile_url != teacher_url):
                            teacher.full_name = teacher_name
                            if teacher_url:
                                teacher.sstu_profile_url = teacher_url
                            teacher.save()
                    else:
                        teacher, _ = Teacher.objects.get_or_create(
                            full_name=teacher_name,
                            defaults=teacher_defaults
                        )

                specific_date = _parse_date(lesson_data.get('specific_date'))
                start_time = _parse_time(lesson_data.get('start_time'))
                end_time = _parse_time(lesson_data.get('end_time'))
                weekday = int(lesson_data.get('weekday'))
                lesson_number = int(lesson_data.get('lesson_number'))

                lesson_defaults = {
                    'group': group,
                    'subject': subject,
                    'teacher': teacher,
                    'lesson_type': lesson_data.get('lesson_type') or Lesson.LessonType.OTHER,
                    'room': lesson_data.get('room') or '',
                    'weekday': weekday,
                    'lesson_number': lesson_number,
                    'start_time': start_time,
                    'end_time': end_time,
                    'specific_date': specific_date,
                    'week_number': lesson_data.get('week_number'),
                    'additional_info': lesson_data.get('additional_info') or '',
                    'is_active': True,
                }

                lookup = {
                    'group': group,
                    'weekday': weekday,
                    'lesson_number': lesson_number,
                    'subject': subject,
                }
                if specific_date is not None:
                    lookup['specific_date'] = specific_date
                else:
                    lookup['specific_date__isnull'] = True
                if teacher:
                    lookup['teacher'] = teacher

                existing = Lesson.objects.filter(**lookup).first()
                if existing:
                    for k, v in lesson_defaults.items():
                        setattr(existing, k, v)
                    existing.save()
                    updated_count += 1
                else:
                    Lesson.objects.create(**lesson_defaults)
                    created_count += 1
            except Exception:
                # Skip bad lesson rows but keep import going
                continue

        removed_count = Lesson.objects.filter(group=group, is_active=False).delete()[0]

        return Response({
            'message': 'Imported group schedule',
            'group_id': group.id,
            'group_name': group.name,
            'lessons_received': len(lessons_data),
            'lessons_deduped': len(normalized_lessons),
            'lessons_created': created_count,
            'lessons_updated': updated_count,
            'lessons_removed': removed_count,
        })

