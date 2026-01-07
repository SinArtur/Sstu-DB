#!/bin/bash
# Проверка содержимого views.py в контейнере

echo "Проверка последних 100 строк views.py в контейнере:"
docker compose -f docker-compose.prod.yml exec backend tail -100 /app/schedule/views.py

echo ""
echo "Поиск всех методов trigger_sync:"
docker compose -f docker-compose.prod.yml exec backend grep -n "def trigger" /app/schedule/views.py

