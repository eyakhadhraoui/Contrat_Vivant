import os
import logging
from datetime import datetime
from tools.cross_notification_tool import get_gestionnaire_assurances_du_contrat
from tools.notification_tool import send_email, send_teams
from tools.email_templates import render_sinistre_email
from rules_engine.risk_analyzer import analyze_risk
from rules_engine.engine import run_rules
from database.db_connection import get_connection
import json
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_SINISTRES_PATH = Path("data/sinistres.json")

# Fallback JSON réservé strictement aux tests. En production, TESTING n'est pas défini,
# donc tout passe systématiquement par MySQL.
_TESTING = os.environ.get("TESTING") == "1"


def _contrat_id_aliases(value: str | None) -> set[str]:
    aliases: set[str] = set()
    if not value:
        return aliases

    text = str(value).strip().upper()
    if not text:
        return aliases

    aliases.add(text)

    canonical = None
    if text.startswith("CSTR"):
        canonical = text
    else:
        match = re.match(r"^C0*(\d+)$", text)
        if match:
            canonical = f"CSTR{int(match.group(1)):05d}"

    if canonical:
        aliases.add(canonical)
        short_match = re.match(r"^CSTR0*(\d+)$", canonical)
        if short_match:
            aliases.add(f"C{int(short_match.group(1)):03d}")

    return aliases


def _get_contrat_details(contrat_id: str) -> dict | None:
    from tools.si_contrats_tool import _normalize_contrat_id

    aliases = _contrat_id_aliases(contrat_id)
    norm = _normalize_contrat_id(contrat_id)
    if norm:
        aliases.add(norm)

    if _TESTING:
        from tools.si_contrats_tool import _load_contrats
        contrats = _load_contrats()
        for c in contrats:
            c_norm = _normalize_contrat_id(c.get("id"))
            if c.get("id") in aliases or c_norm in aliases:
                return {
                    "id": c.get("id"),
                    "type_contrat": c.get("type_contrat") or c.get("type") or "auto",
                    "statut": c.get("statut", "actif"),
                }
        return None

    conn = get_connection()
    if not conn:
        raise ConnectionError("Impossible d'obtenir une connexion MySQL")
    try:
        cur = conn.cursor()
        placeholders = ", ".join(["%s"] * len(aliases))
        cur.execute(f"SELECT id, type_contrat, statut FROM contrats WHERE id IN ({placeholders})", tuple(a for a in aliases if a))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "type_contrat": row[1],
            "statut": row[2] or "actif"
        }
    except Exception as e:
        raise RuntimeError(f"Erreur récupération détails du contrat depuis MySQL: {e}")


def _get_contrat_type(contrat_id: str) -> str | None:
    details = _get_contrat_details(contrat_id)
    return details.get("type_contrat") if details else None


def _sinistre_type_matches_contrat(type_sinistre: str, type_contrat: str) -> bool:
    if not type_sinistre or not type_contrat:
        return False
    norm = type_sinistre.lower().replace('é', 'e').strip()
    if type_contrat == 'auto':
        return 'auto' in norm or 'automobile' in norm
    if type_contrat == 'habitation':
        return 'habitation' in norm or 'logement' in norm
    if type_contrat == 'vie':
        return 'vie' in norm
    if type_contrat == 'sante':
        return 'sante' in norm
    return type_contrat in norm


def get_sinistres(contrat_id: str):
    """Récupère tous les sinistres liés à un contrat depuis MySQL (DB-only en production)."""
    from tools.si_contrats_tool import _normalize_contrat_id

    normalized_contrat_id = _normalize_contrat_id(contrat_id)
    aliases = _contrat_id_aliases(contrat_id)
    if normalized_contrat_id:
        aliases.add(normalized_contrat_id)

    # AVANT : `isinstance(locaux, list)` était toujours vrai car _load_sinistres()
    # ne lève jamais d'exception -> le code MySQL n'était JAMAIS exécuté.
    # CORRECTION : le fallback JSON n'est utilisé qu'explicitement en mode test.
    if _TESTING:
        locaux = _load_sinistres()
        return [
            s for s in locaux
            if _normalize_contrat_id(s.get("contrat_id")) in aliases
        ]

    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor()
        sql = """
            SELECT s.id,
                   s.contrat_id,
                   COALESCE(CONCAT(cl.prenom, ' ', cl.nom), c.client_id) AS client,
                   s.type_sinistre,
                   s.montant_declare,
                   s.date_declaration AS date,
                   s.statut,
                   s.gestionnaire_traitant_id,
                   s.agence_id,
                   COALESCE(CONCAT(g.prenom, ' ', g.nom), g.username, s.gestionnaire_traitant_id) AS gestionnaire_nom,
                   COALESCE(a.nom, s.agence_id) AS agence_nom
            FROM sinistres s
            JOIN contrats c ON s.contrat_id = c.id
            LEFT JOIN clients cl ON c.client_id = cl.id
            LEFT JOIN gestionnaires g ON s.gestionnaire_traitant_id = g.id
            LEFT JOIN agences a ON (s.agence_id = a.id OR c.agence_id = a.id)
            WHERE s.contrat_id IN ({placeholders})
        """
        placeholders = ", ".join(["%s"] * len(aliases))
        cur.execute(sql.format(placeholders=placeholders), tuple(a for a in aliases if a))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        conn.close()
        results = []
        for row in rows:
            item = {col: row[idx] for idx, col in enumerate(cols)}
            item['montant_declare'] = float(item.get('montant_declare', 0))
            item['date'] = str(item.get('date', ''))
            results.append(item)
        return results
    except Exception as e:
        logger.error("Échec récupération sinistres MySQL pour contrat %s: %s", contrat_id, e)
        raise RuntimeError(f"Erreur récupération sinistres depuis MySQL: {e}")


def get_sinistres_par_agence(agence_id: str | None = None):
    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor()
        sql = """
            SELECT s.id,
                   s.contrat_id,
                   COALESCE(CONCAT(cl.prenom, ' ', cl.nom), c.client_id) AS client,
                   s.type_sinistre AS type,
                   s.type_sinistre,
                   s.montant_declare,
                   s.lieu_sinistre AS lieu,
                   s.date_sinistre,
                   s.date_declaration AS date,
                   s.date_reglement,
                   s.responsabilite,
                   s.statut,
                   s.description,
                   s.observations,
                   s.gestionnaire_traitant_id,
                   s.agence_id,
                   COALESCE(CONCAT(g.prenom, ' ', g.nom), g.username, s.gestionnaire_traitant_id) AS gestionnaire_nom,
                   COALESCE(a.nom, s.agence_id) AS agence_nom
            FROM sinistres s
            LEFT JOIN contrats c ON (s.contrat_id = c.id OR s.contrat_id = REPLACE(c.id, 'CSTR000', 'C00'))
            LEFT JOIN clients cl ON c.client_id = cl.id
            LEFT JOIN gestionnaires g ON s.gestionnaire_traitant_id = g.id
            LEFT JOIN agences a ON (s.agence_id = a.id OR c.agence_id = a.id)
        """
        if agence_id:
            sql += " WHERE (s.agence_id = %s OR s.agence_id IS NULL OR c.agence_id = %s)"
            cur.execute(sql, (agence_id, agence_id))
        else:
            cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        conn.close()
        results = []
        for row in rows:
            item = {col: row[idx] for idx, col in enumerate(cols)}
            item['montant_declare'] = float(item.get('montant_declare', 0))
            item['date'] = str(item.get('date', ''))
            item['date_sinistre'] = str(item.get('date_sinistre', '')) if item.get('date_sinistre') else ''
            results.append(item)
        return results
    except Exception as e:
        logger.error("Échec récupération sinistres MySQL pour agence %s: %s", agence_id, e)
        raise RuntimeError(f"Erreur récupération sinistres depuis MySQL: {e}")


def ajouter_sinistre(sinistre_data: dict, gestionnaire: dict):
    """
    Permet d'ajouter un sinistre directement dans MySQL.
    Le fallback JSON n'est utilisé qu'en mode test (TESTING=1).
    """
    from tools.si_contrats_tool import _normalize_contrat_id

    sid = sinistre_data.get("id")
    raw_contrat_id = sinistre_data.get("contrat_id")
    contrat_id = _normalize_contrat_id(raw_contrat_id) or raw_contrat_id
    type_s = sinistre_data.get("type_sinistre") or sinistre_data.get("type") or "Auto - Carambolage"
    montant = float(sinistre_data.get("montant_declare", 0))
    date_val = sinistre_data.get("date_declaration") or sinistre_data.get("date") or datetime.now().strftime("%Y-%m-%d")

    statut = sinistre_data.get("statut", "en_cours")
    gest_id = gestionnaire.get("gestionnaire_id") or gestionnaire.get("id") or "G123"
    agence_id = gestionnaire.get("agence_id") or sinistre_data.get("agence_id") or "AG01"

    if not contrat_id:
        raise ValueError("contrat_id requis pour ajouter un sinistre")

    details = _get_contrat_details(contrat_id)
    if not details:
        c_type = _get_contrat_type(contrat_id)
        if not c_type:
            raise ValueError(f"Contrat introuvable : {contrat_id}")
        details = {"id": contrat_id, "type_contrat": c_type, "statut": "actif"}

    contrat_type = details.get("type_contrat")
    contrat_statut = str(details.get("statut") or "actif").strip().lower()

    if contrat_statut in ("suspendu", "suspendue"):
        raise ValueError(
            f"Impossible de déclarer un sinistre : le contrat {contrat_id} est actuellement suspendu."
        )
    if contrat_statut in ("resilie", "résilié", "resiliée", "résiliée"):
        raise ValueError(
            f"Impossible de déclarer un sinistre : le contrat {contrat_id} est résilié."
        )

    if not _sinistre_type_matches_contrat(type_s, contrat_type):
        raise ValueError(
            f"Incompatibilité de type : Impossible de déclarer un sinistre de type '{type_s}' sur un contrat de type '{contrat_type}'."
        )

    date_sinistre = sinistre_data.get("date_sinistre")
    lieu_sinistre = sinistre_data.get("lieu_sinistre") or sinistre_data.get("lieu")
    description = sinistre_data.get("description")
    responsabilite = sinistre_data.get("responsabilite", "indetermine")
    date_reglement = sinistre_data.get("date_reglement")
    observations = sinistre_data.get("observations")

    if _TESTING:
        locaux = _load_sinistres()
        for s in locaux:
            if s.get("id") == sid:
                s.update({"montant_declare": montant, "statut": statut, "type_sinistre": type_s})
                _save_sinistres(locaux)
                nouveau_sinistre = s
                break
        else:
            nouveau_sinistre = {
                "id": sid,
                "contrat_id": contrat_id,
                "type_sinistre": type_s,
                "montant_declare": montant,
                "date": date_val,
                "statut": statut,
                "gestionnaire_traitant_id": gest_id,
                "agence_id": agence_id,
            }
            locaux.append(nouveau_sinistre)
            _save_sinistres(locaux)
    else:
        # Chemin MySQL réel
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL pour ajouter sinistre")
        try:
            cur = conn.cursor()
            sql = """
                INSERT INTO sinistres (
                    id, contrat_id, date_sinistre, type_sinistre, lieu_sinistre, description,
                    montant_declare, responsabilite, date_declaration, date_reglement, statut,
                    gestionnaire_traitant_id, agence_id, observations
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    montant_declare = VALUES(montant_declare),
                    statut = VALUES(statut),
                    type_sinistre = VALUES(type_sinistre),
                    date_sinistre = VALUES(date_sinistre),
                    lieu_sinistre = VALUES(lieu_sinistre),
                    description = VALUES(description),
                    responsabilite = VALUES(responsabilite),
                    date_reglement = VALUES(date_reglement),
                    observations = VALUES(observations),
                    agence_id = VALUES(agence_id)
            """

            cur.execute(sql, (
                sid, contrat_id, date_sinistre, type_s, lieu_sinistre, description,
                montant, responsabilite, date_val, date_reglement, statut,
                gest_id, agence_id, observations
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error("Échec insertion sinistre MySQL %s: %s", sid, e)
            raise RuntimeError(f"Erreur insertion sinistre dans MySQL: {e}")

        nouveau_sinistre = {
            "id": sid,
            "contrat_id": contrat_id,
            "type_sinistre": type_s,
            "montant_declare": montant,
            "date": date_val,
            "statut": statut,
            "gestionnaire_traitant_id": gest_id,
            "agence_id": agence_id
        }

    # Journalisation dans l'audit
    from tools.audit_log_tool import log_decision
    log_decision("ajout_sinistre", {
        "action": f"Sinistre {sid} ({type_s}) déclaré sur contrat {contrat_id} par {gestionnaire.get('username') or gest_id}",
        "actor": gestionnaire.get("username") or gest_id,
        "gestionnaire_id": gest_id,
        "agence_id": agence_id,
        "contrat_id": contrat_id,
        "sinistre_id": sid,
        "type_sinistre": type_s,
        "montant_declare": montant,
        "statut": statut,
        "status": "OK"
    }, gest_id)


    # Notification au gestionnaire ASSURANCES du contrat concerné (commun aux deux chemins)
    g_assurances = get_gestionnaire_assurances_du_contrat(contrat_id)
    if g_assurances and g_assurances.get('email'):
        from tools.si_contrats_tool import get_contrat
        contrat = get_contrat(contrat_id) or {}
        risk = analyze_risk(contrat, [nouveau_sinistre]) if contrat else {}
        sujet = f"Nouveau sinistre déclaré sur le contrat {contrat_id}"
        
        g_prenom = gestionnaire.get("prenom", "")
        g_nom = gestionnaire.get("nom", "")
        gestionnaire_nom = f"{g_prenom} {g_nom}".strip() or gestionnaire.get("username") or gestionnaire.get("gestionnaire_id") or "Ahmed Trabelsi"
        client_nom = (contrat.get("client") if contrat else None) or nouveau_sinistre.get("client") 
        type_s_val = nouveau_sinistre.get("type_sinistre") or nouveau_sinistre.get("type") or "Auto - Carambolage"

        plain, html = render_sinistre_email(
            event="Nouveau sinistre",
            sinistre_id=nouveau_sinistre['id'],
            contrat_id=contrat_id,
            montant=nouveau_sinistre['montant_declare'],
            gestionnaire_id=gestionnaire.get('gestionnaire_id', 'G123'),
            statut=nouveau_sinistre.get('statut'),
            risk=risk,
            client_nom=client_nom,
            gestionnaire_nom=gestionnaire_nom,
            type_sinistre=type_s_val,
        )
        send_email(g_assurances['email'], sujet, plain, html)
        try:
            send_teams(plain)
        except Exception:
            pass

    # Enregistrement de l'alerte in-app
    from tools.si_agences_clients_tool import save_in_app_alert
    alert_data = {
        "type": "nouveau_sinistre",
        "contrat_id": contrat_id,
        "sinistre_id": sid,
        "message": f"Nouveau sinistre {sid} déclaré sur le contrat {contrat_id} (Montant: {montant} DT)",
        "gestionnaire_source_id": gestionnaire.get("gestionnaire_id"),
        "timestamp": date_val,
    }
    save_in_app_alert(contrat_id, alert_data, "en_attente", gestionnaire.get("gestionnaire_id"))


    return {
        "sinistre": nouveau_sinistre,
        "gestionnaire_assurances_notifie": g_assurances.get("id") if g_assurances else None
    }


def modifier_sinistre(sinistre_id: str, updates: dict, gestionnaire: dict):
    """
    Permet de modifier un sinistre directement dans MySQL.
    """
    if isinstance(updates.get("champs"), dict):
        updates.update(updates["champs"])

    conn = get_connection()
    if not conn:
        raise ConnectionError("Impossible d'obtenir une connexion MySQL pour modifier sinistre")
    try:
        cur = conn.cursor()
        sql = "UPDATE sinistres SET id = id"
        params = []
        if "statut" in updates:
            sql += ", statut = %s"
            params.append(updates["statut"])
        if "montant_declare" in updates and updates["montant_declare"] is not None:
            sql += ", montant_declare = %s"
            params.append(float(updates["montant_declare"]))
        if "type_sinistre" in updates:
            sql += ", type_sinistre = %s"
            params.append(updates["type_sinistre"])
        if "date_sinistre" in updates:
            sql += ", date_sinistre = %s"
            params.append(updates["date_sinistre"])
        if "lieu_sinistre" in updates:
            sql += ", lieu_sinistre = %s"
            params.append(updates["lieu_sinistre"])
        if "description" in updates:
            sql += ", description = %s"
            params.append(updates["description"])
        if "responsabilite" in updates:
            sql += ", responsabilite = %s"
            params.append(updates["responsabilite"])
        if "date_reglement" in updates:
            sql += ", date_reglement = %s"
            params.append(updates["date_reglement"])
        if "observations" in updates:
            sql += ", observations = %s"
            params.append(updates["observations"])

        sql += " WHERE id = %s"
        params.append(sinistre_id)
        cur.execute(sql, params)
        rows_affected = cur.rowcount
        conn.commit()
        if rows_affected == 0:
            cid = updates.get("contrat_id") 
            montant = updates.get("montant_declare")
            statut = updates.get("statut")
            type_s = updates.get("type_sinistre")
            date_val = datetime.now().strftime("%Y-%m-%d")
            gest_id = gestionnaire.get("gestionnaire_id")
            agence_id = gestionnaire.get("agence_id")
            cur.execute("""
                INSERT INTO sinistres (id, contrat_id, type_sinistre, montant_declare, date_declaration, date_sinistre, statut, gestionnaire_traitant_id, agence_id, observations)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (sinistre_id, cid, type_s, montant, date_val, date_val, statut, gest_id, agence_id, updates.get("observations")))
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error("Échec modification sinistre MySQL %s: %s", sinistre_id, e)
        raise RuntimeError(f"Erreur modification sinistre dans MySQL: {e}")


    list_sin = get_sinistres_par_agence(gestionnaire.get("agence_id"))
    sinistre_modifie = next((s for s in list_sin if s['id'] == sinistre_id), None)
    if not sinistre_modifie:
        sinistre_modifie = {"id": sinistre_id, "contrat_id": updates.get("contrat_id", "CSTR00001"), "montant_declare": updates.get("montant_declare", 0), "statut": updates.get("statut", "en_cours")}

    contrat_id = sinistre_modifie.get('contrat_id')
    if not contrat_id:
        raise ValueError(f"contrat_id introuvable pour le sinistre {sinistre_id}")

    from tools.si_contrats_tool import get_contrat
    contrat = get_contrat(contrat_id)
    tous_sinistres = get_sinistres(contrat_id)
    risk = analyze_risk(contrat or {}, tous_sinistres)
    anomalies = risk.get('anomalies', [])

    g_prenom = gestionnaire.get("prenom", "")
    g_nom = gestionnaire.get("nom", "")
    gestionnaire_nom = f"{g_prenom} {g_nom}".strip() or gestionnaire.get("username") or gestionnaire.get("gestionnaire_id") or "Ahmed Trabelsi"
    client_nom = (contrat.get("client") if contrat else None) or sinistre_modifie.get("client")
    type_s_val = sinistre_modifie.get("type_sinistre") or sinistre_modifie.get("type") or "Auto - Carambolage"

    g_assurances = get_gestionnaire_assurances_du_contrat(contrat_id)
    if g_assurances and g_assurances.get('email'):
        sujet = f"Modification du sinistre {sinistre_id} (Contrat {contrat_id})"
        plain, html = render_sinistre_email(
            event="Modification sinistre",
            sinistre_id=sinistre_id,
            contrat_id=contrat_id,
            montant=sinistre_modifie.get('montant_declare', 0),
            gestionnaire_id=gestionnaire.get('gestionnaire_id', 'G123'),
            statut=sinistre_modifie.get('statut'),
            risk=risk,
            client_nom=client_nom,
            gestionnaire_nom=gestionnaire_nom,
            type_sinistre=type_s_val,
        )
        send_email(g_assurances['email'], sujet, plain, html)
        try:
            send_teams(plain)
        except Exception:
            pass

    return {
        "sinistre": sinistre_modifie,
        "gestionnaire_assurances_notifie": g_assurances.get("id") if g_assurances else None,
        "cross_analysis_declenchee": True,
        "analyse_auto_declenchee": True,
        "risk_score": risk.get("score"),
        "urgency_level": risk.get("urgency_level"),
        "anomalies_detectees": anomalies,
        "nb_anomalies_detectees": len(anomalies),
        "anomalies": anomalies,
        "risk_analysis": risk,
    }


def _load_sinistres():
    """Helper for tests: charge `data/sinistres.json` si présent."""
    try:
        if not _SINISTRES_PATH.exists():
            return []
        with _SINISTRES_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_sinistres(sinistres):
    """Helper for tests: sauvegarde `data/sinistres.json`."""
    try:
        _SINISTRES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SINISTRES_PATH.open("w", encoding="utf-8") as f:
            json.dump(sinistres, f, ensure_ascii=False, indent=2)
    except Exception:
        pass