@echo off
REM Скрипт для однократного запуска синхронизации расписания

cd /d "%~dp0"

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.8+ и добавьте его в PATH
    pause
    exit /b 1
)

REM Запускаем однократную синхронизацию
echo Запуск однократной синхронизации расписания...
python schedule_sync_client.py --once

pause

