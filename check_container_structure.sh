#!/bin/bash
# Скрипт для проверки структуры контейнера

echo "Проверка структуры проекта в контейнере..."
docker compose -f docker-compose.prod.yml exec backend ls -la /app/

echo ""
echo "Проверка наличия schedule app..."
docker compose -f docker-compose.prod.yml exec backend ls -la /app/schedule/ 2>/dev/null || echo "Папка schedule не найдена"

echo ""
echo "Поиск файла views.py..."
docker compose -f docker-compose.prod.yml exec backend find /app -name "views.py" -type f | grep schedule

echo ""
echo "Проверка метода trigger_sync_sync..."
docker compose -f docker-compose.prod.yml exec backend find /app -name "views.py" -exec grep -l "trigger_sync_sync" {} \;

