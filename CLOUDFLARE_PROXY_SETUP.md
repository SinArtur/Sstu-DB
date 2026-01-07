# Настройка Cloudflare Worker как прокси для rasp.sstu.ru

## Вариант 1: Использовать готовый Cloudflare Worker (рекомендуется)

### Шаги:

1. **Зарегистрируйтесь на Cloudflare** (бесплатно): https://dash.cloudflare.com/sign-up

2. **Создайте Worker:**
   - Перейдите в Workers & Pages → Create application → Create Worker
   - Назовите worker (например: `sstu-proxy`)
   - Вставьте код из файла `cloudflare-worker-proxy.js`
   - Нажмите "Deploy"

3. **Получите URL Worker:**
   - После деплоя вы получите URL вида: `https://sstu-proxy.YOUR_SUBDOMAIN.workers.dev`
   - Этот URL будет проксировать запросы к rasp.sstu.ru

4. **Настройте на сервере:**
   ```bash
   # В .env файл добавьте:
   SSTU_SCHEDULE_PROXY=http://YOUR_WORKER_URL.workers.dev?url=
   # Или используйте как базовый URL в парсере
   ```

## Вариант 2: Модифицировать парсер для использования Cloudflare Worker

Можно изменить парсер, чтобы он использовал Cloudflare Worker URL напрямую.

## Вариант 3: Использовать публичный прокси через Cloudflare

Если у вас есть доступ к прокси-серверу, который работает через Cloudflare, используйте его как обычный HTTP прокси.

## Настройка парсера для Cloudflare Worker

Если используете Worker, нужно изменить BASE_URL в парсере на URL Worker.

