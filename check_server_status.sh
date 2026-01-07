#!/bin/bash
# Скрипт для проверки состояния сервера и контейнеров

echo "=== Проверка Docker ==="
docker --version
docker compose version

echo ""
echo "=== Проверка запущенных контейнеров ==="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== Проверка логов backend (последние 50 строк) ==="
docker compose -f docker-compose.prod.yml logs backend --tail=50

echo ""
echo "=== Проверка логов frontend (последние 50 строк) ==="
docker compose -f docker-compose.prod.yml logs frontend --tail=50

echo ""
echo "=== Проверка логов nginx (последние 50 строк) ==="
docker compose -f docker-compose.prod.yml logs nginx --tail=50

echo ""
echo "=== Проверка использования ресурсов ==="
docker stats --no-stream

echo ""
echo "=== Проверка доступности портов ==="
netstat -tlnp | grep -E ':(80|443|8000|3000)' || ss -tlnp | grep -E ':(80|443|8000|3000)'

