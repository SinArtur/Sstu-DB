#!/bin/bash
# Скрипт для настройки SSL сертификата для polikek.ru

set -e

DOMAIN="polikek.ru"
EMAIL="${1:-admin@polikek.ru}"  # Email для уведомлений Let's Encrypt

echo "🔒 Настройка SSL сертификата для $DOMAIN..."

# 1. Установите certbot (если не установлен)
if ! command -v certbot &> /dev/null; then
    echo "Установка certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot
fi

# 2. Остановите nginx контейнер временно (certbot нужен порт 80)
echo "Остановка nginx контейнера..."
cd ~/opt/Sstu-DB
docker compose -f docker-compose.prod.yml stop nginx

# 3. Получите сертификат
echo "Получение SSL сертификата..."
sudo certbot certonly --standalone \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

# 4. Создайте папку для SSL сертификатов (если не существует)
mkdir -p nginx/ssl

# 5. Скопируйте сертификаты
echo "Копирование сертификатов..."
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
sudo chown $USER:$USER nginx/ssl/*

# 6. Запустите nginx обратно
echo "Запуск nginx контейнера..."
docker compose -f docker-compose.prod.yml up -d nginx

echo "✅ SSL сертификат настроен!"
echo ""
echo "Следующие шаги:"
echo "1. Обновите nginx/nginx.prod.conf - раскомментируйте HTTPS блок"
echo "2. Перезапустите nginx: docker compose -f docker-compose.prod.yml restart nginx"
echo "3. Настройте автоматическое обновление сертификата (cron job)"

