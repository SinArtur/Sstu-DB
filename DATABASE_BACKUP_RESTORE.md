# Инструкция по сохранению и восстановлению базы данных

## Проблема: База данных стирается при пересборке контейнеров

### Причины:
1. Volume `postgres_data` удаляется при `docker compose down -v`
2. Backend использует SQLite вместо PostgreSQL из-за неправильного парсинга `DATABASE_URL`

## Решение:

### 1. Проверьте, что volume существует и не удаляется

```bash
# Проверить существующие volumes
docker volume ls | grep postgres_data

# Проверить информацию о volume
docker volume inspect Sstu-DB_postgres_data
```

### 2. НИКОГДА не используйте `docker compose down -v` на продакшене!

Команда `-v` удаляет volumes вместе с данными. Используйте просто:

```bash
# Остановить контейнеры БЕЗ удаления volumes
docker compose -f docker-compose.prod.yml down

# Перезапустить контейнеры (volumes сохранятся)
docker compose -f docker-compose.prod.yml up -d
```

### 3. Создайте резервную копию базы данных

```bash
# Создать backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U ${DB_USER:-sstudb_user} ${DB_NAME:-sstudb} > backup_$(date +%Y%m%d_%H%M%S).sql

# Или с указанием пароля через переменную окружения
docker compose -f docker-compose.prod.yml exec -e PGPASSWORD=${DB_PASSWORD} db pg_dump -U ${DB_USER:-sstudb_user} ${DB_NAME:-sstudb} > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. Восстановить из backup

```bash
# Остановить backend (чтобы не было активных подключений)
docker compose -f docker-compose.prod.yml stop backend

# Восстановить из backup
docker compose -f docker-compose.prod.yml exec -T db psql -U ${DB_USER:-sstudb_user} ${DB_NAME:-sstudb} < backup_YYYYMMDD_HHMMSS.sql

# Или с паролем
docker compose -f docker-compose.prod.yml exec -T -e PGPASSWORD=${DB_PASSWORD} db psql -U ${DB_USER:-sstudb_user} ${DB_NAME:-sstudb} < backup_YYYYMMDD_HHMMSS.sql

# Запустить backend
docker compose -f docker-compose.prod.yml start backend
```

### 5. Проверьте, что backend использует PostgreSQL

```bash
# Проверить логи backend при запуске
docker compose -f docker-compose.prod.yml logs backend | grep -i "database\|postgres\|sqlite"

# Проверить настройки DATABASE в Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django.conf import settings
print('Database ENGINE:', settings.DATABASES['default']['ENGINE'])
print('Database NAME:', settings.DATABASES['default']['NAME'])
print('Database HOST:', settings.DATABASES['default'].get('HOST', 'N/A'))
"
```

### 6. Если база данных все равно стирается:

#### Вариант A: Явно указать имя volume в docker-compose.prod.yml

```yaml
volumes:
  postgres_data:
    name: sstudb_postgres_data  # Явное имя volume
```

#### Вариант B: Использовать named volume с external: true

```yaml
volumes:
  postgres_data:
    external: true
    name: sstudb_postgres_data
```

Создать volume вручную:
```bash
docker volume create sstudb_postgres_data
```

### 7. Автоматическое резервное копирование (cron job)

Добавьте в crontab (`crontab -e`):

```bash
# Резервное копирование базы данных каждый день в 2:00
0 2 * * * cd /root/opt/Sstu-DB && docker compose -f docker-compose.prod.yml exec -T -e PGPASSWORD=$(grep DB_PASSWORD .env | cut -d '=' -f2) db pg_dump -U $(grep DB_USER .env | cut -d '=' -f2) $(grep DB_NAME .env | cut -d '=' -f2) > /root/backups/sstudb_$(date +\%Y\%m\%d).sql && find /root/backups -name "sstudb_*.sql" -mtime +7 -delete
```

## Проверка после пересборки:

```bash
# 1. Проверить, что volume существует
docker volume ls | grep postgres

# 2. Проверить, что контейнер PostgreSQL использует volume
docker compose -f docker-compose.prod.yml exec db psql -U ${DB_USER:-sstudb_user} -d ${DB_NAME:-sstudb} -c "SELECT COUNT(*) FROM accounts_user;"

# 3. Если таблицы пустые, значит volume был удален или пересоздан
```

## Если данные потеряны:

1. Восстановите из последнего backup (если есть)
2. Или пересоздайте суперпользователя:
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
   ```
3. Запустите синхронизацию расписания через клиентский скрипт

