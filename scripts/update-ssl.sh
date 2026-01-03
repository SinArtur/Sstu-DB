#!/bin/bash
# Скрипт для обновления SSL сертификата

set -e

DOMAIN=${1:-yourdomain.com}

echo "🔒 Обновление SSL сертификата для $DOMAIN..."

# Обновление сертификата
sudo certbot renew --quiet

# Копирование сертификатов
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ~/sstudb/nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ~/sstudb/nginx/ssl/
sudo chown ubuntu:ubuntu ~/sstudb/nginx/ssl/*

# Перезапуск nginx
cd ~/sstudb
docker-compose -f docker-compose.prod.yml restart nginx

echo "✅ SSL сертификат обновлен!"







