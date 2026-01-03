"""
Management command to create all institutes and departments.
"""
from django.core.management.base import BaseCommand
from django.db import models
from branches.models import Branch
from accounts.models import User


class Command(BaseCommand):
    help = 'Create all institutes and departments from the university structure'

    def handle(self, *args, **options):
        # Get or create admin user for creator
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            self.stdout.write(self.style.WARNING('No admin user found. Creating a default admin...'))
            admin_user = User.objects.create_user(
                email='admin@university.ru',
                username='admin',
                password='admin123',
                role='admin',
                is_email_verified=True
            )

        institutes_data = [
            {
                'name': 'ИНСТИТУТ ЭНЕРГЕТИКИ',
                'short_name': 'ИнЭН',
                'departments': [
                    {'name': 'Промышленная теплотехника', 'short': 'ПТ'},
                    {'name': 'Электроэнергетика и электротехника', 'short': 'ЭЛЭТ'},
                    {'name': 'Тепловая и атомная энергетика имени А.И. Андрющенко', 'short': 'ТАЭ'},
                ]
            },
            {
                'name': 'ИНСТИТУТ МАШИНОСТРОЕНИЯ, МАТЕРИАЛОВЕДЕНИЯ И ТРАНСПОРТА',
                'short_name': 'ИММТ',
                'departments': [
                    {'name': 'Сварка и металлургия', 'short': 'СМ'},
                    {'name': 'Технология машиностроения', 'short': 'ТМС'},
                    {'name': 'Техническая механика и мехатроника', 'short': 'ТММ'},
                    {'name': 'Материаловедение и биомедицинская инженерия', 'short': 'МБИ'},
                    {'name': 'Инженерная геометрия и основы САПР', 'short': 'ИГС'},
                    {'name': 'Организация перевозок, безопасность движения и сервис автомобилей', 'short': 'ОПБC'},
                ]
            },
            {
                'name': 'ИНСТИТУТ ЭЛЕКТРОННОЙ ТЕХНИКИ И ПРИБОРОСТРОЕНИЯ',
                'short_name': 'ИнЭТиП',
                'departments': [
                    {'name': 'Системотехника и управление в технических системах', 'short': 'СТУ'},
                    {'name': 'Радиоэлектроника и телекоммуникации', 'short': 'РТ'},
                    {'name': 'Приборостроение', 'short': 'ПБС'},
                    {'name': 'Электронные приборы и устройства', 'short': 'ЭПУ'},
                    {'name': 'Информационная безопасность автоматизированных систем', 'short': 'ИБС'},
                ]
            },
            {
                'name': 'ИНСТИТУТ ПРИКЛАДНЫХ ИНФОРМАЦИОННЫХ ТЕХНОЛОГИЙ И КОММУНИКАЦИЙ',
                'short_name': 'ИнПИТ',
                'departments': [
                    {'name': 'Информационно-коммуникационные системы и программная инженерия', 'short': 'ИКСП'},
                    {'name': 'Прикладные информационные технологии', 'short': 'ПИТ'},
                    {'name': 'Медиакоммуникации', 'short': 'МКМ'},
                    {'name': 'Переводоведение и межкультурная коммуникация', 'short': 'ПМК'},
                    {'name': 'Информационные системы и моделирование', 'short': 'ИСМ'},
                    {'name': 'Программное обеспечение вычислительных систем и компьютерных сетей', 'short': 'ПВКС'},
                ]
            },
            {
                'name': 'ФИЗИКО-ТЕХНИЧЕСКИЙ ИНСТИТУТ',
                'short_name': 'ФТИ',
                'departments': [
                    {'name': 'Математика и моделирование', 'short': 'МиМ'},
                    {'name': 'Прикладная математика и системный анализ', 'short': 'ПМиСА'},
                    {'name': 'Физика', 'short': 'ФИЗ'},
                    {'name': 'Химия и химическая технология материалов', 'short': 'ХИМ'},
                ]
            },
            {
                'name': 'ИНСТИТУТ УРБАНИСТИКИ, АРХИТЕКТУРЫ И СТРОИТЕЛЬСТВА',
                'short_name': 'УРБАС',
                'departments': [
                    {'name': 'Архитектура', 'short': 'АРХ'},
                    {'name': 'Дизайн архитектурной среды', 'short': 'ДАС'},
                    {'name': 'Теплогазоснабжение и нефтегазовое дело', 'short': 'ТНД'},
                    {'name': 'Строительные материалы, конструкции и технологии', 'short': 'СМКТ'},
                    {'name': 'Экология и техносферная безопасность', 'short': 'ЭТБ'},
                    {'name': 'Транспортное строительство', 'short': 'ТСТ'},
                ]
            },
            {
                'name': 'СОЦИАЛЬНО-ЭКОНОМИЧЕСКИЙ ИНСТИТУТ',
                'short_name': 'СЭИ',
                'departments': [
                    {'name': 'Бухгалтерского учета, анализа хозяйственной деятельности и аудита', 'short': 'БУХ'},
                    {'name': 'Производственный менеджмент', 'short': 'ПМН'},
                    {'name': 'Таможенного дела и товароведения', 'short': 'ТМЖ'},
                    {'name': 'Экономика и маркетинг', 'short': 'ЭКМ'},
                    {'name': 'Отраслевое управление и экономическая безопасность', 'short': 'ОУБ'},
                    {'name': 'Политология и социология', 'short': 'ПС'},
                    {'name': 'История и философия', 'short': 'ИФ'},
                    {'name': 'Иностранные языки и профессиональная коммуникация', 'short': 'ИПК'},
                    {'name': 'Физическая культура и спорт', 'short': 'ФКС'},
                ]
            },
        ]

        created_count = 0
        updated_count = 0

        for institute_data in institutes_data:
            # Create or get institute - use short name
            institute_name = institute_data['short_name']
            institute_full_name = institute_data['name']
            
            # Try to find existing institute by short name or full name
            institute = Branch.objects.filter(
                type=Branch.BranchType.INSTITUTE
            ).filter(
                models.Q(name=institute_name) | models.Q(name=institute_full_name)
            ).first()
            
            if institute:
                # Update existing institute
                if institute.name != institute_name:
                    old_name = institute.name
                    institute.name = institute_name
                    institute.status = Branch.Status.APPROVED
                    institute.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Обновлен институт: {institute_name} (было: {old_name})'))
                else:
                    updated_count += 1
                    if institute.status != Branch.Status.APPROVED:
                        institute.status = Branch.Status.APPROVED
                        institute.save()
                    self.stdout.write(self.style.WARNING(f'→ Институт уже существует: {institute_name}'))
            else:
                # Create new institute
                institute = Branch.objects.create(
                    type=Branch.BranchType.INSTITUTE,
                    name=institute_name,
                    creator=admin_user,
                    status=Branch.Status.APPROVED,
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Создан институт: {institute_name}'))

            # Create departments - use short name only
            for dept_data in institute_data['departments']:
                dept_short = dept_data['short']
                dept_full_name = dept_data['name']
                
                # Try to find existing department by short name or full name
                department = Branch.objects.filter(
                    type=Branch.BranchType.DEPARTMENT,
                    parent=institute
                ).filter(
                    models.Q(name=dept_short) | models.Q(name__contains=dept_short) | models.Q(name=dept_full_name)
                ).first()
                
                if department:
                    # Update existing department
                    if department.name != dept_short:
                        old_name = department.name
                        department.name = dept_short
                        department.status = Branch.Status.APPROVED
                        department.save()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Обновлена кафедра: {dept_short} (было: {old_name})'))
                    else:
                        updated_count += 1
                        if department.status != Branch.Status.APPROVED:
                            department.status = Branch.Status.APPROVED
                            department.save()
                else:
                    # Create new department
                    department = Branch.objects.create(
                        type=Branch.BranchType.DEPARTMENT,
                        name=dept_short,
                        parent=institute,
                        creator=admin_user,
                        status=Branch.Status.APPROVED,
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Создана кафедра: {dept_short}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Готово! Создано новых: {created_count}, обновлено существующих: {updated_count}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Всего институтов: {Branch.objects.filter(type=Branch.BranchType.INSTITUTE, status=Branch.Status.APPROVED).count()}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Всего кафедр: {Branch.objects.filter(type=Branch.BranchType.DEPARTMENT, status=Branch.Status.APPROVED).count()}'
        ))

