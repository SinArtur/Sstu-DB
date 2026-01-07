"""
Management command to create test data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import InviteToken
from branches.models import Branch

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for development'

    def handle(self, *args, **options):
        # Create admin user
        admin, created = User.objects.get_or_create(
            email='admin@university.local',
            defaults={
                'username': 'admin',
                'role': User.Role.ADMIN,
                'is_email_verified': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create moderator user
        moderator, created = User.objects.get_or_create(
            email='moderator@university.local',
            defaults={
                'username': 'moderator',
                'role': User.Role.MODERATOR,
                'is_email_verified': True,
            }
        )
        if created:
            moderator.set_password('mod123')
            moderator.save()
            self.stdout.write(self.style.SUCCESS('Created moderator user'))

        # Create sample branches
        institute, created = Branch.objects.get_or_create(
            name='ИТИС',
            type=Branch.BranchType.INSTITUTE,
            defaults={
                'creator': admin,
                'status': Branch.Status.APPROVED,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created institute branch'))

        direction, created = Branch.objects.get_or_create(
            name='Программная инженерия',
            parent=institute,
            type=Branch.BranchType.DIRECTION,
            defaults={
                'creator': admin,
                'status': Branch.Status.APPROVED,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created direction branch'))

        subject, created = Branch.objects.get_or_create(
            name='Базы данных',
            parent=direction,
            type=Branch.BranchType.SUBJECT,
            defaults={
                'creator': admin,
                'status': Branch.Status.APPROVED,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created subject branch'))

        # Create invite tokens for admin
        InviteToken.create_for_user(admin, count=5)
        self.stdout.write(self.style.SUCCESS('Created invite tokens for admin'))

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))

