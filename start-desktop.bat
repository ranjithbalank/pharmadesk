@echo off
REM Launch PharmaDesk as a desktop app (local Waitress server + window).
REM This is the single icon counter staff use. Add to Windows startup via
REM install-autostart.ps1 so it opens automatically at logon.
cd /d "%~dp0backend"
call venv\Scripts\activate
python desktop.py %*
