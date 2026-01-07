# Обновление кода на сервере для синхронизации

## Проблема

Endpoint `/api/schedule/updates/trigger_sync_sync/` возвращает 405 (Method Not Allowed), что означает, что на сервере используется старая версия кода без этого endpoint.

## Решение

Нужно обновить код на сервере:

```bash
# 1. Перейдите в директорию проекта
cd ~/opt/Sstu-DB

# 2. Обновите код из GitHub
git pull origin main

# 3. Пересоберите backend контейнер
docker compose -f docker-compose.prod.yml build backend

# 4. Перезапустите backend
docker compose -f docker-compose.prod.yml restart backend

# 5. Проверьте, что endpoint работает
curl -X POST https://polikek.ru/api/schedule/updates/trigger_sync_sync/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## Проверка после обновления

После обновления проверьте:

```bash
# Проверка через OPTIONS запрос (должен показать POST в Allow)
curl -X OPTIONS https://polikek.ru/api/schedule/updates/trigger_sync_sync/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v
```

Должно быть в заголовках:
```
Allow: GET, HEAD, OPTIONS, POST
```

## Альтернатива: Использование кнопки на сайте

Пока код не обновлен на сервере, можно использовать кнопку "Обновить расписание" на сайте (если она уже работает через другой endpoint).

