#!/bin/bash
# Script to restore basic branches (institutes and departments) on server

echo "=== Restoring Basic Branches ==="
cd ~/opt/Sstu-DB

echo ""
echo "1. Creating admin user (if doesn't exist)..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell <<'PYEOF'
from accounts.models import User

# Get or create admin
admin, created = User.objects.get_or_create(
    email='admin@university.local',
    defaults={
        'username': 'admin',
        'role': User.Role.ADMIN,
        'is_email_verified': True,
        'is_staff': True,
        'is_superuser': True,
    }
)

if created:
    admin.set_password('admin123')
    admin.save()
    print(f"✓ Created admin user: {admin.username}")
else:
    print(f"✓ Admin user already exists: {admin.username}")
PYEOF

echo ""
echo "2. Creating all institutes and departments..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_institutes

echo ""
echo "3. Checking created branches..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell <<'PYEOF'
from branches.models import Branch

institutes = Branch.objects.filter(type='institute', status='approved')
departments = Branch.objects.filter(type='department', status='approved')

print(f"\n✓ Institutes: {institutes.count()}")
for inst in institutes:
    print(f"  - {inst.name}")

print(f"\n✓ Departments: {departments.count()}")
print(f"  (Total departments under all institutes)")
PYEOF

echo ""
echo "=== Done ==="
echo "Visit https://polikek.ru to see the branches"

