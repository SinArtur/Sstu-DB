# Исправление проблем при деплое на сервер

## Проблема 1: Конфликт с nginx.prod.conf

На сервере есть локальные изменения в `nginx/nginx.prod.conf`, которые нужно сохранить или перезаписать.

### Решение:

**Вариант 1: Сохранить локальные изменения (если они важны)**
```bash
# Сохраните текущую версию
cp nginx/nginx.prod.conf nginx/nginx.prod.conf.backup

# Сделайте stash локальных изменений
git stash

# Обновите код
git pull origin main

# Примените сохраненные изменения обратно (если нужно)
git stash pop
# Разрешите конфликты вручную, если они есть
```

**Вариант 2: Перезаписать локальные изменения (рекомендуется)**
```bash
# Сохраните текущую версию на всякий случай
cp nginx/nginx.prod.conf nginx/nginx.prod.conf.backup

# Отмените локальные изменения
git checkout -- nginx/nginx.prod.conf

# Обновите код
git pull origin main
```

## Проблема 2: Ошибка docker-compose с переменными окружения

Ошибка: `ERROR: Invalid interpolation format for "db" option in service "services"`

Это происходит из-за того, что docker-compose не может найти переменные окружения или использует старую версию.

### Решение:

**1. Убедитесь, что файл .env существует и содержит все необходимые переменные:**
```bash
cat .env
```

Должны быть определены:
```
DB_NAME=sstudb
DB_USER=sstudb_user
DB_PASSWORD=your_password
DEBUG=False
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=your-domain.com
# и другие переменные
```

**2. Проверьте версию docker-compose:**
```bash
docker-compose --version
```

Если версия ниже 2.1, обновите docker-compose или используйте альтернативный синтаксис.

**3. Используйте docker compose (v2) вместо docker-compose:**
```bash
# Вместо docker-compose используйте docker compose (без дефиса)
docker compose -f docker-compose.prod.yml exec backend pip install -r requirements.txt
```

**4. Или временно исправьте docker-compose.prod.yml:**

Если проблема сохраняется, можно временно заменить переменные на конкретные значения или использовать другой синтаксис. Но лучше убедиться, что .env файл правильно загружается.

**5. Проверьте, что .env файл загружается:**
```bash
# Убедитесь, что docker-compose видит переменные
docker-compose -f docker-compose.prod.yml config
```

Это покажет финальную конфигурацию с подставленными переменными.

## Полная последовательность команд для деплоя:

```bash
# 1. Сохраните текущий nginx.conf (на всякий случай)
cp nginx/nginx.prod.conf nginx/nginx.prod.conf.backup

# 2. Отмените локальные изменения в nginx
git checkout -- nginx/nginx.prod.conf

# 3. Обновите код
git pull origin main

# 4. Проверьте .env файл
cat .env | grep -E "DB_NAME|DB_USER|DB_PASSWORD"

# 5. Проверьте конфигурацию docker-compose
docker compose -f docker-compose.prod.yml config > /dev/null && echo "Config OK" || echo "Config ERROR"

# 6. Обновите зависимости
docker compose -f docker-compose.prod.yml exec backend pip install -r requirements.txt

# 7. Примените миграции
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 8. Соберите статические файлы
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# 9. Перезапустите контейнеры
docker compose -f docker-compose.prod.yml restart

# 10. Выполните первоначальную синхронизацию расписания
docker compose -f docker-compose.prod.yml exec backend python manage.py sync_schedule
```

## Если docker-compose v2 не установлен:

Установите docker-compose v2 или используйте обновленный синтаксис:

```bash
# Для Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Или используйте docker-compose с явным указанием .env файла
docker-compose --env-file .env -f docker-compose.prod.yml up -d
```

## Проверка после деплоя:

```bash
# Проверьте статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Проверьте логи
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Проверьте, что API работает
curl http://localhost:8000/api/schedule/groups/ -H "Authorization: Bearer YOUR_TOKEN"
```

