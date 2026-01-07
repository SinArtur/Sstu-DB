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

# Ensure UTF-8 output on Windows console (prevents garbled Cyrillic logs)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

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

# Настройки локального парсинга rasp.sstu.ru (на вашем ПК)
SSTU_TIMEOUT = int(os.getenv('SSTU_TIMEOUT', '60'))
SSTU_PROXY = os.getenv('SSTU_PROXY', '').strip() or None

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


def login_and_get_tokens(retries: int = 3):
    """Автоматически логинится и получает токены через API."""
    global _current_token, _current_refresh_token
    
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        logger.error("ADMIN_EMAIL и ADMIN_PASSWORD не установлены в .env файле!")
        return False
    
    url = f"{API_BASE_URL}/auth/login/"
    
    for attempt in range(retries):
        try:
            logger.info(f"Попытка входа (попытка {attempt + 1}/{retries})...")
            response = requests.post(
                url,
                json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD},
                headers={'Content-Type': 'application/json'},
                timeout=60  # Увеличил таймаут до 60 секунд
            )
        
            if response.status_code == 200:
                data = response.json()
                _current_token = data.get('access')
                _current_refresh_token = data.get('refresh')
                
                if _current_token and _current_refresh_token:
                    logger.info("Успешно получены токены через автоматический вход")
                    return True
                else:
                    logger.error("Не удалось получить токены из ответа API")
                    return False
            else:
                error_msg = response.json().get('non_field_errors', ['Неизвестная ошибка']) if response.content else 'Нет ответа'
                logger.error(f"Ошибка входа (код {response.status_code}): {error_msg}")
                if attempt < retries - 1:
                    logger.info(f"Повторная попытка через 5 секунд...")
                    time.sleep(5)
                    continue
                return False
        except requests.exceptions.Timeout as e:
            logger.warning(f"Таймаут подключения к серверу (попытка {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 10  # Увеличиваем время ожидания с каждой попыткой
                logger.info(f"Повторная попытка через {wait_time} секунд...")
                time.sleep(wait_time)
                continue
            logger.error(f"Не удалось подключиться к серверу после {retries} попыток. Проверьте доступность {API_BASE_URL}")
            logger.error("Возможно, сервер перезагружается или недоступен. Попробуйте позже.")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Ошибка подключения к серверу (попытка {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 10
                logger.info(f"Повторная попытка через {wait_time} секунд...")
                time.sleep(wait_time)
                continue
            logger.error(f"Не удалось подключиться к серверу после {retries} попыток. Проверьте доступность {API_BASE_URL}")
            logger.error("Возможно, сервер перезагружается или недоступен. Попробуйте позже.")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при автоматическом входе: {str(e)}")
            if attempt < retries - 1:
                logger.info(f"Повторная попытка через 5 секунд...")
                time.sleep(5)
                continue
            return False
    
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
    """
    Локально парсит rasp.sstu.ru (на вашем ПК) и загружает данные на сервер через API.
    Сервер НЕ делает никаких запросов к rasp.sstu.ru.
    """
    global _current_token, _current_refresh_token
    
    # Ensure we have an access token (login/refresh)
    if not _current_token and not API_TOKEN:
        if ADMIN_EMAIL and ADMIN_PASSWORD:
            logger.info("Токен не установлен, выполняю автоматический вход...")
            if not login_and_get_tokens():
                logger.error("Не удалось получить токены. Проверьте ADMIN_EMAIL и ADMIN_PASSWORD в schedule_sync_client.env")
                return False
        else:
            logger.error("Нет токена и нет ADMIN_EMAIL/ADMIN_PASSWORD — авторизация невозможна")
            return False

    def _get_token() -> str:
        return _current_token or API_TOKEN

    def _post_json(url: str, payload: dict, timeout: int = 600) -> requests.Response:
        headers = {'Authorization': f'Bearer {_get_token()}', 'Content-Type': 'application/json'}
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 401:
            logger.warning("Access token истек (401). Пробую обновить/перелогиниться...")
            if refresh_access_token():
                headers['Authorization'] = f'Bearer {_get_token()}'
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        return resp

    # Import parser from backend/schedule/parser.py without needing Django
    try:
        # Добавляем путь к backend в sys.path
        script_dir = Path(__file__).parent
        backend_dir = script_dir / 'backend'
        
        # Проверяем, что папка backend существует
        if not backend_dir.exists():
            logger.error(f"Папка 'backend' не найдена рядом со скриптом. Ожидается: {backend_dir}")
            return False
        
        # Добавляем backend в путь для импорта модуля schedule
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        
        # Импортируем парсер
        from backend.schedule.parser import SSTUScheduleParser  # type: ignore
    except ImportError as e:
        logger.error(f"Не удалось импортировать парсер. Убедитесь, что папка 'backend/schedule' существует. Ошибка: {e}")
        logger.error(f"Текущий путь скрипта: {script_dir}")
        logger.error(f"Ожидаемый путь к парсеру: {backend_dir / 'schedule' / 'parser.py'}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при импорте парсера: {e}", exc_info=True)
        return False

    parser = SSTUScheduleParser(timeout=SSTU_TIMEOUT, proxy=SSTU_PROXY, cloudflare_worker_url=None)

    logger.info("Начинаю локальный парсинг rasp.sstu.ru...")
    institutes = parser.parse_main_page()
    if not institutes:
        logger.error("Не удалось распарсить главную страницу rasp.sstu.ru (institutes пустой)")
        return False

    def _ser_time(t):
        if t is None:
            return None
        return t.strftime('%H:%M:%S')

    def _ser_date(d):
        if d is None:
            return None
        return d.isoformat()

    total_groups = 0
    ok_groups = 0
    total_lessons = 0

    import_url = f"{API_BASE_URL}/schedule/updates/import_group/"

    for inst in institutes:
        inst_payload = {'name': inst.get('name'), 'sstu_id': inst.get('sstu_id')}
        for grp in inst.get('groups', []) or []:
            group_sstu_id = grp.get('sstu_id')
            if not group_sstu_id:
                continue
            total_groups += 1
            group_payload = {
                'name': grp.get('name'),
                'sstu_id': group_sstu_id,
                'education_form': grp.get('education_form'),
                'degree_type': grp.get('degree_type'),
                'course_number': grp.get('course_number'),
            }

            lessons = parser.parse_group_schedule(group_sstu_id) or []
            total_lessons += len(lessons)

            lessons_payload = []
            for l in lessons:
                # Parser returns python date/time objects; convert to JSON-safe strings
                lessons_payload.append({
                    'subject_name': l.get('subject_name'),
                    'teacher_name': l.get('teacher_name'),
                    'teacher_id': l.get('teacher_id'),
                    'teacher_url': l.get('teacher_url'),
                    'lesson_type': l.get('lesson_type'),
                    'room': l.get('room'),
                    'weekday': l.get('weekday'),
                    'lesson_number': l.get('lesson_number'),
                    'start_time': _ser_time(l.get('start_time')),
                    'end_time': _ser_time(l.get('end_time')),
                    'specific_date': _ser_date(l.get('specific_date')),
                    'week_number': l.get('week_number'),
                    'additional_info': l.get('additional_info', ''),
                })

            payload = {
                'institute': inst_payload,
                'group': group_payload,
                'lessons': lessons_payload,
            }

            try:
                resp = _post_json(import_url, payload, timeout=60)  # Уменьшил таймаут до 60 секунд
                if resp.status_code == 200:
                    ok_groups += 1
                    try:
                        data = resp.json()
                        logger.info(
                            f"Импорт OK: {group_payload.get('name')} "
                            f"(создано: {data.get('lessons_created')}, обновлено: {data.get('lessons_updated')}, удалено: {data.get('lessons_removed')})"
                        )
                    except Exception:
                        logger.info(f"Импорт OK: {group_payload.get('name')}")
                elif resp.status_code == 405:
                    logger.error(
                        f"Импорт FAIL: {group_payload.get('name')} -> 405 (Метод POST не разрешен). "
                        f"Возможно, на сервере старый код без эндпоинта /api/schedule/updates/import_group/. "
                        f"Обновите сервер или проверьте URL."
                    )
                else:
                    logger.error(f"Импорт FAIL: {group_payload.get('name')} -> {resp.status_code} {resp.text[:200]}")
            except requests.exceptions.Timeout:
                logger.error(
                    f"Импорт FAIL: {group_payload.get('name')} -> Таймаут подключения к серверу. "
                    f"Проверьте доступность {API_BASE_URL}"
                )
            except requests.exceptions.ConnectionError as e:
                logger.error(
                    f"Импорт FAIL: {group_payload.get('name')} -> Ошибка подключения: {e}. "
                    f"Проверьте доступность {API_BASE_URL}"
                )
            except Exception as e:
                logger.error(f"Импорт FAIL: {group_payload.get('name')} -> Неожиданная ошибка: {e}")

    logger.info(f"Импорт завершен. Групп: {ok_groups}/{total_groups}, занятий распаршено: {total_lessons}")
    return ok_groups == total_groups


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
    # Проверяем наличие либо токена, либо учетных данных для автоматического входа
    if not API_TOKEN and not (ADMIN_EMAIL and ADMIN_PASSWORD):
        logger.error("=" * 60)
        logger.error("ОШИБКА: Не указаны данные для авторизации!")
        logger.error("=" * 60)
        logger.error("ВАРИАНТ 1 (РЕКОМЕНДУЕТСЯ): Автоматический вход")
        logger.error("Укажите в файле schedule_sync_client.env:")
        logger.error("  ADMIN_EMAIL=ваш_email@example.com")
        logger.error("  ADMIN_PASSWORD=ваш_пароль")
        logger.error("")
        logger.error("ВАРИАНТ 2: Ручной ввод токена")
        logger.error("Укажите в файле schedule_sync_client.env:")
        logger.error("  API_TOKEN=your_access_token_here")
        logger.error("  API_REFRESH_TOKEN=your_refresh_token_here (опционально)")
        logger.error("")
        logger.error("Файл должен находиться в той же папке, что и скрипт:")
        logger.error(f"  {env_path}")
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

