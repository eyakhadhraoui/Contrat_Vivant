import json
import logging
from pathlib import Path
from database.db_connection import get_connection

logger = logging.getLogger(__name__)
_DATA_DIR = Path("data")

def _load_json(filename: str):
    p = _DATA_DIR / filename
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_json(filename: str, data: list):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    p = _DATA_DIR / filename
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def supprimer_contrat(contrat_id: str, gestionnaire: dict):
    """Supprime un contrat de MySQL (et du JSON fallback) et enregistre l'événement d'audit."""
    gest_id = gestionnaire.get("gestionnaire_id") or gestionnaire.get("id") or "G123"
    prenom = gestionnaire.get("prenom", "")
    nom = gestionnaire.get("nom", "")
    actor_name = f"{prenom} {nom}".strip() or gestionnaire.get("username") or gest_id

    # 1. Suppression MySQL (suppression en cascade des sinistres associés)
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sinistres WHERE contrat_id = %s", (contrat_id,))
            cur.execute("DELETE FROM contrats WHERE id = %s", (contrat_id,))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        logger.error(f"Erreur suppression contrat MySQL: {e}")

    # 2. Suppression JSON fallback
    contrats = _load_json("contrats.json")
    contrats_filtres = [c for c in contrats if c.get("id") != contrat_id]
    _save_json("contrats.json", contrats_filtres)

    sinistres = _load_json("sinistres.json")
    sinistres_filtres = [s for s in sinistres if s.get("contrat_id") != contrat_id]
    _save_json("sinistres.json", sinistres_filtres)

    # 3. Log d'audit
    from tools.audit_log_tool import log_decision
    log_decision("suppression_contrat", {
        "action": f"Contrat {contrat_id} supprimé par le gestionnaire {actor_name}",
        "actor": actor_name,
        "contrat_id": contrat_id,
        "status": "OK"
    }, gest_id)

    return {"status": "success", "message": f"Contrat {contrat_id} supprimé avec succès."}


def supprimer_sinistre(sinistre_id: str, gestionnaire: dict):
    """Supprime un sinistre de MySQL (et du JSON fallback) et enregistre l'événement d'audit."""
    gest_id = gestionnaire.get("gestionnaire_id") or gestionnaire.get("id") or "G123"
    prenom = gestionnaire.get("prenom", "")
    nom = gestionnaire.get("nom", "")
    actor_name = f"{prenom} {nom}".strip() or gestionnaire.get("username") or gest_id

    # 1. Suppression MySQL
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sinistres WHERE id = %s", (sinistre_id,))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        logger.error(f"Erreur suppression sinistre MySQL: {e}")

    # 2. Suppression JSON fallback
    sinistres = _load_json("sinistres.json")
    sinistres_filtres = [s for s in sinistres if s.get("id") != sinistre_id]
    _save_json("sinistres.json", sinistres_filtres)

    # 3. Log d'audit
    from tools.audit_log_tool import log_decision
    log_decision("suppression_sinistre", {
        "action": f"Sinistre {sinistre_id} supprimé par le gestionnaire {actor_name}",
        "actor": actor_name,
        "sinistre_id": sinistre_id,
        "status": "OK"
    }, gest_id)

    return {"status": "success", "message": f"Sinistre {sinistre_id} supprimé avec succès."}
