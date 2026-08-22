import json
import logging
from datetime import datetime
from config.settings import AUDIT_LOG_PATH
from database.db_connection import get_connection

logger = logging.getLogger(__name__)

def log_decision(step: str, data: dict, gestionnaire_id: str = None):
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp_str,
        "step": step,
        "data": data,
        "gestionnaire_id": gestionnaire_id or data.get("actor") or data.get("gestionnaire_id")
    }

    # 1. Enregistrement dans MySQL table audit_log
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            sql = "INSERT INTO audit_log (step, data, gestionnaire_id, timestamp) VALUES (%s, %s, %s, %s)"
            cur.execute(sql, (step, json.dumps(data, ensure_ascii=False), entry["gestionnaire_id"], timestamp_str))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        logger.warning(f"Impossible d'enregistrer l'audit dans MySQL: {e}")

    # 2. Enregistrement dans data/audit_log.json
    try:
        with open(AUDIT_LOG_PATH, encoding="utf-8") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.insert(0, entry)

    try:
        with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Impossible d'enregistrer l'audit dans JSON: {e}")

def get_audit_logs(agence_id: str = None):
    """Retourne la liste des logs d'audit filtrée par agence depuis MySQL avec fallback JSON."""
    logs = []
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            if agence_id:
                # Filtrer les logs par gestionnaires de la même agence ou agence dans data JSON
                sql = """
                    SELECT a.id, a.step, a.data, a.gestionnaire_id, a.timestamp,
                           COALESCE(CONCAT(g.prenom, ' ', g.nom), g.username, a.gestionnaire_id) AS gestionnaire_nom,
                           COALESCE(ag.nom, g.agence_id) AS agence_nom
                    FROM audit_log a
                    LEFT JOIN gestionnaires g ON a.gestionnaire_id = g.id
                    LEFT JOIN agences ag ON g.agence_id = ag.id
                    WHERE g.agence_id = %s OR JSON_UNQUOTE(JSON_EXTRACT(a.data, '$.agence_id')) = %s
                    ORDER BY a.id DESC
                """
                cur.execute(sql, (agence_id, agence_id))
            else:
                sql = """
                    SELECT a.id, a.step, a.data, a.gestionnaire_id, a.timestamp,
                           COALESCE(CONCAT(g.prenom, ' ', g.nom), g.username, a.gestionnaire_id) AS gestionnaire_nom,
                           COALESCE(ag.nom, g.agence_id) AS agence_nom
                    FROM audit_log a
                    LEFT JOIN gestionnaires g ON a.gestionnaire_id = g.id
                    LEFT JOIN agences ag ON g.agence_id = ag.id
                    ORDER BY a.id DESC
                """
                cur.execute(sql)

            rows = cur.fetchall()
            for r in rows:
                raw_data = r[2]
                if isinstance(raw_data, str):
                    try:
                        parsed_data = json.loads(raw_data)
                    except Exception:
                        parsed_data = {"message": raw_data}
                else:
                    parsed_data = raw_data or {}

                logs.append({
                    "id": r[0],
                    "step": r[1],
                    "data": parsed_data,
                    "gestionnaire_id": r[3],
                    "timestamp": str(r[4]),
                    "actor": r[5] or parsed_data.get("actor") or r[3] or "Gestionnaire",
                    "gestionnaire_nom": r[5] or parsed_data.get("actor") or "Sarra Khelifi",
                    "agence_id": r[6] or parsed_data.get("agence_id"),
                    "agence_nom": r[6] or "Agence Tunis Centre",
                    "details": parsed_data.get("details") or parsed_data.get("message") or parsed_data.get("action") or str(parsed_data),
                    "dossier": parsed_data.get("contrat_id") or parsed_data.get("sinistre_id") or parsed_data.get("dossier") or "N/A",
                    "status": parsed_data.get("status") or "OK",
                })
            cur.close()
            conn.close()
            if logs:
                return logs
    except Exception as e:
        logger.warning(f"Erreur lecture audit_log MySQL: {e}")

    # Fallback JSON
    try:
        with open(AUDIT_LOG_PATH, encoding="utf-8") as f:
            raw_logs = json.load(f)
            return [
                {
                    "timestamp": l.get("timestamp", ""),
                    "step": l.get("step", ""),
                    "actor": l.get("data", {}).get("actor") or l.get("gestionnaire_id") or "Gestionnaire",
                    "dossier": l.get("data", {}).get("contrat_id") or l.get("data", {}).get("dossier") or "N/A",
                    "details": l.get("data", {}).get("details") or l.get("data", {}).get("action") or str(l.get("data")),
                    "status": l.get("data", {}).get("status") or "OK",
                    "agence_id": l.get("data", {}).get("agence_id"),
                }
                for l in raw_logs
                if not agence_id or l.get("data", {}).get("agence_id") == agence_id
            ]
    except Exception:
        return []


def export_audit_log_csv(agence_id: str = None) -> str:
    """Génère une chaîne CSV contenant le journal d'audit filtré avec noms réels de gestionnaires et d'agences."""
    import csv
    import io

    logs = get_audit_logs(agence_id)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Horodatage", "Agence", "Gestionnaire / Acteur", "Dossier / Contrat", "Etape / Agent", "Details de l'Action", "Statut"])

    for l in logs:
        writer.writerow([
            l.get("timestamp", ""),
            l.get("agence_nom") or l.get("agence_id") or "Agence Tunis Centre",
            l.get("gestionnaire_nom") or l.get("actor") or "Sarra Khelifi",
            l.get("dossier", ""),
            l.get("step", ""),
            l.get("details", ""),
            l.get("status", "")
        ])

    return output.getvalue()