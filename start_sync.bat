@echo off
REM Скрипт для запуска синхронизации расписания в фоновом режиме
REM Этот файл можно добавить в автозагрузку Windows

cd /d "%~dp0"

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.8+ и добавьте его в PATH
    pause
    exit /b 1
)

REM Запускаем скрипт синхронизации
echo Запуск синхронизации расписания...
python schedule_sync_client.py

REM Если скрипт завершился с ошибкой, показываем сообщение
if errorlevel 1 (
    echo.
    echo Синхронизация завершилась с ошибкой.
    echo Проверьте файл logs/schedule_sync.log для подробностей.
    pause
)

