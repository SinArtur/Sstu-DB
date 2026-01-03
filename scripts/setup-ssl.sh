#!/bin/bash
# Скрипт для получения SSL сертификата для polikek.ru

set -e

DOMAIN="polikek.ru"
EMAIL="your-email@example.com"  # Замените на ваш email

echo "🔐 Настройка SSL сертификата для $DOMAIN"

# Проверка, что домен указывает на этот сервер
echo "📋 Проверка DNS..."
IP=$(curl -s ifconfig.me)
echo "IP адрес сервера: $IP"
echo "Убедитесь, что A-записи для $DOMAIN и www.$DOMAIN указывают на $IP"

read -p "DNS настроены? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Сначала настройте DNS записи на reg.ru:"
    echo "   Тип: A"
    echo "   Имя: @ (или пусто)"
    echo "   Значение: $IP"
    echo ""
    echo "   Тип: A"
    echo "   Имя: www"
    echo "   Значение: $IP"
    exit 1
fi

# Создание директории для сертификатов
echo "📁 Создание директории для сертификатов..."
mkdir -p nginx/ssl

# Остановка nginx временно для получения сертификата
echo "⏸️  Временно останавливаем nginx..."
docker compose -f docker-compose.prod.yml stop nginx || true

# Получение сертификата
echo "🔐 Получение SSL сертификата через Let's Encrypt..."
certbot certonly --standalone \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

# Копирование сертификатов
echo "📋 Копирование сертификатов..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/

# Установка правильных прав доступа
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem

echo "✅ Сертификаты скопированы в nginx/ssl/"

# Запуск nginx обратно
echo "▶️  Запуск nginx..."
docker compose -f docker-compose.prod.yml up -d nginx

echo "🎉 SSL сертификат успешно настроен!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Обновите ALLOWED_HOSTS в .env файле:"
echo "   ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN"
echo ""
echo "2. Перезапустите backend:"
echo "   docker compose -f docker-compose.prod.yml restart backend"
echo ""
echo "3. Проверьте сайт: https://$DOMAIN"

