import json
import re
import random
import bcrypt
import jwt
from datetime import datetime, timedelta
from config.settings import GESTIONNAIRES_PATH, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES

from database.db_connection import get_connection

def _generate_gestionnaire_id():
    """Retourne un nouvel identifiant gestionnaire unique au format GNNN."""
    max_id = 0
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM gestionnaires WHERE id LIKE 'G%'")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        ids = [row[0] for row in rows if row and isinstance(row[0], str)]
    except Exception:
        ids = []

    if not ids:
        try:
            with open(GESTIONNAIRES_PATH, encoding='utf-8-sig') as f:
                gestionnaires = json.load(f)
            ids = [g.get('id', '') for g in gestionnaires if isinstance(g.get('id', ''), str)]
        except Exception:
            ids = []

    for ident in ids:
        match = re.match(r'^G0*(\d+)$', str(ident).upper())
        if match:
            max_id = max(max_id, int(match.group(1)))

    return f'G{max_id + 1:03d}'

def username_exists(username: str) -> bool:
    gestionnaire = get_gestionnaire_by_username(username)
    return gestionnaire is not None


def create_gestionnaire(username: str, password: str, email: str, nom: str, prenom: str, role: str = 'assurances', agence_id: str | None = None):
    if not username or not password or not email or not nom or not prenom:
        raise ValueError('Tous les champs requis doivent être fournis')

    role = role.lower().strip()
    if role not in ('assurances', 'sinistres'):
        raise ValueError("Le rôle doit être 'assurances' ou 'sinistres'")

    if username_exists(username):
        raise ValueError('Nom d\'utilisateur déjà utilisé')

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    gestionnaire_id = _generate_gestionnaire_id()
    agence_id = agence_id or 'AG01'
    gestionnaire = {
        'id': gestionnaire_id,
        'nom': nom,
        'prenom': prenom,
        'username': username,
        'email': email,
        'password_hash': password_hash,
        'role': role,
        'agence_id': agence_id,
    }

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO gestionnaires (id, nom, prenom, username, email, password_hash, role, agence_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
            (gestionnaire_id, nom, prenom, username, email, password_hash, role, agence_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return gestionnaire
    except Exception:
        # Fallback JSON uniquement en développement ou si MySQL indisponible.
        try:
            with open(GESTIONNAIRES_PATH, encoding='utf-8-sig') as f:
                gestionnaires = json.load(f)
        except FileNotFoundError:
            gestionnaires = []
        except Exception as exc:
            raise RuntimeError(f"Impossible de persister le gestionnaire : {exc}")

        if any(g.get('username') == username for g in gestionnaires):
            raise ValueError('Nom d\'utilisateur déjà utilisé')

        gestionnaires.append(gestionnaire)
        with open(GESTIONNAIRES_PATH, 'w', encoding='utf-8') as f:
            json.dump(gestionnaires, f, ensure_ascii=False, indent=2)
        return gestionnaire


def get_gestionnaire_by_username(username: str):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM gestionnaires WHERE username = %s", (username,))
            res = cur.fetchone()
            cur.close()
            conn.close()
            if res:
                return res
        except Exception:
            pass

    with open(GESTIONNAIRES_PATH, encoding='utf-8-sig') as f:
        gestionnaires = json.load(f)
    return next((g for g in gestionnaires if g['username'] == username), None)


def login(username: str, password: str) -> str:
    gestionnaire = get_gestionnaire_by_username(username)

    if not gestionnaire:
        raise PermissionError('Identifiant inconnu')

    pwd_hash = gestionnaire.get('password_hash') or gestionnaire.get('mot_de_passe_hash')
    if not pwd_hash:
        raise PermissionError('Mot de passe incorrect')

    try:
        pwd_hash_bytes = pwd_hash.encode('utf-8') if isinstance(pwd_hash, str) else pwd_hash
        password_valide = bcrypt.checkpw(
            password.encode('utf-8'),
            pwd_hash_bytes
        )
    except Exception:
        password_valide = False

    if not password_valide:
        raise PermissionError('Mot de passe incorrect')

    payload = {
        'gestionnaire_id': gestionnaire.get('id', ''),
        'username': gestionnaire.get('username', username),
        'nom': gestionnaire.get('nom', ''),
        'prenom': gestionnaire.get('prenom', ''),
        'role': gestionnaire.get('role', 'assurances'),
        'agence_id': gestionnaire.get('agence_id', 'AG01'),
        'exp': datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise PermissionError('Token expire, veuillez vous reconnecter')
    except jwt.InvalidTokenError:
        raise PermissionError('Token invalide')
