#!/bin/bash
# Скрипт для полной переустановки проекта на сервере (БД сохраняется)

set -e  # Остановка при ошибке

echo "========================================="
echo "Переустановка проекта SSTU-DB"
echo "========================================="

cd ~/opt/Sstu-DB

echo ""
echo "=== 1. Создаем резервную копию БД ==="
BACKUP_FILE=~/backup_$(date +%Y%m%d_%H%M%S).sql
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U Sinan -d sstudb > "$BACKUP_FILE"
echo "Бэкап создан: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"

echo ""
echo "=== 2. Копируем .env файл ==="
cp .env ~/.env.backup
echo ".env сохранен в ~/.env.backup"

echo ""
echo "=== 3. Останавливаем и удаляем контейнеры ==="
docker compose -f docker-compose.prod.yml down -v

echo ""
echo "=== 4. Удаляем образы проекта ==="
docker images | grep sstu-db | awk '{print $3}' | xargs -r docker rmi -f || echo "Нет образов для удаления"

echo ""
echo "=== 5. Чистим Docker систему ==="
docker system prune -a -f

echo ""
echo "=== 6. Удаляем старый проект ==="
cd ~/opt
rm -rf Sstu-DB

echo ""
echo "=== 7. Клонируем проект заново ==="
git clone https://github.com/SinArtur/Sstu-DB.git
cd Sstu-DB

echo ""
echo "=== 8. Восстанавливаем .env файл ==="
cp ~/.env.backup .env
echo ".env восстановлен"

echo ""
echo "=== 9. Проверяем .env ==="
echo "Первые 10 строк .env:"
head -10 .env

echo ""
echo "=== 10. Запускаем только БД ==="
docker compose -f docker-compose.prod.yml up -d db

echo ""
echo "=== 11. Ждем запуска PostgreSQL (30 сек) ==="
sleep 30

echo ""
echo "=== 12. Восстанавливаем БД из бэкапа ==="
docker compose -f docker-compose.prod.yml exec -T db psql -U Sinan -d sstudb < "$BACKUP_FILE"
echo "БД восстановлена"

echo ""
echo "=== 13. Собираем все сервисы ==="
docker compose -f docker-compose.prod.yml build

echo ""
echo "=== 14. Запускаем все сервисы ==="
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "=== 15. Ждем запуска всех сервисов (20 сек) ==="
sleep 20

echo ""
echo "=== 16. Проверяем статус контейнеров ==="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== 17. Проверяем логи backend ==="
docker compose -f docker-compose.prod.yml logs --tail=20 backend

echo ""
echo "=== 18. Проверяем логи nginx ==="
docker compose -f docker-compose.prod.yml logs --tail=20 nginx

echo ""
echo "========================================="
echo "Переустановка завершена!"
echo "========================================="
echo ""
echo "Бэкап БД: $BACKUP_FILE"
echo "Бэкап .env: ~/.env.backup"
echo ""
echo "Проверь сайт: https://polikek.ru"

