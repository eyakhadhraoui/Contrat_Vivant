# Script pour lancer et relancer automatiquement le worker
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# Se placer à la racine du projet
Set-Location (Join-Path $scriptDir '..')
$LogDir = Join-Path (Get-Location) 'logs'
if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$log = Join-Path $LogDir 'worker.log'

while ($true) {
    $timestamp = Get-Date -Format o
    Add-Content -Path $log -Value "=== Starting worker at $timestamp ==="
    # Lancer le worker en utilisant l'interpréteur du venv
    & "$PWD\venv\Scripts\python.exe" "scripts\worker.py" 2>&1 | ForEach-Object { Add-Content -Path $log -Value ("[$(Get-Date -Format o)] " + $_) }
    $timestamp = Get-Date -Format o
    Add-Content -Path $log -Value "=== Worker exited at $timestamp. Restarting in 5s ==="
    Start-Sleep -Seconds 5
}
