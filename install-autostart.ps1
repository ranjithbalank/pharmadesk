# Register PharmaDesk to launch automatically at user logon (BRD ï¿½9.4).
# Creates a Scheduled Task that runs start-desktop.bat, and a daily 9pm task
# that backs up the database (SEC-3). Run once, from this folder:
#
#     powershell -ExecutionPolicy Bypass -File install-autostart.ps1
#
# Remove later with:  Unregister-ScheduledTask -TaskName "PharmaDesk*" -Confirm:$false

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$startBat  = Join-Path $root 'start-desktop.bat'
$python    = Join-Path $root 'backend\venv\Scripts\python.exe'
$manage    = Join-Path $root 'backend\manage.py'

# 1) Launch the app at logon.
$appAction  = New-ScheduledTaskAction -Execute $startBat
$appTrigger = New-ScheduledTaskTrigger -AtLogOn
$appSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'PharmaDesk - Launch at logon' `
    -Action $appAction -Trigger $appTrigger -Settings $appSettings -Force | Out-Null
Write-Host 'Registered: PharmaDesk - Launch at logon' -ForegroundColor Green

# 2) Daily database backup at 21:00.
$bkpAction  = New-ScheduledTaskAction -Execute $python -Argument "`"$manage`" backup_db" -WorkingDirectory (Join-Path $root 'backend')
$bkpTrigger = New-ScheduledTaskTrigger -Daily -At 9pm
Register-ScheduledTask -TaskName 'PharmaDesk - Daily backup' `
    -Action $bkpAction -Trigger $bkpTrigger -Force | Out-Null
Write-Host 'Registered: PharmaDesk - Daily backup (21:00)' -ForegroundColor Green

Write-Host ''
Write-Host 'Done. Tip: set an off-machine backup folder so a PC failure cannot lose data:'
Write-Host '  setx PHARMADESK_BACKUP_DIR "D:\Backups\PharmaDesk"' -ForegroundColor Yellow
