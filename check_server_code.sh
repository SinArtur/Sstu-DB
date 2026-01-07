#!/bin/bash
# Скрипт для проверки кода на сервере

echo "Проверка наличия метода trigger_sync_sync в views.py..."
docker compose -f docker-compose.prod.yml exec backend grep -n "trigger_sync_sync" config/schedule/views.py

echo ""
echo "Проверка последних изменений в views.py..."
docker compose -f docker-compose.prod.yml exec backend tail -50 config/schedule/views.py | grep -A 10 "trigger_sync"

