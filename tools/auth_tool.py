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


def get_gestionnaire_by_email_or_google_id(email: str, google_id: str | None = None):
    """Recherche un gestionnaire existant par email ou identifiant Google dans MySQL ou JSON."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            if google_id:
                cur.execute("SELECT * FROM gestionnaires WHERE google_id = %s OR email = %s LIMIT 1", (google_id, email))
            else:
                cur.execute("SELECT * FROM gestionnaires WHERE email = %s LIMIT 1", (email,))
            res = cur.fetchone()
            cur.close()
            conn.close()
            if res:
                return res
        except Exception:
            pass

    try:
        with open(GESTIONNAIRES_PATH, encoding='utf-8-sig') as f:
            gestionnaires = json.load(f)
        return next((g for g in gestionnaires if g.get('email') == email or (google_id and g.get('google_id') == google_id)), None)
    except Exception:
        return None


def authenticate_or_create_google_user(email: str, nom: str = '', prenom: str = '', google_id: str | None = None, picture: str | None = None):
    """
    Authentifie ou crée automatiquement un gestionnaire via Google OAuth SSO.
    Si l'utilisateur existe déjà -> connexion directe sans doublon.
    Si l'utilisateur n'existe pas -> création immédiate et connexion automatique.
    """
    email_clean = (email or '').strip().lower()
    if not email_clean:
        raise ValueError("L'adresse email est requise pour l'authentification Google")

    gestionnaire = get_gestionnaire_by_email_or_google_id(email_clean, google_id)
    is_new_user = False

    if not gestionnaire:
        is_new_user = True
        # Dériver un username unique propre
        base_username = email_clean.split('@')[0].replace('.', '_')
        username = base_username
        counter = 1
        while username_exists(username):
            username = f"{base_username}_{counter}"
            counter += 1

        gestionnaire_id = _generate_gestionnaire_id()
        role = 'assurances' # Rôle par défaut
        agence_id = 'AG01'
        nom_val = nom.strip() if nom else 'Utilisateur'
        prenom_val = prenom.strip() if prenom else 'Google'
        placeholder_pwd = f"google_sso_{google_id or email_clean}"
        password_hash = bcrypt.hashpw(placeholder_pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        gestionnaire = {
            'id': gestionnaire_id,
            'nom': nom_val,
            'prenom': prenom_val,
            'username': username,
            'email': email_clean,
            'password_hash': password_hash,
            'role': role,
            'agence_id': agence_id,
            'google_id': google_id,
            'picture_url': picture
        }

        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    'INSERT INTO gestionnaires (id, nom, prenom, username, email, password_hash, role, agence_id, google_id, picture_url) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (gestionnaire_id, nom_val, prenom_val, username, email_clean, password_hash, role, agence_id, google_id, picture)
                )
                conn.commit()
                cur.close()
                conn.close()
            except Exception as exc:
                # Si erreur colonne google_id inexistante, insérer sans ces colonnes
                try:
                    cur = conn.cursor()
                    cur.execute(
                        'INSERT INTO gestionnaires (id, nom, prenom, username, email, password_hash, role, agence_id) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (gestionnaire_id, nom_val, prenom_val, username, email_clean, password_hash, role, agence_id)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception:
                    pass
    else:
        # Utilisateur existant : associer google_id ou picture_url si disponibles
        if google_id or picture:
            conn = get_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE gestionnaires SET google_id = COALESCE(google_id, %s), picture_url = COALESCE(picture_url, %s) WHERE id = %s",
                        (google_id, picture, gestionnaire.get('id'))
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception:
                    pass

    # Génération du token JWT de session
    payload = {
        'gestionnaire_id': gestionnaire.get('id', ''),
        'username': gestionnaire.get('username', ''),
        'nom': gestionnaire.get('nom', nom),
        'prenom': gestionnaire.get('prenom', prenom),
        'role': gestionnaire.get('role', 'assurances'),
        'agence_id': gestionnaire.get('agence_id', 'AG01'),
        'email': gestionnaire.get('email', email_clean),
        'picture_url': picture or gestionnaire.get('picture_url', ''),
        'exp': datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return {
        'status': 'success',
        'token': token,
        'gestionnaire': {
            'id': gestionnaire.get('id'),
            'username': gestionnaire.get('username'),
            'nom': gestionnaire.get('nom'),
            'prenom': gestionnaire.get('prenom'),
            'role': gestionnaire.get('role', 'assurances'),
            'agence_id': gestionnaire.get('agence_id', 'AG01'),
            'email': gestionnaire.get('email', email_clean),
            'picture_url': picture or gestionnaire.get('picture_url', '')
        },
        'is_new_user': is_new_user
    }


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise PermissionError('Token expire, veuillez vous reconnecter')
    except jwt.InvalidTokenError:
        raise PermissionError('Token invalide')

