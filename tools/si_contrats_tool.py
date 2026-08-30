import os
import logging
from datetime import datetime
from tools.cross_notification_tool import get_gestionnaires_sinistres_concernes
from tools.notification_tool import send_email, send_teams
from tools.email_templates import render_contrat_modification_email, render_sinistre_email
from tools.si_sinistres_tool import get_sinistres
from database.db_connection import get_connection
import json
from pathlib import Path

logger = logging.getLogger(__name__)

_CONTRATS_PATH = Path("data/contrats.json")

# Le fallback JSON ne doit JAMAIS s'activer en production.
# Il n'est utilisé que si la variable d'environnement TESTING=1 est définie.
_TESTING = os.environ.get("TESTING") == "1"


def _is_testing() -> bool:
    return os.environ.get("TESTING") == "1" or _TESTING


def _resolve_client_id(client_reference: str) -> str | None:
    if not client_reference:
        return None

    # Assume a direct client ID when it follows CLxx format.
    if client_reference.upper().startswith("CL"):
        return client_reference.upper()

    if _is_testing():
        return client_reference

    try:
        conn = get_connection()
        if not conn:
            if _is_testing():
                return client_reference
            raise ConnectionError("Impossible d'obtenir une connexion MySQL pour résoudre le client")
        cur = conn.cursor()
        sql = (
            "SELECT id FROM clients WHERE CONCAT(prenom, ' ', nom) = %s OR CONCAT(nom, ' ', prenom) = %s "
            "OR prenom = %s OR nom = %s LIMIT 1"
        )
        cur.execute(sql, (client_reference, client_reference, client_reference, client_reference))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else (client_reference if _is_testing() else None)
    except Exception as e:
        if _is_testing():
            return client_reference
        raise RuntimeError(f"Erreur résolution client depuis MySQL: {e}")


def _normalize_contrat_id(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    if text.startswith("CSTR"):
        return text

    match = __import__("re").match(r"^C0*(\d+)$", text)
    if match:
        number = int(match.group(1))
        return f"CSTR{number:05d}"

    return text


def get_contrat(query: str):
    """Récupère un contrat depuis MySQL avec tous ses champs, y compris les noms réels du gestionnaire et de l'agence."""
    if not query:
        raise ValueError("Identifiant de contrat requis")

    raw_query = query
    query = _normalize_contrat_id(query)

    if _is_testing():
        contrats = _load_contrats()
        for c in contrats:
            c_id = c.get("id")
            c_norm = _normalize_contrat_id(c_id)
            if c_id in (query, raw_query) or (c_norm and c_norm in (query, raw_query)):
                return c

    try:
        conn = get_connection()
        if not conn:
            if _is_testing():
                contrats = _load_contrats()
                for c in contrats:
                    c_id = c.get("id")
                    c_norm = _normalize_contrat_id(c_id)
                    if c_id in (query, raw_query) or (c_norm and c_norm in (query, raw_query)):
                        return c
                return None
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT c.id, COALESCE(CONCAT(cl.prenom, ' ', cl.nom), c.client_id) AS client, c.client_id, "
            "c.type_contrat AS type, c.type_contrat, c.garantie_max, c.prime_mensuelle, c.prime_annuelle, c.franchise, "
            "c.date_debut, c.date_fin, c.statut, c.mode_paiement, c.frequence_paiement, c.duree_mois, "
            "c.couverture, c.exclusions, c.observations, c.date_derniere_modif, c.gestionnaire_createur_id, c.agence_id, "
            "COALESCE(CONCAT(g.prenom, ' ', g.nom), g.username, c.gestionnaire_createur_id) AS gestionnaire_nom, "
            "COALESCE(a.nom, c.agence_id) AS agence_nom "
            "FROM contrats c "
            "LEFT JOIN clients cl ON c.client_id = cl.id "
            "LEFT JOIN gestionnaires g ON c.gestionnaire_createur_id = g.id "
            "LEFT JOIN agences a ON c.agence_id = a.id "
            "WHERE c.id = %s OR c.id = %s",
            (query, raw_query)
        )
        row = cursor.fetchone()
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
        if not row:
            if _is_testing():
                contrats = _load_contrats()
                for c in contrats:
                    c_id = c.get("id")
                    c_norm = _normalize_contrat_id(c_id)
                    if c_id in (query, raw_query) or (c_norm and c_norm in (query, raw_query)):
                        return c
            return None
        return {col: row[idx] for idx, col in enumerate(cols)}
    except Exception as e:
        if _is_testing():
            contrats = _load_contrats()
            for c in contrats:
                c_id = c.get("id")
                c_norm = _normalize_contrat_id(c_id)
                if c_id in (query, raw_query) or (c_norm and c_norm in (query, raw_query)):
                    return c
            return None
        raise RuntimeError(f"Erreur récupération contrat depuis MySQL: {e}")


def get_contrats_par_agence(agence_id: str):
    """Retourne tous les contrats de l'agence spécifiée depuis MySQL avec noms de gestionnaires et d'agences."""
    if _is_testing():
        contrats = _load_contrats()
        if agence_id:
            return [c for c in contrats if c.get("agence_id") == agence_id or not c.get("agence_id")]
        return contrats

    try:
        conn = get_connection()
        if not conn:
            if _is_testing():
                contrats = _load_contrats()
                if agence_id:
                    return [c for c in contrats if c.get("agence_id") == agence_id or not c.get("agence_id")]
                return contrats
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor()
        sql = (
            "SELECT c.id, COALESCE(CONCAT(cl.prenom, ' ', cl.nom), c.client_id) AS client, c.client_id, "
            "c.type_contrat AS type, c.type_contrat, c.garantie_max, c.prime_mensuelle, c.prime_annuelle, c.franchise, "
            "c.date_debut, c.date_fin, c.statut, c.mode_paiement, c.frequence_paiement, c.duree_mois, "
            "c.couverture, c.exclusions, c.observations, c.date_derniere_modif, c.gestionnaire_createur_id, c.agence_id, "
            "COALESCE(CONCAT(g.prenom, ' ', g.nom), g.username, c.gestionnaire_createur_id) AS gestionnaire_nom, "
            "COALESCE(a.nom, c.agence_id) AS agence_nom "
            "FROM contrats c "
            "LEFT JOIN clients cl ON c.client_id = cl.id "
            "LEFT JOIN gestionnaires g ON c.gestionnaire_createur_id = g.id "
            "LEFT JOIN agences a ON c.agence_id = a.id"
        )
        if agence_id:
            sql += " WHERE (c.agence_id = %s OR c.agence_id IS NULL)"
            cur.execute(sql, (agence_id,))
        else:
            cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        conn.close()
        results = []
        for row in rows:
            item = {col: row[idx] for idx, col in enumerate(cols)}
            item['garantie_max'] = float(item.get('garantie_max', 0))
            if item.get('prime_mensuelle') is not None: item['prime_mensuelle'] = float(item['prime_mensuelle'])
            if item.get('prime_annuelle') is not None: item['prime_annuelle'] = float(item['prime_annuelle'])
            if item.get('franchise') is not None: item['franchise'] = float(item['franchise'])
            item['date_derniere_modif'] = str(item.get('date_derniere_modif', ''))
            results.append(item)
        return results
    except Exception as e:
        if _is_testing():
            contrats = _load_contrats()
            if agence_id:
                return [c for c in contrats if c.get("agence_id") == agence_id or not c.get("agence_id")]
            return contrats
        raise RuntimeError(f"Erreur récupération contrats depuis MySQL: {e}")


def ajouter_contrat(contrat_data: dict, gestionnaire: dict):
    raw_cid = contrat_data.get("id")
    cid = _normalize_contrat_id(raw_cid) or raw_cid
    client_ref = contrat_data.get("client_id") or contrat_data.get("client")
    garantie_max = float(contrat_data.get("garantie_max", 50000))
    statut = contrat_data.get("statut", "actif")
    date_now = datetime.now().strftime("%Y-%m-%d")
    gest_id = gestionnaire.get("gestionnaire_id") or gestionnaire.get("id") or "G123"
    agence_id = gestionnaire.get("agence_id") or contrat_data.get("agence_id") or "AG01"
    type_contrat = contrat_data.get("type_contrat") or contrat_data.get("type") or "auto"

    prime_mensuelle = float(contrat_data["prime_mensuelle"]) if contrat_data.get("prime_mensuelle") else None
    prime_annuelle = float(contrat_data["prime_annuelle"]) if contrat_data.get("prime_annuelle") else None
    franchise = float(contrat_data["franchise"]) if contrat_data.get("franchise") else None
    date_debut = contrat_data.get("date_debut") or date_now
    date_fin = contrat_data.get("date_fin") or date_now
    mode_paiement = contrat_data.get("mode_paiement")
    frequence_paiement = contrat_data.get("frequence_paiement")
    duree_mois = int(contrat_data["duree_mois"]) if contrat_data.get("duree_mois") else None
    couverture = contrat_data.get("couverture")
    exclusions = contrat_data.get("exclusions")
    observations = contrat_data.get("observations")

    # Résolution du client HORS du try générique : une erreur métier claire, pas un 503.
    client_id = _resolve_client_id(client_ref)
    if not client_id:
        raise ValueError(
            f"Client introuvable pour la référence '{client_ref}'. "
            f"Utilisez un client_id existant (format CLxx) ou un nom/prénom déjà en base."
        )

    # Règle Métier : Unicité par type de contrat par client (1 Auto, 1 Habitation, 1 Vie, 1 Santé)
    try:
        conn_chk = get_connection()
        if conn_chk:
            cur_chk = conn_chk.cursor()
            cur_chk.execute(
                "SELECT id FROM contrats WHERE client_id = %s AND type_contrat = %s AND statut IN ('actif', 'suspendu') AND id != %s",
                (client_id, type_contrat, cid)
            )
            dup_row = cur_chk.fetchone()
            cur_chk.close()
            conn_chk.close()
            if dup_row:
                raise ValueError(
                    f"Le client '{client_id}' détient déjà un contrat de type '{type_contrat}' (N° {dup_row[0]}). "
                    f"Chaque client ne peut souscrire qu'un seul contrat par type."
                )
    except ValueError:
        raise
    except Exception as e:
        logger.warning(f"Impossible de vérifier l'unicité du contrat: {e}")

    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL pour ajouter contrat")
        cur = conn.cursor()
        sql = """
            INSERT INTO contrats (
                id, client_id, type_contrat, garantie_max, prime_mensuelle, prime_annuelle, franchise,
                date_debut, date_fin, statut, mode_paiement, frequence_paiement, duree_mois,
                couverture, exclusions, observations, date_creation, date_derniere_modif, gestionnaire_createur_id, agence_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                garantie_max = VALUES(garantie_max),
                prime_mensuelle = VALUES(prime_mensuelle),
                prime_annuelle = VALUES(prime_annuelle),
                franchise = VALUES(franchise),
                date_debut = VALUES(date_debut),
                date_fin = VALUES(date_fin),
                statut = VALUES(statut),
                mode_paiement = VALUES(mode_paiement),
                frequence_paiement = VALUES(frequence_paiement),
                duree_mois = VALUES(duree_mois),
                couverture = VALUES(couverture),
                exclusions = VALUES(exclusions),
                observations = VALUES(observations),
                date_derniere_modif = VALUES(date_derniere_modif),
                type_contrat = VALUES(type_contrat),
                agence_id = VALUES(agence_id)
        """
        cur.execute(sql, (
            cid, client_id, type_contrat, garantie_max, prime_mensuelle, prime_annuelle, franchise,
            date_debut, date_fin, statut, mode_paiement, frequence_paiement, duree_mois,
            couverture, exclusions, observations, date_now, date_now, gest_id, agence_id
        ))
        conn.commit()
        cur.close()
        conn.close()

        # Enregistrement dans l'historique d'audit
        from tools.audit_log_tool import log_decision
        log_decision("ajout_contrat", {
            "action": f"Contrat {cid} ({type_contrat}) souscrit par {gestionnaire.get('username') or gest_id}",
            "actor": gestionnaire.get("username") or gest_id,
            "gestionnaire_id": gest_id,
            "agence_id": agence_id,
            "contrat_id": cid,
            "type_contrat": type_contrat,
            "client_id": client_id,
            "garantie_max": garantie_max,
            "statut": statut,
            "status": "OK"
        }, gest_id)

        contrat = get_contrat(cid)
        return contrat if contrat else {
            "id": cid, "client": client_id, "garantie_max": garantie_max,
            "statut": statut, "date_derniere_modif": date_now,
            "gestionnaire_createur_id": gest_id, "agence_id": agence_id,
        }

    except (RuntimeError, ConnectionError) as e:
        logger.error("Échec insertion MySQL pour le contrat %s: %s", cid, e)
        raise
    except Exception as e:
        logger.error("Erreur SQL insertion contrat %s: %s", cid, e)
        raise RuntimeError(f"Erreur insertion contrat dans MySQL: {e}")


def modifier_contrat(contrat_id: str, updates: dict, gestionnaire: dict):
    """
    Permet de modifier un contrat existant dans MySQL.
    SI ce contrat a déjà un sinistre → notifie le(s) gestionnaire(s) SINISTRES concerné(s).
    """
    contrat_id = _normalize_contrat_id(contrat_id) or contrat_id
    date_now = datetime.now().strftime("%Y-%m-%d")

    if isinstance(updates.get("champs"), dict):
        updates.update(updates["champs"])

    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL pour modifier contrat")
        cur = conn.cursor()
        sql = "UPDATE contrats SET date_derniere_modif = %s"
        params = [date_now]
        if "statut" in updates:
            sql += ", statut = %s"
            params.append(updates["statut"])
        if "garantie_max" in updates and updates["garantie_max"] is not None:
            sql += ", garantie_max = %s"
            params.append(float(updates["garantie_max"]))
        if "prime_mensuelle" in updates and updates["prime_mensuelle"] is not None:
            sql += ", prime_mensuelle = %s"
            params.append(float(updates["prime_mensuelle"]))
        if "prime_annuelle" in updates and updates["prime_annuelle"] is not None:
            sql += ", prime_annuelle = %s"
            params.append(float(updates["prime_annuelle"]))
        if "franchise" in updates and updates["franchise"] is not None:
            sql += ", franchise = %s"
            params.append(float(updates["franchise"]))
        if "date_debut" in updates:
            sql += ", date_debut = %s"
            params.append(updates["date_debut"])
        if "date_fin" in updates:
            sql += ", date_fin = %s"
            params.append(updates["date_fin"])
        if "mode_paiement" in updates:
            sql += ", mode_paiement = %s"
            params.append(updates["mode_paiement"])
        if "frequence_paiement" in updates:
            sql += ", frequence_paiement = %s"
            params.append(updates["frequence_paiement"])
        if "type_contrat" in updates or "type" in updates:
            sql += ", type_contrat = %s"
            params.append(updates.get("type_contrat") or updates.get("type"))
        if "couverture" in updates:
            sql += ", couverture = %s"
            params.append(updates["couverture"])
        if "exclusions" in updates:
            sql += ", exclusions = %s"
            params.append(updates["exclusions"])
        if "observations" in updates:
            sql += ", observations = %s"
            params.append(updates["observations"])

        sql += " WHERE id = %s"
        params.append(contrat_id)
        cur.execute(sql, params)
        rows_affected = cur.rowcount
        conn.commit()
        if rows_affected == 0:
            client_id = updates.get("client_id") or updates.get("client") or "CL01"
            garantie_max = updates.get("garantie_max") or 50000.0
            statut = updates.get("statut") or "actif"
            type_contrat = updates.get("type_contrat") or updates.get("type") or "auto"
            obs = updates.get("observations") or "Créé via modification"
            cur.execute("""
                INSERT INTO contrats (id, client_id, type_contrat, garantie_max, statut, observations, date_debut, date_fin, date_derniere_modif, gestionnaire_createur_id, agence_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (contrat_id, client_id, type_contrat, garantie_max, statut, obs, date_now, date_now, date_now, gestionnaire.get("gestionnaire_id", "G123"), gestionnaire.get("agence_id", "AG01")))
        cur.close()
        conn.close()

        # Log d'audit
        from tools.audit_log_tool import log_decision
        gest_id = gestionnaire.get("gestionnaire_id") or gestionnaire.get("id") or "G123"
        agence_id = gestionnaire.get("agence_id") or "AG01"
        log_decision("modification_contrat", {
            "action": f"Contrat {contrat_id} modifié par {gestionnaire.get('username') or gest_id}",
            "actor": gestionnaire.get("username") or gest_id,
            "gestionnaire_id": gest_id,
            "agence_id": agence_id,
            "contrat_id": contrat_id,
            "updates": updates,
            "status": "OK"
        }, gest_id)

    except Exception as e:
        if _is_testing():
            contrats = _load_contrats()
            for c in contrats:
                c_id = c.get("id")
                c_norm = _normalize_contrat_id(c_id)
                if c_id == contrat_id or c_norm == contrat_id:
                    c.update(updates)
                    _save_contrats(contrats)
                    break
        else:
            logger.error("Échec mise à jour MySQL pour le contrat %s: %s", contrat_id, e)
            raise RuntimeError(f"Erreur mise à jour contrat dans MySQL: {e}")




    contrat_modifie = get_contrat(contrat_id)
    if not contrat_modifie:
        contrat_modifie = {"id": contrat_id, "statut": updates.get("statut", "actif"), "garantie_max": updates.get("garantie_max", 50000)}

    sinistres_lies = get_sinistres(contrat_id)
    gestionnaires_sinistres = []
    if sinistres_lies:
        gestionnaires_sinistres = get_gestionnaires_sinistres_concernes(contrat_id)
        sujet = f"Alerte : Modification du contrat {contrat_id}"
        g_prenom = gestionnaire.get("prenom", "")
        g_nom = gestionnaire.get("nom", "")
        gestionnaire_nom = f"{g_prenom} {g_nom}".strip() or gestionnaire.get("username") or gestionnaire.get("gestionnaire_id") or "Sarra Khelifi"
        client_nom = contrat_modifie.get("client")
        raw_type = contrat_modifie.get("type_contrat") or contrat_modifie.get("type") or "auto"
        formule = f"Contrat {raw_type.capitalize()}"

        plain, html = render_contrat_modification_email(
            contrat_id=contrat_id,
            client=client_nom,
            gestionnaire_id=gestionnaire.get("gestionnaire_id") or "G123",
            nb_sinistres=len(sinistres_lies),
            gestionnaire_nom=gestionnaire_nom,
            formule=formule,
        )
        for g_sinistre in gestionnaires_sinistres:
            if g_sinistre.get('email'):
                send_email(g_sinistre['email'], sujet, plain, html)
        try:
            send_teams(plain)
        except Exception:
            pass

        # Enregistrement de l'alerte in-app dans la table `historique`
        from tools.si_agences_clients_tool import save_in_app_alert
        alert_data = {
            "type": "modification_contrat",
            "contrat_id": contrat_id,
            "message": f"Contrat {contrat_id} modifié par le gestionnaire {gestionnaire.get('gestionnaire_id')}",
            "gestionnaire_source_id": gestionnaire.get("gestionnaire_id"),
            "nb_sinistres_lies": len(sinistres_lies),
            "timestamp": date_now,
        }
        save_in_app_alert(contrat_id, alert_data, "en_attente", gestionnaire.get("gestionnaire_id"))


    return {
        "contrat": contrat_modifie,
        "sinistres_existant": len(sinistres_lies) > 0,
        "gestionnaires_sinistres_notifies": [g.get("id") for g in gestionnaires_sinistres]
    }


def _load_contrats():
    """Backward-compatible helper for tests: charge `data/contrats.json` si présent."""
    try:
        if not _CONTRATS_PATH.exists():
            return []
        with _CONTRATS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_contrats(contrats):
    """Backward-compatible helper for tests: sauvegarde `data/contrats.json`."""
    try:
        _CONTRATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _CONTRATS_PATH.open("w", encoding="utf-8") as f:
            json.dump(contrats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
