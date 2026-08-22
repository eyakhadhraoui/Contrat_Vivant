import json
import logging
from datetime import datetime
from database.db_connection import get_connection, ensure_rag_and_chat_tables

logger = logging.getLogger(__name__)

# Assurer l'existence des tables
ensure_rag_and_chat_tables()


def save_chat_message(gestionnaire_id: str, sender: str, message: str, sources: list = None, session_id: str = 'default') -> dict:
    """Enregistre un message (utilisateur ou assistant) dans la base MySQL."""
    if not gestionnaire_id or not message:
        return {}

    sources_json = json.dumps(sources or [], ensure_ascii=False) if sources else None
    
    try:
        conn = get_connection()
        if not conn:
            return {}
        cur = conn.cursor()
        sql = """
            INSERT INTO chat_messages (session_id, gestionnaire_id, sender, message, sources, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        cur.execute(sql, (session_id, gestionnaire_id, sender, message, sources_json))
        conn.commit()
        msg_id = cur.lastrowid
        cur.close()
        conn.close()

        return {
            "id": msg_id,
            "session_id": session_id,
            "gestionnaire_id": gestionnaire_id,
            "sender": sender,
            "message": message,
            "sources": sources or [],
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur sauvegarde message chat dans MySQL: {e}")
        return {}


def get_chat_history(gestionnaire_id: str, session_id: str = 'default', limit: int = 100) -> list:
    """Récupère l'historique complet des messages pour le gestionnaire."""
    if not gestionnaire_id:
        return []

    try:
        conn = get_connection()
        if not conn:
            return []
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT id, session_id, gestionnaire_id, sender, message, sources, created_at
            FROM chat_messages
            WHERE gestionnaire_id = %s AND (session_id = %s OR %s = 'all')
            ORDER BY created_at ASC, id ASC
            LIMIT %s
        """
        cur.execute(sql, (gestionnaire_id, session_id, session_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for r in rows:
            sources_val = []
            if r.get('sources'):
                try:
                    sources_val = json.loads(r['sources']) if isinstance(r['sources'], str) else r['sources']
                except Exception:
                    sources_val = []

            dt = r.get('created_at')
            time_str = dt.strftime('%H:%M') if isinstance(dt, datetime) else ''

            results.append({
                "id": r.get('id'),
                "sender": r.get('sender'),
                "text": r.get('message'),
                "sources": sources_val,
                "time": time_str,
                "created_at": str(dt) if dt else ''
            })

        return results
    except Exception as e:
        logger.error(f"Erreur récupération historique chat depuis MySQL: {e}")
        return []


def clear_chat_history(gestionnaire_id: str, session_id: str = 'default') -> bool:
    """Supprime l'historique de discussion pour un gestionnaire."""
    if not gestionnaire_id:
        return False

    try:
        conn = get_connection()
        if not conn:
            return False
        cur = conn.cursor()
        sql = "DELETE FROM chat_messages WHERE gestionnaire_id = %s"
        params = [gestionnaire_id]
        if session_id and session_id != 'all':
            sql += " AND session_id = %s"
            params.append(session_id)
        cur.execute(sql, tuple(params))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Erreur suppression historique chat: {e}")
        return False
