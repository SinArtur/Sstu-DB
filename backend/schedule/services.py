"""
Service for synchronizing schedule data from SSTU website.
"""
import logging
import os
from typing import List, Dict, Optional
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import Institute, Group, Teacher, Subject, Lesson, ScheduleUpdate
from .parser import SSTUScheduleParser

logger = logging.getLogger(__name__)


class ScheduleSyncService:
    """Service for synchronizing schedule data."""
    
    def __init__(self):
        # Get proxy from settings if available
        proxy = getattr(settings, 'SSTU_SCHEDULE_PROXY', None) or os.getenv('SSTU_SCHEDULE_PROXY')
        # Get Cloudflare Worker URL from settings if available
        cloudflare_worker_url = getattr(settings, 'SSTU_CLOUDFLARE_WORKER_URL', None) or os.getenv('SSTU_CLOUDFLARE_WORKER_URL')
        timeout = getattr(settings, 'SSTU_SCHEDULE_TIMEOUT', 60)  # Default 60 seconds
        # If using Cloudflare Worker, increase timeout as it may be slower
        if cloudflare_worker_url:
            timeout = max(timeout, 120)  # At least 120 seconds for Worker (it's slow)
        self.parser = SSTUScheduleParser(timeout=timeout, proxy=proxy, cloudflare_worker_url=cloudflare_worker_url)
        self.stats = {
            'groups_updated': 0,
            'lessons_added': 0,
            'lessons_removed': 0,
        }
    
    def sync_all(self) -> ScheduleUpdate:
        """Sync all schedule data."""
        update = ScheduleUpdate.objects.create(
            status=ScheduleUpdate.Status.IN_PROGRESS
        )
        
        try:
            logger.info("Starting schedule synchronization")
            
            # Parse main page
            institutes_data = self.parser.parse_main_page()
            if not institutes_data:
                raise Exception("Failed to parse main page")
            
            # Process each institute
            for institute_data in institutes_data:
                self._process_institute(institute_data)
            
            # Mark update as successful
            update.status = ScheduleUpdate.Status.SUCCESS
            update.finished_at = timezone.now()
            update.groups_updated = self.stats['groups_updated']
            update.lessons_added = self.stats['lessons_added']
            update.lessons_removed = self.stats['lessons_removed']
            update.save()
            
            logger.info(f"Schedule synchronization completed: {self.stats}")
            
        except Exception as e:
            logger.error(f"Schedule synchronization failed: {e}")
            update.status = ScheduleUpdate.Status.FAILED
            update.finished_at = timezone.now()
            update.error_message = str(e)
            update.save()
        
        return update
    
    def _process_institute(self, institute_data: Dict):
        """Process single institute and its groups."""
        # Get or create institute
        institute, _ = Institute.objects.get_or_create(
            sstu_id=institute_data.get('sstu_id'),
            defaults={'name': institute_data['name']}
        )
        
        # Update name if changed
        if institute.name != institute_data['name']:
            institute.name = institute_data['name']
            institute.save()
        
        # Process groups
        for group_data in institute_data['groups']:
            self._process_group(group_data, institute)
    
    def _process_group(self, group_data: Dict, institute: Institute):
        """Process single group and its schedule."""
        try:
            # Get or create group
            defaults = {
                'name': group_data['name'],
                'institute': institute,
                'education_form': group_data['education_form'],
                'degree_type': group_data['degree_type'],
                'course_number': group_data.get('course_number'),
            }
            
            if group_data.get('sstu_id'):
                group, created = Group.objects.get_or_create(
                    sstu_id=group_data['sstu_id'],
                    defaults=defaults
                )
                # Update fields if group exists
                if not created:
                    for key, value in defaults.items():
                        setattr(group, key, value)
                    group.save()
            else:
                group, created = Group.objects.get_or_create(
                    name=group_data['name'],
                    defaults=defaults
                )
            
            # Parse group schedule
            if group.sstu_id:
                self._sync_group_schedule(group)
                self.stats['groups_updated'] += 1
            
        except Exception as e:
            logger.error(f"Error processing group {group_data.get('name')}: {e}")
    
    @transaction.atomic
    def _sync_group_schedule(self, group: Group):
        """Sync schedule for specific group."""
        try:
            # Parse schedule
            lessons_data = self.parser.parse_group_schedule(group.sstu_id)
            
            if not lessons_data:
                logger.warning(f"No lessons found for group {group.name}")
                return
            
            # Mark all existing lessons as inactive
            old_lessons = Lesson.objects.filter(group=group, is_active=True)
            old_count = old_lessons.count()
            old_lessons.update(is_active=False)
            
            # Create or update lessons
            for lesson_data in lessons_data:
                self._create_or_update_lesson(lesson_data, group)
            
            # Remove old inactive lessons
            removed = Lesson.objects.filter(group=group, is_active=False).delete()[0]
            
            self.stats['lessons_added'] += len(lessons_data)
            self.stats['lessons_removed'] += removed
            
            logger.info(f"Synced {len(lessons_data)} lessons for group {group.name}")
            
        except Exception as e:
            logger.error(f"Error syncing schedule for group {group.name}: {e}")
            raise
    
    def _create_or_update_lesson(self, lesson_data: Dict, group: Group):
        """Create or update single lesson."""
        # Get or create subject
        subject, _ = Subject.objects.get_or_create(
            name=lesson_data['subject_name']
        )
        
        # Get or create teacher
        teacher = None
        if lesson_data.get('teacher_name'):
            teacher_defaults = {
                'full_name': lesson_data['teacher_name'],
            }
            if lesson_data.get('teacher_url'):
                teacher_defaults['sstu_profile_url'] = lesson_data['teacher_url']
            
            if lesson_data.get('teacher_id'):
                teacher, _ = Teacher.objects.get_or_create(
                    sstu_id=lesson_data['teacher_id'],
                    defaults=teacher_defaults
                )
            else:
                teacher, _ = Teacher.objects.get_or_create(
                    full_name=lesson_data['teacher_name'],
                    defaults=teacher_defaults
                )
        
        # Create lesson
        lesson_defaults = {
            'group': group,
            'subject': subject,
            'teacher': teacher,
            'lesson_type': lesson_data['lesson_type'],
            'room': lesson_data.get('room', ''),
            'weekday': lesson_data['weekday'],
            'lesson_number': lesson_data['lesson_number'],
            'start_time': lesson_data['start_time'],
            'end_time': lesson_data['end_time'],
            'specific_date': lesson_data.get('specific_date'),
            'week_number': lesson_data.get('week_number'),
            'is_active': True,
        }
        
        # Try to find existing lesson
        # Теперь все занятия имеют specific_date (дату из заголовка дня)
        # Ищем по группе, дате, дню недели, номеру пары, предмету и преподавателю
        lookup_fields = {
            'group': group,
            'weekday': lesson_data['weekday'],
            'lesson_number': lesson_data['lesson_number'],
            'subject': subject,
        }
        
        if lesson_data.get('specific_date'):
            lookup_fields['specific_date'] = lesson_data['specific_date']
        else:
            lookup_fields['specific_date__isnull'] = True
        
        # Если есть преподаватель, добавляем его в поиск для более точного совпадения
        if teacher:
            lookup_fields['teacher'] = teacher
        
        existing = Lesson.objects.filter(**lookup_fields).first()
        
        if existing:
            # Update existing lesson
            for key, value in lesson_defaults.items():
                setattr(existing, key, value)
            existing.save()
        else:
            # Create new lesson
            Lesson.objects.create(**lesson_defaults)
    
    def sync_single_group(self, group_id: int) -> bool:
        """Sync schedule for single group by SSTU ID."""
        try:
            group = Group.objects.get(sstu_id=group_id)
            self._sync_group_schedule(group)
            return True
        except Group.DoesNotExist:
            logger.error(f"Group with SSTU ID {group_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error syncing group {group_id}: {e}")
            return False

