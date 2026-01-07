# Модуль расписания СГТУ

Модуль для парсинга и отображения расписания занятий с сайта СГТУ (rasp.sstu.ru).

## Возможности

- Автоматический парсинг расписания групп с сайта СГТУ
- Хранение информации об институтах, группах, преподавателях и занятиях
- Периодическое обновление расписания каждые 3 часа
- API для получения расписания
- Поиск и фильтрация по различным параметрам
- Персональное расписание для каждого студента

## Настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Миграции базы данных

```bash
python manage.py migrate
```

### 3. Первоначальная загрузка данных

Для загрузки всего расписания:

```bash
python manage.py sync_schedule
```

Для загрузки расписания конкретной группы:

```bash
python manage.py sync_schedule --group 104
```

где `104` - это SSTU ID группы (можно найти в URL на сайте rasp.sstu.ru)

### 4. Настройка Celery

Для автоматического обновления расписания каждые 3 часа необходимо запустить Celery worker и beat:

#### Windows (для разработки):

```bash
# В отдельных терминалах:

# Redis (должен быть установлен и запущен)
redis-server

# Celery worker
celery -A config worker -l info --pool=solo

# Celery beat (для периодических задач)
celery -A config beat -l info
```

#### Linux/macOS:

```bash
# Redis (должен быть установлен и запущен)
redis-server

# Celery worker
celery -A config worker -l info

# Celery beat
celery -A config beat -l info
```

## API Endpoints

### Институты

- `GET /api/schedule/institutes/` - список всех институтов
- `GET /api/schedule/institutes/{id}/` - информация об институте

### Группы

- `GET /api/schedule/groups/` - список всех групп
  - Параметры: `institute`, `education_form`, `degree_type`, `course_number`, `search`
- `GET /api/schedule/groups/{id}/` - информация о группе
- `GET /api/schedule/groups/my_group/` - группа текущего пользователя
- `POST /api/schedule/groups/{id}/sync/` - запустить синхронизацию для группы

### Преподаватели

- `GET /api/schedule/teachers/` - список преподавателей
  - Параметры: `search`
- `GET /api/schedule/teachers/{id}/` - информация о преподавателе

### Предметы

- `GET /api/schedule/subjects/` - список предметов
  - Параметры: `search`
- `GET /api/schedule/subjects/{id}/` - информация о предмете

### Занятия

- `GET /api/schedule/lessons/` - список занятий
  - Параметры: `group`, `subject`, `teacher`, `weekday`, `lesson_type`, `lesson_number`, `institute`, `date_from`, `date_to`, `search`
- `GET /api/schedule/lessons/{id}/` - информация о занятии
- `GET /api/schedule/lessons/my_schedule/` - расписание текущего пользователя
  - Параметры: `weekday`
- `GET /api/schedule/lessons/weekly/?group={id}` - недельное расписание группы

### Обновления

- `GET /api/schedule/updates/` - история обновлений
- `GET /api/schedule/updates/latest/` - последнее обновление
- `POST /api/schedule/updates/trigger_sync/` - запустить обновление (только для модераторов/админов)

## Модели

### Institute
Институт/факультет СГТУ

### Group
Учебная группа

### Teacher
Преподаватель

### Subject
Учебный предмет/дисциплина

### Lesson
Занятие в расписании

### ScheduleUpdate
Запись об обновлении расписания

## Использование на фронтенде

### Выбор группы в профиле

Пользователь может выбрать свою группу на странице профиля. После выбора группы:
- В навигации появится ссылка на расписание
- На странице расписания автоматически отобразится расписание выбранной группы

### Просмотр расписания

1. Перейти на страницу "Расписание"
2. Выбрать институт и группу (если еще не выбраны)
3. Использовать фильтры для поиска конкретных занятий
4. Просматривать расписание по дням недели

### Поиск

Поиск работает по:
- Названию предмета
- ФИО преподавателя
- Номеру аудитории

## Особенности парсинга

- Парсер обрабатывает HTML страницы с сайта rasp.sstu.ru
- Поддерживается парсинг:
  - Обычных занятий (лекции, практики, лабораторные)
  - Экзаменов с конкретными датами
  - Информации о преподавателях
  - Аудиторий
- При обновлении расписания старые данные не удаляются сразу, а помечаются как неактивные
- Если сайт СГТУ недоступен, используются старые данные

## Периодичность обновления

По умолчанию расписание обновляется каждые 3 часа. Это настраивается в `config/celery.py`:

```python
app.conf.beat_schedule = {
    'sync-schedules-every-3-hours': {
        'task': 'schedule.sync_all_schedules',
        'schedule': crontab(minute=0, hour='*/3'),  # Каждые 3 часа
    },
}
```

## Troubleshooting

### Расписание не загружается

1. Проверьте, что сайт rasp.sstu.ru доступен
2. Проверьте логи Django на наличие ошибок
3. Попробуйте запустить синхронизацию вручную: `python manage.py sync_schedule`

### Celery не запускается

1. Убедитесь, что Redis запущен
2. Проверьте настройки CELERY_BROKER_URL и CELERY_RESULT_BACKEND в settings.py
3. На Windows используйте флаг `--pool=solo`

### Парсер возвращает пустые данные

1. Проверьте, что структура HTML на сайте СГТУ не изменилась
2. Обновите селекторы в `schedule/parser.py` если необходимо

## Лицензия

MIT

