# 🚀 Быстрый старт: Модуль расписания

Минимальная инструкция для запуска модуля расписания СГТУ.

## 📋 Что нужно

- Python 3.12
- PostgreSQL (или SQLite для разработки)
- Redis
- Node.js

## ⚡ За 5 минут

### 1. Установка зависимостей

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Миграции

```bash
cd backend
python manage.py migrate
```

### 3. Загрузка расписания (опционально)

```bash
# Это займет несколько минут
python manage.py sync_schedule

# Или загрузите расписание только одной группы для теста
python manage.py sync_schedule --group 104
```

### 4. Запуск Redis

```bash
# Windows (Docker)
docker run -p 6379:6379 redis:alpine

# Linux/macOS
redis-server
```

### 5. Запуск Celery (в отдельных терминалах)

```bash
cd backend

# Терминал 1
celery -A config worker -l info --pool=solo  # Windows
# или
celery -A config worker -l info              # Linux/macOS

# Терминал 2
celery -A config beat -l info
```

### 6. Запуск приложения

```bash
# Backend (терминал 3)
cd backend
python manage.py runserver

# Frontend (терминал 4)
cd frontend
npm run dev
```

### 7. Использование

1. Откройте http://localhost:3000
2. Войдите в систему
3. Профиль → Выберите группу → Сохранить
4. Расписание → Просмотрите расписание

## 🎯 Минимальный вариант (без Celery)

Если не нужно автообновление:

```bash
# 1. Установка
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. Миграции
cd ../backend && python manage.py migrate

# 3. Загрузка расписания (опционально)
python manage.py sync_schedule --group 104

# 4. Запуск (2 терминала)
# Терминал 1:
cd backend && python manage.py runserver

# Терминал 2:
cd frontend && npm run dev
```

**Redis и Celery не обязательны** для базовой работы!

## 📝 Коды групп СГТУ

Найти код группы можно на сайте https://rasp.sstu.ru:
- Выберите институт и группу
- Скопируйте ID из URL: `https://rasp.sstu.ru/rasp/group/104` → код `104`

Примеры:
- б-РКЛМ-21: 104
- б-БИСТ-11: 328
- б-КТОП-11: 83

## 🔍 Проверка работы

### Backend API:
```bash
curl http://localhost:8000/api/schedule/groups/
```

### Frontend:
http://localhost:3000/schedule

### Django Admin:
http://localhost:8000/admin/schedule/

## ⚙️ Настройки

### Изменить периодичность обновления

Файл: `backend/config/celery.py`

```python
app.conf.beat_schedule = {
    'sync-schedules-every-3-hours': {
        'task': 'schedule.sync_all_schedules',
        'schedule': crontab(minute=0, hour='*/3'),  # Каждые 3 часа
    },
}
```

Измените на:
- `crontab(minute=0, hour='*/1')` - каждый час
- `crontab(minute=0, hour='*/6')` - каждые 6 часов
- `crontab(minute=0, hour=0)` - раз в день в полночь

## 🐛 Проблемы?

### Не видно расписания
1. Проверьте, что выбрана группа в профиле
2. Запустите `python manage.py sync_schedule --group 104`
3. Проверьте логи Django

### Celery не запускается
- Windows: используйте `--pool=solo`
- Убедитесь, что Redis запущен: `redis-cli ping` → `PONG`

### Ошибка подключения к БД
- Проверьте PostgreSQL: `psql -U postgres -l`
- Или используйте SQLite (настройки в `settings.py`)

## 📚 Подробная документация

- [Полная инструкция](SCHEDULE_SETUP.md)
- [Документация модуля](backend/schedule/README.md)
- [API Swagger](http://localhost:8000/api/swagger/)

---

**Готово! Наслаждайтесь расписанием! 📅**

