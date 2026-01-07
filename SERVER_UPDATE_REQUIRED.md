# Инструкция по обновлению сервера для поддержки клиентского парсинга

## Проблема: Ошибка 405 "Метод POST не разрешен" для эндпоинта `/api/schedule/updates/import_group/`

Это означает, что на сервере нет нового эндпоинта `import_group` в `ScheduleUpdateViewSet`.

## Решение: Обновить и перезапустить backend контейнер

### 1. Обновить код на сервере

```bash
cd ~/opt/Sstu-DB
git pull origin main
```

### 2. Проверить, что новый код есть

```bash
# Проверить, что метод import_group существует
grep -n "def import_group" backend/schedule/views.py

# Должна быть строка примерно 304:
# 304:    def import_group(self, request):
```

### 3. Пересобрать и перезапустить backend контейнер

```bash
# Пересобрать backend с новым кодом
docker compose -f docker-compose.prod.yml build backend

# Остановить старый контейнер
docker compose -f docker-compose.prod.yml stop backend

# Запустить новый контейнер
docker compose -f docker-compose.prod.yml up -d backend

# Или все в одной команде:
docker compose -f docker-compose.prod.yml up -d --build backend
```

### 4. Проверить логи backend

```bash
# Проверить, что backend запустился без ошибок
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Ищите ошибки типа:
# - ImportError
# - ModuleNotFoundError
# - SyntaxError
```

### 5. Проверить, что эндпоинт доступен

```bash
# Проверить через Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django.urls import reverse
from rest_framework.routers import DefaultRouter
from schedule.views import ScheduleUpdateViewSet

# Проверить, что метод существует
if hasattr(ScheduleUpdateViewSet, 'import_group'):
    print('✓ Метод import_group существует')
else:
    print('✗ Метод import_group НЕ существует!')

# Попробовать получить URL (требует настройки URL patterns)
try:
    print('✓ ViewSet зарегистрирован')
except Exception as e:
    print(f'✗ Ошибка: {e}')
"

# Или проверьте доступные URL через DRF
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django.urls import get_resolver
resolver = get_resolver()
# Найти все URL patterns
patterns = []
for pattern in resolver.url_patterns:
    if 'schedule' in str(pattern):
        patterns.append(str(pattern))
print('Schedule URLs:', patterns)
"
```

### 6. Проверить через API (требует токена админа)

```bash
# Проверить, что эндпоинт доступен (должен вернуть 401 или 403, но НЕ 405)
curl -X POST https://polikek.ru/api/schedule/updates/import_group/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{}' \
  -v

# Если возвращает 405 - эндпоинт не существует
# Если возвращает 400 - эндпоинт существует (но данные неправильные)
# Если возвращает 401/403 - эндпоинт существует (но нет авторизации)
```

### 7. Если эндпоинт все равно не работает

#### Вариант A: Проверить, что URL правильно настроен

```bash
# Проверить, что в backend/schedule/urls.py есть router.register для updates
grep -A 2 "router.register.*updates" backend/schedule/urls.py

# Должно быть:
# router.register(r'updates', ScheduleUpdateViewSet, basename='schedule-update')
```

#### Вариант B: Перезапустить все контейнеры

```bash
# Перезапустить все контейнеры
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

#### Вариант C: Проверить, что нет конфликтов в коде

```bash
# Проверить синтаксис Python файлов
docker compose -f docker-compose.prod.yml exec backend python -m py_compile backend/schedule/views.py

# Если есть ошибки - они будут выведены
```

### 8. После успешного обновления

Запустите клиентский скрипт снова:

```bash
# На вашем ПК
python schedule_sync_client.py --once
```

Должно работать без ошибок 405.

## Важно

- **НЕ используйте** `docker compose down -v` - это удалит volumes с данными!
- **Всегда проверяйте логи** после перезапуска контейнеров
- **Создавайте backup** базы данных перед обновлением (см. `DATABASE_BACKUP_RESTORE.md`)
