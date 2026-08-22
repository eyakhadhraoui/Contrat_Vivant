import os
from config.settings import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT


def get_connection():
    """Retourne une connexion MySQL avec détection automatique de l'hôte (Local / Docker)."""
    import mysql.connector

    # Si on est dans Docker (/app ou variable d'environnement), prioriser 'db', sinon 'localhost'
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('IN_DOCKER') == '1'
    if in_docker:
        hosts_to_try = [MYSQL_HOST or "db", "db", "localhost"]
    else:
        hosts_to_try = ["localhost", "127.0.0.1", MYSQL_HOST or "db"]

    passwords_to_try = [MYSQL_PASSWORD if MYSQL_PASSWORD is not None else ""]
    if "" not in passwords_to_try:
        passwords_to_try.append("")
    if "rootpassword" not in passwords_to_try:
        passwords_to_try.append("rootpassword")

    last_err = None
    for h in hosts_to_try:
        if not h:
            continue
        for p in passwords_to_try:
            try:
                return mysql.connector.connect(
                    host=h,
                    user=MYSQL_USER or "root",
                    password=p,
                    database=MYSQL_DATABASE or "assurance_db",
                    port=int(MYSQL_PORT or 3306),
                    connection_timeout=1
                )
            except Exception as e:
                last_err = e
                continue

    raise RuntimeError(f"Échec connexion MySQL: {last_err}")


def ensure_rag_and_chat_tables():
    """Crée automatiquement les tables rag_documents et chat_messages si elles n'existent pas encore."""
    try:
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) DEFAULT 'pdf',
                file_size INT DEFAULT 0,
                chunks_count INT DEFAULT 0,
                content_text LONGTEXT,
                uploaded_by VARCHAR(50) DEFAULT 'system',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(100) DEFAULT 'default',
                gestionnaire_id VARCHAR(50) NOT NULL,
                sender ENUM('user', 'bot') NOT NULL,
                message LONGTEXT NOT NULL,
                sources JSON DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Erreur initialisation tables RAG/Chat: {e}")



