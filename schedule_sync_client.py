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
SYNC_INTERVAL_HOURS = int(os.getenv('SYNC_INTERVAL_HOURS', '3'))  # Каждые 3 часа
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

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


def sync_schedule():
    """Вызывает API для синхронизации расписания."""
    if not API_TOKEN:
        logger.error("API_TOKEN не установлен в .env файле!")
        return False
    
    url = f"{API_BASE_URL}/schedule/updates/trigger_sync_sync/"
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
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

