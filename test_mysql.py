from database.db_connection import get_connection

try:
    conn = get_connection()
    print('Connexion MySQL reussie !')
    conn.close()
except Exception as e:
    print('Erreur de connexion :', e)
