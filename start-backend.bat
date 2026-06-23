@echo off
REM Launch the local PharmaDesk API server on http://127.0.0.1:8000
cd /d "%~dp0backend"
call venv\Scripts\activate
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
