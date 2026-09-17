# scripts/setup_backup_schedule.ps1
<#
.SYNOPSIS
    Registers the Daily ACRO-BIS Project Backup into Windows Task Scheduler.
.DESCRIPTION
    Runs every day automatically (default: 11:00 PM) in the background.
    Copies all updated files to E:\ACRO_DEV_BACKUP\YYYY-MM-DD\
    Tracks git diffs, purges backups older than 14 days, and logs to logs\backup.log.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File "scripts\setup_backup_schedule.ps1"
#>

param(
    [string]$TaskName = "ACRO_BIS_Daily_Backup",
    [string]$Time = "23:00", # Runs daily at 11:00 PM
    [string]$ScriptPath = "D:\PROJECTS\VsCode Project\ACRO-BIS\scripts\backup_daily.ps1"
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Registering Automated Daily Backup in Task Scheduler" -ForegroundColor Cyan
Write-Host "Task Name : $TaskName"
Write-Host "Daily Time: $Time"
Write-Host "Script    : $ScriptPath"
Write-Host "Target Dir: E:\ACRO_DEV_BACKUP"
Write-Host "=================================================="

try {
    # Check if script exists
    if (-not (Test-Path $ScriptPath)) {
        Write-Error "Backup script not found at: $ScriptPath"
    }

    # Define the scheduled task action
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""

    # Define daily trigger
    $Trigger = New-ScheduledTaskTrigger -Daily -At $Time

    # Define settings (run even if on battery, don't stop if runs long, start when available)
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)

    # Register or overwrite the scheduled task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Daily automated backup for ACRO-BIS multi-tenant ERP to E:\ACRO_DEV_BACKUP" `
        -Force | Out-Null

    Write-Host "`n[SUCCESS] Task '$TaskName' registered successfully!" -ForegroundColor Green
    Write-Host "It will automatically run every day at $Time in the background without user prompt."
    Write-Host "View it anytime in Windows Task Scheduler (taskschd.msc)." -ForegroundColor Yellow
} catch {
    Write-Host "`n[ERROR] Failed to register task: $_" -ForegroundColor Red
    Write-Host "Note: Registering Task Scheduler jobs may require running PowerShell as Administrator." -ForegroundColor Yellow
    exit 1
}
