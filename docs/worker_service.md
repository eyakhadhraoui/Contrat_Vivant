Usage rapide — garder la surveillance active

Démarrer immédiatement (PowerShell) :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_worker_forever.ps1
```

Lancer depuis l'explorateur : double-cliquer sur `scripts\run_worker_forever.bat`.

Vérifier les logs :

```powershell
Get-Content -Path logs\worker.log -Wait -Tail 50
```

Créer une tâche planifiée au démarrage (PowerShell, adapter les chemins) :

```powershell
$action = New-ScheduledTaskAction -Execute "C:\\path\\to\\agent-assurance\\venv\\Scripts\\python.exe" -Argument "scripts/worker.py"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "AgentAssuranceWorker" -Action $action -Trigger $trigger -RunLevel Highest -Force
```

Alternativement, installer `nssm` (https://nssm.cc/) et créer un service qui exécute `venv\Scripts\python.exe scripts\worker.py` pour un contrôle plus fin.

Notes:
- Le script `run_worker_forever` relance automatiquement le worker en cas d'arrêt.
- Pour production, préférez un service Windows (nssm) ou un orchestrateur de processus.
