#!/usr/bin/env python3
"""
Скрипт для автоматической синхронизации расписания с вашего компьютера.
Этот скрипт периодически вызывает API для обновления расписания.

Использование:
1. Установите зависимости: pip install requests schedule python-dotenv
2. Создайте файл .env с настройками (см. ниже)
3. Запустите скрипт: python schedule_sync_client.py

Для автозапуска:
- Windows: Добавьте в Планировщик заданий Windows
- Или запустите как службу через NSSM (Non-Sucking Service Manager)
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Попробуем импортировать schedule для периодического выполнения
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("ВНИМАНИЕ: Библиотека 'schedule' не установлена.")
    print("Установите её: pip install schedule")
    print("Скрипт будет работать в режиме однократного запуска.")

# Загружаем переменные окружения из .env файла
# Сначала пробуем schedule_sync_client.env, потом .env
env_path = Path(__file__).parent / 'schedule_sync_client.env'
if not env_path.exists():
    env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Настройки из переменных окружения
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')
API_TOKEN = os.getenv('API_TOKEN', '')
API_REFRESH_TOKEN = os.getenv('API_REFRESH_TOKEN', '')  # Refresh token для автоматического обновления
# Учетные данные для автоматического логина (если токены не указаны)
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
SYNC_INTERVAL_HOURS = int(os.getenv('SYNC_INTERVAL_HOURS', '3'))  # Каждые 3 часа
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Глобальные переменные для хранения токенов (могут обновляться)
_current_token = API_TOKEN
_current_refresh_token = API_REFRESH_TOKEN

# Настройка логирования
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'schedule_sync.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def login_and_get_tokens():
    """Автоматически логинится и получает токены через API."""
    global _current_token, _current_refresh_token
    
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        logger.error("ADMIN_EMAIL и ADMIN_PASSWORD не установлены в .env файле!")
        return False
    
    try:
        url = f"{API_BASE_URL}/auth/login/"
        response = requests.post(
            url,
            json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            _current_token = data.get('access')
            _current_refresh_token = data.get('refresh')
            
            if _current_token and _current_refresh_token:
                logger.info("Успешно получены токены через автоматический вход")
                # Опционально: сохранить токены в файл (можно закомментировать для безопасности)
                # save_tokens_to_env_file(_current_token, _current_refresh_token)
                return True
            else:
                logger.error("Не удалось получить токены из ответа API")
                return False
        else:
            error_msg = response.json().get('non_field_errors', ['Неизвестная ошибка'])
            logger.error(f"Ошибка входа (код {response.status_code}): {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при автоматическом входе: {str(e)}")
        return False


def refresh_access_token():
    """Обновляет access token используя refresh token."""
    global _current_token, _current_refresh_token
    
    refresh_token = _current_refresh_token or API_REFRESH_TOKEN
    
    if not refresh_token:
        logger.warning("Refresh token не установлен. Попытка автоматического входа...")
        # Пробуем автоматически войти
        if login_and_get_tokens():
            return True
        logger.error("Не удалось обновить токен и автоматически войти")
        return False
    
    try:
        url = f"{API_BASE_URL}/auth/token/refresh/"
        response = requests.post(url, json={'refresh': refresh_token}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            new_token = data.get('access')
            if new_token:
                _current_token = new_token
                logger.info("Токен доступа успешно обновлен")
                return True
            else:
                logger.error("Не удалось получить новый токен из ответа")
                # Пробуем автоматически войти
                logger.info("Пробую автоматический вход...")
                return login_and_get_tokens()
        else:
            logger.warning(f"Ошибка обновления токена (код {response.status_code}). Пробую автоматический вход...")
            # Если refresh token истек, пробуем автоматически войти
            return login_and_get_tokens()
    except Exception as e:
        logger.error(f"Ошибка при обновлении токена: {str(e)}")
        return False


def sync_schedule():
    """Вызывает API для синхронизации расписания."""
    global _current_token, _current_refresh_token
    
    # Если токен не установлен, пробуем автоматически войти
    if not _current_token and not API_TOKEN:
        if ADMIN_EMAIL and ADMIN_PASSWORD:
            logger.info("Токен не установлен, выполняю автоматический вход...")
            if not login_and_get_tokens():
                logger.error("Не удалось получить токены. Проверьте ADMIN_EMAIL и ADMIN_PASSWORD в .env файле.")
                return False
        else:
            logger.error("API_TOKEN не установлен и автоматический вход невозможен (нет ADMIN_EMAIL/ADMIN_PASSWORD)!")
            return False
    
    # Используем текущий токен (может быть обновлен)
    token = _current_token or API_TOKEN
    
    # URL для синхронной синхронизации (DRF action)
    url = f"{API_BASE_URL}/schedule/updates/trigger_sync_sync/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        logger.info("Начинаю синхронизацию расписания...")
        response = requests.post(url, headers=headers, timeout=600)  # 10 минут таймаут
        
        if response.status_code == 200:
            data = response.json()
            logger.info(
                f"Синхронизация успешно завершена! "
                f"Обновлено групп: {data.get('groups_updated', 0)}, "
                f"Добавлено занятий: {data.get('lessons_added', 0)}, "
                f"Удалено занятий: {data.get('lessons_removed', 0)}"
            )
            return True
        elif response.status_code == 401:
            # Токен истек, попробуем обновить
            logger.warning("Токен истек, пытаюсь обновить...")
            if refresh_access_token():
                # Повторяем запрос с новым токеном
                headers['Authorization'] = f'Bearer {_current_token}'
                response = requests.post(url, headers=headers, timeout=600)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        f"Синхронизация успешно завершена после обновления токена! "
                        f"Обновлено групп: {data.get('groups_updated', 0)}, "
                        f"Добавлено занятий: {data.get('lessons_added', 0)}, "
                        f"Удалено занятий: {data.get('lessons_removed', 0)}"
                    )
                    return True
                else:
                    logger.error(f"Ошибка синхронизации после обновления токена (код {response.status_code})")
                    return False
            else:
                logger.error("Не удалось обновить токен. Обновите токены вручную в файле .env")
                return False
        elif response.status_code == 403:
            logger.error("Ошибка доступа: У вас нет прав администратора")
            return False
        elif response.status_code == 400:
            error_msg = response.json().get('error', 'Неизвестная ошибка')
            logger.warning(f"Синхронизация уже выполняется: {error_msg}")
            return False
        else:
            error_msg = response.json().get('error', 'Неизвестная ошибка') if response.content else 'Нет ответа от сервера'
            logger.error(f"Ошибка синхронизации (код {response.status_code}): {error_msg}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к API. Синхронизация может занять много времени.")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Не удалось подключиться к API: {API_BASE_URL}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
        return False


def run_once():
    """Запускает синхронизацию один раз."""
    logger.info("=" * 60)
    logger.info("Запуск синхронизации расписания")
    logger.info(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    success = sync_schedule()
    
    logger.info("=" * 60)
    if success:
        logger.info("Синхронизация завершена успешно")
    else:
        logger.warning("Синхронизация завершена с ошибками")
    logger.info("=" * 60)
    
    return success


def run_scheduled():
    """Запускает синхронизацию по расписанию."""
    if not SCHEDULE_AVAILABLE:
        logger.error("Библиотека 'schedule' не установлена. Используйте режим однократного запуска.")
        return
    
    # Настраиваем расписание
    schedule.every(SYNC_INTERVAL_HOURS).hours.do(sync_schedule)
    
    # Первый запуск сразу
    logger.info("Запуск первой синхронизации...")
    sync_schedule()
    
    logger.info(f"Скрипт настроен на синхронизацию каждые {SYNC_INTERVAL_HOURS} часов")
    logger.info("Скрипт работает. Нажмите Ctrl+C для остановки.")
    
    # Основной цикл
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
    except KeyboardInterrupt:
        logger.info("Остановка скрипта по запросу пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)


def main():
    """Главная функция."""
    # Проверяем наличие токена
    if not API_TOKEN:
        logger.error("=" * 60)
        logger.error("ОШИБКА: API_TOKEN не установлен!")
        logger.error("=" * 60)
        logger.error("Создайте файл .env в той же папке, что и скрипт, со следующим содержимым:")
        logger.error("")
        logger.error("API_BASE_URL=http://your-server.com/api")
        logger.error("API_TOKEN=your_access_token_here")
        logger.error("SYNC_INTERVAL_HOURS=3")
        logger.error("LOG_LEVEL=INFO")
        logger.error("")
        logger.error("Чтобы получить токен:")
        logger.error("1. Войдите на сайт")
        logger.error("2. Откройте консоль браузера (F12)")
        logger.error("3. Выполните: localStorage.getItem('auth-storage')")
        logger.error("4. Найдите accessToken в JSON")
        logger.error("=" * 60)
        sys.exit(1)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            run_once()
        elif sys.argv[1] == '--help':
            print(__doc__)
        else:
            logger.error(f"Неизвестный аргумент: {sys.argv[1]}")
            print("Использование: python schedule_sync_client.py [--once|--help]")
    else:
        # По умолчанию запускаем в режиме расписания
        if SCHEDULE_AVAILABLE:
            run_scheduled()
        else:
            logger.warning("Библиотека 'schedule' не установлена. Запускаю однократную синхронизацию.")
            run_once()


if __name__ == '__main__':
    main()

