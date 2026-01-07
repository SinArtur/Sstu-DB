# Настройка прокси для доступа к rasp.sstu.ru

## Поиск публичного прокси

Публичные прокси можно найти на сайтах:
- https://www.proxy-list.download/
- https://free-proxy-list.net/
- https://www.proxyscrape.com/

**Важно:** Выбирайте прокси из России, так как сайт rasp.sstu.ru может быть доступен только из РФ.

## Формат прокси

Прокси должен быть в формате:
```
http://IP:PORT
```
или с авторизацией:
```
http://USERNAME:PASSWORD@IP:PORT
```

## Настройка на сервере

### 1. Найдите рабочий прокси

Проверьте прокси перед использованием:
```bash
# Проверьте доступность прокси
curl -x http://PROXY_IP:PORT https://rasp.sstu.ru/ --max-time 10

# Если работает, вы увидите HTML код страницы
```

### 2. Добавьте в .env файл

```bash
# Отредактируйте .env файл
nano .env

# Добавьте строки:
SSTU_SCHEDULE_PROXY=http://PROXY_IP:PORT
SSTU_SCHEDULE_TIMEOUT=120
```

### 3. Обновите код и пересоберите

```bash
git pull origin main
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
```

### 4. Проверьте синхронизацию

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py sync_schedule
```

## Альтернатива: Использование SOCKS5 прокси

Если у вас есть SOCKS5 прокси, можно использовать библиотеку `requests[socks]`:

```bash
# Установите дополнительную зависимость
docker compose -f docker-compose.prod.yml exec backend pip install requests[socks]

# В .env используйте формат:
# SSTU_SCHEDULE_PROXY=socks5://PROXY_IP:PORT
```

## Проверка работы прокси

После настройки проверьте логи:
```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50 | grep -i proxy
```

## Важные замечания

1. **Публичные прокси нестабильны** - они могут перестать работать в любой момент
2. **Безопасность** - не используйте публичные прокси для критичных данных
3. **Скорость** - публичные прокси могут быть медленными
4. **Блокировка** - некоторые прокси могут быть заблокированы сайтом

## Рекомендация

Для production лучше использовать:
- Собственный VPN/прокси сервер
- Российский VPS для парсинга
- Или парсить данные локально и загружать на сервер

