# Инструкция по деплою обновления на сервер

## Что было добавлено:
1. **Модуль расписания** (`backend/schedule/`) - парсинг расписания с сайта СГТУ
2. **Новые зависимости**: `beautifulsoup4`, `requests`
3. **Celery** для периодической синхронизации расписания (каждые 3 часа)
4. **Новая страница** на фронтенде: `/schedule`

## Шаги для деплоя:

### 1. Подключитесь к серверу
```bash
ssh user@your-server
cd /path/to/project
```

### 2. Обновите код из GitHub
```bash
git pull origin main
```

### 3. Обновите зависимости
```bash
# В контейнере backend
docker-compose -f docker-compose.prod.yml exec backend pip install -r requirements.txt
```

### 4. Примените миграции
```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### 5. Соберите статические файлы
```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### 6. Перезапустите контейнеры
```bash
docker-compose -f docker-compose.prod.yml restart
```

### 7. Или используйте скрипт деплоя (полная пересборка)
```bash
bash scripts/deploy.sh
```

## Важные моменты:

### Настройка Celery (если еще не настроен)

1. **Убедитесь, что Redis запущен**:
```bash
docker-compose -f docker-compose.prod.yml up -d redis
```

2. **Запустите Celery worker**:
```bash
docker-compose -f docker-compose.prod.yml exec backend celery -A config worker -l info
```

3. **Запустите Celery beat** (для периодических задач):
```bash
docker-compose -f docker-compose.prod.yml exec backend celery -A config beat -l info
```

### Первоначальная синхронизация расписания

После деплоя нужно выполнить первоначальную синхронизацию:
```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py sync_schedule
```

Это может занять несколько минут, так как парсится расписание для всех групп.

### Проверка работы

1. Проверьте, что API работает:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://your-domain/api/schedule/groups/
```

2. Проверьте, что страница расписания открывается на фронтенде

3. Проверьте логи:
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery
```

## Обновление docker-compose.prod.yml (если нужно)

Если в `docker-compose.prod.yml` нет сервисов для Celery и Redis, добавьте:

```yaml
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  celery:
    build:
      context: ./backend
      dockerfile: ../docker/backend.Dockerfile
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery-beat:
    build:
      context: ./backend
      dockerfile: ../docker/backend.Dockerfile
    command: celery -A config beat -l info
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis
```

## Troubleshooting

### Если миграции не применяются:
```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py makemigrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Если расписание не синхронизируется:
- Проверьте логи парсера
- Убедитесь, что сайт rasp.sstu.ru доступен
- Проверьте настройки Celery в `backend/config/settings.py`

### Если фронтенд не показывает расписание:
- Проверьте консоль браузера на ошибки
- Убедитесь, что API возвращает данные
- Проверьте, что маршрут `/schedule` добавлен в `frontend/src/App.tsx`

