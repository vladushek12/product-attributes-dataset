@echo off
set VENV_DIR=.venv
echo %VENV_DIR%

set PYTHON_SCRIPT=./src/data/komus/crawler.py

:: Активируем виртуальное окружение
call %VENV_DIR%\Scripts\activate

:: Запуск Python-скрипта с аргументами
python %PYTHON_SCRIPT% %*

:: Деактивируем окружение
deactivate