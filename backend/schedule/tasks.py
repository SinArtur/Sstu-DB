"""
Celery tasks for schedule synchronization.
"""
from celery import shared_task
import logging
from .services import ScheduleSyncService

logger = logging.getLogger(__name__)


@shared_task(name='schedule.sync_all_schedules')
def sync_all_schedules():
    """
    Sync all schedules from SSTU website.
    This task should be run periodically (every 3 hours).
    """
    logger.info("Starting schedule synchronization task")
    service = ScheduleSyncService()
    update = service.sync_all()
    
    if update.status == 'success':
        logger.info(f"Schedule sync completed successfully: {update.groups_updated} groups updated")
        return {
            'status': 'success',
            'groups_updated': update.groups_updated,
            'lessons_added': update.lessons_added,
            'lessons_removed': update.lessons_removed,
        }
    else:
        logger.error(f"Schedule sync failed: {update.error_message}")
        return {
            'status': 'failed',
            'error': update.error_message,
        }


@shared_task(name='schedule.sync_single_group')
def sync_single_group(group_id: int):
    """
    Sync schedule for single group.
    
    Args:
        group_id: SSTU group ID
    """
    logger.info(f"Syncing schedule for group {group_id}")
    service = ScheduleSyncService()
    success = service.sync_single_group(group_id)
    
    if success:
        logger.info(f"Group {group_id} synced successfully")
        return {'status': 'success', 'group_id': group_id}
    else:
        logger.error(f"Failed to sync group {group_id}")
        return {'status': 'failed', 'group_id': group_id}

