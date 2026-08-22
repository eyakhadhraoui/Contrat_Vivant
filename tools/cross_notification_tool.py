from database.db_connection import get_connection
import json
import re
from pathlib import Path

_DATA_DIR = Path("data")


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

def _load_json(filename: str):
    try:
        p = _DATA_DIR / filename
        if not p.exists():
            return []
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_gestionnaire_by_id(gestionnaire_id: str):
    try:
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor()
        cur.execute("SELECT id, nom, prenom, username, email, role, agence_id FROM gestionnaires WHERE id = %s", (gestionnaire_id,))
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        conn.close()
        if not row:
            return None
        return {col: row[idx] for idx, col in enumerate(cols)}
    except Exception as e:
        raise RuntimeError(f"Erreur récupération gestionnaire depuis MySQL: {e}")


def get_gestionnaires_sinistres_concernes(contrat_id: str):
    try:
        aliases = _contrat_id_aliases(contrat_id)
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor()
        placeholders = ", ".join(["%s"] * len(aliases))
        cur.execute("""
            SELECT DISTINCT g.id, g.nom, g.prenom, g.username, g.email, g.role, g.agence_id
            FROM sinistres s
            JOIN gestionnaires g ON s.gestionnaire_traitant_id = g.id
            WHERE s.contrat_id IN ({placeholders})
        """.format(placeholders=placeholders), tuple(a for a in aliases if a))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        conn.close()
        results = []
        for row in rows:
            results.append({col: row[idx] for idx, col in enumerate(cols)})
        if results:
            return results
        # If DB returned no rows, fall back to JSON files below
    except Exception:
        # Fallback to JSON data files for test/dev environments
        sinistres = _load_json("sinistres.json")
        gestionnaires = _load_json("gestionnaires.json")
        aliases = _contrat_id_aliases(contrat_id)
        ids = {
            s.get("gestionnaire_traitant_id")
            for s in sinistres
            if _contrat_id_aliases(s.get("contrat_id")) & aliases
        }
        results = [g for g in gestionnaires if g.get("id") in ids]
        return results

    # Final fallback if DB returned no rows and no exception occurred
    sinistres = _load_json("sinistres.json")
    gestionnaires = _load_json("gestionnaires.json")
    aliases = _contrat_id_aliases(contrat_id)
    ids = {
        s.get("gestionnaire_traitant_id")
        for s in sinistres
        if _contrat_id_aliases(s.get("contrat_id")) & aliases
    }
    results = [g for g in gestionnaires if g.get("id") in ids]
    return results


def get_gestionnaire_assurances_du_contrat(contrat_id: str):
    try:
        aliases = _contrat_id_aliases(contrat_id)
        conn = get_connection()
        if not conn:
            raise ConnectionError("Impossible d'obtenir une connexion MySQL")
        cur = conn.cursor()
        placeholders = ", ".join(["%s"] * len(aliases))
        cur.execute("""
            SELECT g.id, g.nom, g.prenom, g.username, g.email, g.role, g.agence_id
            FROM contrats c
            JOIN gestionnaires g ON c.gestionnaire_createur_id = g.id
            WHERE c.id IN ({placeholders})
        """.format(placeholders=placeholders), tuple(a for a in aliases if a))
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        conn.close()
        if row:
            return {col: row[idx] for idx, col in enumerate(cols)}
        # If DB returned no row, fall back to JSON files below
    except Exception:
        # Fallback to JSON data files for test/dev environments
        contrats = _load_json("contrats.json")
        gestionnaires = _load_json("gestionnaires.json")
        aliases = _contrat_id_aliases(contrat_id)
        contrat = next((c for c in contrats if _contrat_id_aliases(c.get("id")) & aliases), None)
        if not contrat:
            return None
        gest_id = contrat.get("gestionnaire_createur_id") or contrat.get("gestionnaire_createur") or contrat.get("gestionnaire_id")
        if not gest_id:
            return None
        return next((g for g in gestionnaires if g.get("id") == gest_id), None)

    # Final fallback if DB returned no data and no exception occurred
    contrats = _load_json("contrats.json")
    gestionnaires = _load_json("gestionnaires.json")
    aliases = _contrat_id_aliases(contrat_id)
    contrat = next((c for c in contrats if _contrat_id_aliases(c.get("id")) & aliases), None)
    if not contrat:
        return None
    gest_id = contrat.get("gestionnaire_createur_id") or contrat.get("gestionnaire_createur") or contrat.get("gestionnaire_id")
    if not gest_id:
        return None
    return next((g for g in gestionnaires if g.get("id") == gest_id), None)


