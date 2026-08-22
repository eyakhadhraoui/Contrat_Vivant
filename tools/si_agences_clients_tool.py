"""
Outils d'accès aux tables agences, clients et historique dans MySQL.
"""

import json
import logging
from datetime import datetime
from database.db_connection import get_connection

logger = logging.getLogger(__name__)


def get_agences():
    """Retourne la liste complète des agences depuis MySQL."""
    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nom, ville, adresse FROM agences ORDER BY id ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows or []
    except Exception as e:
        logger.error("Erreur récupération agences depuis MySQL: %s", e)
        raise RuntimeError(f"Erreur récupération agences depuis MySQL: {e}")


def get_clients():
    """Retourne la liste complète des clients depuis MySQL."""
    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nom, prenom, cin, email, telephone, adresse, date_creation FROM clients ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for r in rows:
            if r.get('date_creation'):
                r['date_creation'] = str(r['date_creation'])
        return rows or []
    except Exception as e:
        logger.error("Erreur récupération clients depuis MySQL: %s", e)
        raise RuntimeError(f"Erreur récupération clients depuis MySQL: {e}")


def ajouter_client(client_data: dict, gestionnaire: dict):
    """Ajoute un nouveau client dans MySQL et enregistre l'événement dans le journal d'audit."""
    import random
    raw_id = client_data.get("id")
    cid = raw_id or f"CL{random.randint(10, 99)}"
    nom = client_data.get("nom", "").strip()
    prenom = client_data.get("prenom", "").strip()
    cin = client_data.get("cin", "")
    email = client_data.get("email", "")
    telephone = client_data.get("telephone", "")
    adresse = client_data.get("adresse", "Tunisie")

    if not nom or not prenom:
        raise ValueError("Le nom et le prénom du client sont obligatoires.")

    gest_id = gestionnaire.get("gestionnaire_id") or gestionnaire.get("id") or "G123"
    agence_id = gestionnaire.get("agence_id") or "AG01"

    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL pour ajouter un client")
        cur = conn.cursor()
        sql = """
            INSERT INTO clients (id, nom, prenom, cin, email, telephone, adresse)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nom = VALUES(nom), prenom = VALUES(prenom), cin = VALUES(cin),
                email = VALUES(email), telephone = VALUES(telephone), adresse = VALUES(adresse)
        """
        cur.execute(sql, (cid, nom, prenom, cin, email, telephone, adresse))
        conn.commit()
        cur.close()
        conn.close()

        # Audit log
        from tools.audit_log_tool import log_decision
        log_decision("ajout_client", {
            "action": f"Nouveau client {cid} ({prenom} {nom}) créé par {gestionnaire.get('username') or gest_id}",
            "actor": gestionnaire.get("username") or gest_id,
            "gestionnaire_id": gest_id,
            "agence_id": agence_id,
            "client_id": cid,
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "status": "OK"
        }, gest_id)

        return {"id": cid, "nom": nom, "prenom": prenom, "cin": cin, "email": email, "telephone": telephone, "adresse": adresse}
    except Exception as e:
        logger.error("Échec création client MySQL: %s", e)
        raise RuntimeError(f"Erreur création client dans MySQL: {e}")



def save_in_app_alert(contrat_id: str, alert_data: dict, validation_status: str = 'en_attente', gestionnaire_id: str | None = None):
    """Insère une alerte/notification in-app dans la table `historique` de MySQL."""
    try:
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        sql = "INSERT INTO historique (contrat_id, alert, validation_status, valide_par_gestionnaire_id) VALUES (%s, %s, %s, %s)"
        cur.execute(sql, (contrat_id, json.dumps(alert_data, ensure_ascii=False), validation_status, gestionnaire_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error("Échec enregistrement alerte in-app dans MySQL: %s", e)


def get_historique_db(agence_id: str | None = None, status: str | None = None, contrat_id: str | None = None):
    """
    Retourne les entrées de la table `historique` filtrées par l'agence du gestionnaire authentifié.
    """
    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT h.id, h.contrat_id, h.alert, h.validation_status, h.valide_par_gestionnaire_id, h.date_validation,
                   c.agence_id, g.nom AS gestionnaire_nom, g.prenom AS gestionnaire_prenom
            FROM historique h
            LEFT JOIN contrats c ON h.contrat_id = c.id
            LEFT JOIN gestionnaires g ON h.valide_par_gestionnaire_id = g.id
            WHERE 1=1
        """
        params = []
        if agence_id:
            sql += " AND (c.agence_id = %s OR c.agence_id IS NULL)"
            params.append(agence_id)
        if status:
            sql += " AND h.validation_status = %s"
            params.append(status)
        if contrat_id:
            sql += " AND h.contrat_id LIKE %s"
            params.append(f"%{contrat_id}%")

        sql += " ORDER BY h.date_validation DESC"
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for row in rows:
            if isinstance(row.get('alert'), str):
                try:
                    row['alert'] = json.loads(row['alert'])
                except Exception:
                    pass
            if row.get('date_validation'):
                row['date_validation'] = str(row['date_validation'])
            results.append(row)
        return results
    except Exception as e:
        logger.error("Erreur récupération historique depuis MySQL: %s", e)
        raise RuntimeError(f"Erreur récupération historique depuis MySQL: {e}")


def get_alerts_for_gestionnaire(gestionnaire_id: str, agence_id: str | None = None):
    """
    Retourne les alertes in-app non traitées (y compris celles reportées 'pas_maintenant') concernant l'agence ou le gestionnaire.
    """
    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT h.id, h.contrat_id, h.alert, h.validation_status, h.valide_par_gestionnaire_id, h.date_validation,
                   c.agence_id
            FROM historique h
            LEFT JOIN contrats c ON h.contrat_id = c.id
            WHERE h.validation_status IN ('en_attente', 'en_attente_validation', 'escalade_aucun_gestionnaire', 'pas_maintenant')
        """
        params = []
        if agence_id:
            sql += " AND (c.agence_id = %s OR c.agence_id IS NULL)"
            params.append(agence_id)

        sql += " ORDER BY h.date_validation DESC LIMIT 50"
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for row in rows:
            if isinstance(row.get('alert'), str):
                try:
                    row['alert'] = json.loads(row['alert'])
                except Exception:
                    pass
            if row.get('date_validation'):
                row['date_validation'] = str(row['date_validation'])
            results.append(row)
        return results
    except Exception as e:
        logger.error("Erreur récupération alertes depuis MySQL: %s", e)
        raise RuntimeError(f"Erreur récupération alertes depuis MySQL: {e}")


def update_alert_validation_status(alert_id: int, status: str, gestionnaire_id: str, comment: str | None = None):
    """
    Met à jour le statut d'une alerte dans la table historique (ex: validee, rejetee, pas_maintenant).
    """
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            try:
                sql = """
                    UPDATE historique
                    SET validation_status = %s, valide_par_gestionnaire_id = %s, date_validation = %s
                    WHERE id = %s
                """
                cur.execute(sql, (status, gestionnaire_id, date_now, alert_id))
            except Exception:
                sql = """
                    UPDATE historique
                    SET validation_status = %s, date_validation = %s
                    WHERE id = %s
                """
                cur.execute(sql, (status, date_now, alert_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
    except Exception as e:
        logger.error(f"Erreur mise à jour alerte MySQL {alert_id}: {e}")
        return False
