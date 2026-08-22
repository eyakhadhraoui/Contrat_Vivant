# Agent IA — Spécification d'ingestion et d'architecture

But: document court décrivant l'ingestion continue d'événements, le schéma d'événement, le worker, replay, et feedback.

## Objectifs
- Recevoir en continu les événements liés aux contrats (modification, échéance, sinistre, retard).
- Classifier l'événement (`contrat` / `sinistre` / `risque`).
- Calculer l'urgence via le moteur de règles + scoring.
- Produire et router une alerte contextualisée vers le(s) gestionnaire(s).
- Permettre feedback gestionnaire (valider / ajuster / rejeter).
- Permettre le rejouage de dossiers historiques et l'export audit.

## Composants
- Ingest API: endpoint HTTP `POST /api/events` (ingestion synchrone) — valide et publie sur une queue.
- Queue: Redis Streams / RabbitMQ / simple Redis list selon infra.
- Worker: consommateur asynchrone qui lit la queue, charge le `state` minimal puis appelle `graph.invoke(state)`.
- Replay CLI: script qui lit des dossiers historiques et envoie dans le worker de façon contrôlée.
- Feedback API: `POST /api/alerts/{alert_id}/feedback` pour stocker la décision du gestionnaire.
- Audit export: job périodique qui extrait logs structurés et génère CSV/JSON.

## Schéma d'événement (JSON)
{
  "event_id": "uuid",
  "timestamp": "2026-07-30T12:34:56Z",
  "event_type": "modification|sinistre|echeance|retard_paiement",
  "contrat_id": "C123",
  "payload": { /* champ libre dépendant du type */ },
  "source": "systeme_externe|ui|batch",
  "received_by": "webhook|api" 
}

- `payload` exemples:
  - modification: {"champs_modifies": {"garantie_max": 120000}}
  - sinistre: {"id":"S123","montant_declare":50000,"date":"2026-07-29"}

## Endpoint d'ingestion (prototype)
- POST /api/events
  - Valide JSON et renvoie `202 Accepted` + `event_id`.
  - Enfile l'événement dans la queue.

## Worker (pseudocode)
- boucle: pop event
- valider -> reconstruire `state` minimal: `token|contrat_id|modification_type`
- appeler `graph.invoke(state)` (ou `graph.invoke_stream` si streaming)
- persister résultat + audit log
- si anomalies: générer notification via `nodes/notification_node`

Extrait minimal:
```py
from graph.workflow import graph

def handle(event):
    state = { 'token': event.get('token'), 'contrat_id': event['contrat_id'], 'modification_type': event['event_type'] }
    res = graph.invoke(state)
    # persist res, envoyer notifications
```

## Feedback: table SQL minimale
```sql
CREATE TABLE alert_feedback (
  id INT AUTO_INCREMENT PRIMARY KEY,
  alert_id VARCHAR(64) NOT NULL,
  gestionnaire_id VARCHAR(64),
  decision ENUM('valide','ajuste','rejette'),
  note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Replay CLI
- `scripts/replay_dossier.py --file historical.json --dry-run`:
  - recharge l'état d'origine et exécute le graph, compare sorties avant/après.

## Exports & rapports
- Job périodique `reports/generate_reports.py --from 2026-07-01 --to 2026-07-30` qui:
  - compte alertes par catégorie, taux validation/ajustement/rejet, délai moyen traitement
  - export CSV/JSON horodatés pour audits

## Variables d'environnement utiles (`.env`)
- `TEAMS_WEBHOOK_URL`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- `REDIS_URL` / `RABBITMQ_URL`

## Tests à ajouter
- Unit tests pour `POST /api/events` (validation + queue enqueue)
- Integration test: worker consume -> graph.invoke -> notification
- Replay tests: runner deterministe sur fixtures

## Run rapide (prototype)
```bash
# start redis (optionnel)
# lancer worker
python -m scripts.worker
# envoyer un événement
curl -X POST http://127.0.0.1:8000/api/events -H "Content-Type: application/json" -d @example_event.json
```

## Livrables proposés
- `api/events.py` (endpoint POST)
- `scripts/worker.py` (consumer minimal)
- `scripts/replay_dossier.py` (replay harness)
- `database/migrations/` SQL pour `alert_feedback`
- Tests et docs README court

---
Spécification conciser livrée. Si vous souhaitez, je peux implémenter maintenant le prototype `POST /api/events` + `scripts/worker.py` et le test associé.
