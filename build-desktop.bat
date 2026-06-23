@echo off
REM Build the PharmaDesk desktop app: compile the React UI and collect it
REM into Django's static files so the local server can serve it.
setlocal
cd /d "%~dp0"

echo [1/3] Building React UI...
cd frontend
if not exist node_modules ( call npm install )
call npm run build
if errorlevel 1 ( echo Frontend build failed. & exit /b 1 )

echo [2/3] Collecting static files into Django...
cd ..\backend
call venv\Scripts\activate
python manage.py collectstatic --noinput
if errorlevel 1 ( echo collectstatic failed. & exit /b 1 )

echo [3/3] Applying migrations...
python manage.py migrate

echo.
echo Build complete. Launch with start-desktop.bat
endlocal
