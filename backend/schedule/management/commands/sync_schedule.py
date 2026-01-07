"""
Management command to sync schedule data.
"""
from django.core.management.base import BaseCommand
from schedule.services import ScheduleSyncService


class Command(BaseCommand):
    help = 'Sync schedule data from SSTU website'

    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            type=int,
            help='Sync only specific group by SSTU ID',
        )

    def handle(self, *args, **options):
        service = ScheduleSyncService()
        
        group_id = options.get('group')
        
        if group_id:
            self.stdout.write(f'Syncing schedule for group {group_id}...')
            success = service.sync_single_group(group_id)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'Successfully synced group {group_id}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to sync group {group_id}'))
        else:
            self.stdout.write('Syncing all schedules...')
            self.stdout.write('This may take several minutes...')
            
            update = service.sync_all()
            
            if update.status == 'success':
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully synced schedules:\n'
                    f'  Groups updated: {update.groups_updated}\n'
                    f'  Lessons added: {update.lessons_added}\n'
                    f'  Lessons removed: {update.lessons_removed}'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Schedule sync failed: {update.error_message}'
                ))

