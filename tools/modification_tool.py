from database.db_connection import get_connection

def lister_contrats(agence_id: str) -> list:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('''
        SELECT c.*, cl.nom as client_nom, cl.prenom as client_prenom
        FROM contrats c
        JOIN clients cl ON c.client_id = cl.id
        WHERE c.agence_id = %s
    ''', (agence_id,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    for r in results:
        r['client'] = r['client_prenom'] + ' ' + r['client_nom']
        r['garantie_max'] = float(r['garantie_max'])
        r['date_derniere_modif'] = str(r['date_derniere_modif'])
    return results

def lister_sinistres(agence_id: str) -> list:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('''
        SELECT s.*, cl.nom as client_nom, cl.prenom as client_prenom
        FROM sinistres s
        JOIN contrats c ON s.contrat_id = c.id
        JOIN clients cl ON c.client_id = cl.id
        WHERE s.agence_id = %s
    ''', (agence_id,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    for r in results:
        r['client'] = r['client_prenom'] + ' ' + r['client_nom']
        r['montant_declare'] = float(r['montant_declare'])
        r['date'] = str(r['date_declaration'])
    return results

def creer_contrat(contrat: dict) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''INSERT INTO contrats (id, client_id, type_contrat, garantie_max, statut, date_creation, date_derniere_modif, gestionnaire_createur_id, agence_id)
                    VALUES (%s,%s,%s,%s,%s,CURDATE(),CURDATE(),%s,%s)''',
                (contrat['id'], contrat['client_id'], contrat.get('type_contrat', 'vie'),
                 contrat['garantie_max'], contrat.get('statut', 'actif'),
                 contrat['gestionnaire_createur_id'], contrat['agence_id']))
    conn.commit()
    cur.close()
    conn.close()
    return contrat

def modifier_contrat(contrat_id: str, champs: dict) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    sets = ', '.join(k + ' = %s' for k in champs.keys())
    valeurs = list(champs.values()) + [contrat_id]
    cur.execute('UPDATE contrats SET ' + sets + ', date_derniere_modif = CURDATE() WHERE id = %s', valeurs)
    conn.commit()
    cur.close()
    conn.close()

    cur2 = conn.cursor(dictionary=True) if conn.is_connected() else None
    conn2 = get_connection()
    cur2 = conn2.cursor(dictionary=True)
    cur2.execute('SELECT * FROM contrats WHERE id = %s', (contrat_id,))
    result = cur2.fetchone()
    cur2.close()
    conn2.close()
    if not result:
        raise ValueError('Contrat introuvable : ' + contrat_id)
    return result

def contrat_a_sinistre_existant(contrat_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM sinistres WHERE contrat_id = %s', (contrat_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def creer_sinistre(sinistre: dict) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT statut FROM contrats WHERE id = %s', (sinistre['contrat_id'],))
    row = cur.fetchone()
    if row:
        c_statut = str(row[0] or '').strip().lower()
        if c_statut in ('suspendu', 'suspendue'):
            cur.close()
            conn.close()
            raise ValueError(f"Impossible de déclarer un sinistre : le contrat {sinistre['contrat_id']} est actuellement suspendu.")
        if c_statut in ('resilie', 'résilié', 'resiliée', 'résiliée'):
            cur.close()
            conn.close()
            raise ValueError(f"Impossible de déclarer un sinistre : le contrat {sinistre['contrat_id']} est résilié.")

    cur.execute('''INSERT INTO sinistres (id, contrat_id, type_sinistre, montant_declare, date_declaration, statut, gestionnaire_traitant_id, agence_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
                (sinistre['id'], sinistre['contrat_id'], sinistre.get('type_sinistre', 'Non specifie'),
                 sinistre['montant_declare'], sinistre['date'], sinistre.get('statut', 'en_cours'),
                 sinistre['gestionnaire_traitant_id'], sinistre['agence_id']))
    conn.commit()
    cur.close()
    conn.close()
    return sinistre

def modifier_sinistre(sinistre_id: str, champs: dict) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    sets = ', '.join(k + ' = %s' for k in champs.keys())
    valeurs = list(champs.values()) + [sinistre_id]
    cur.execute('UPDATE sinistres SET ' + sets + ' WHERE id = %s', valeurs)
    conn.commit()
    cur.close()
    conn.close()

    conn2 = get_connection()
    cur2 = conn2.cursor(dictionary=True)
    cur2.execute('SELECT * FROM sinistres WHERE id = %s', (sinistre_id,))
    result = cur2.fetchone()
    cur2.close()
    conn2.close()
    if not result:
        raise ValueError('Sinistre introuvable : ' + sinistre_id)
    return result
