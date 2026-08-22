import bcrypt
from database.db_connection import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute('INSERT IGNORE INTO agences VALUES (%s,%s,%s,%s)', ('AG01', 'Agence Tunis Centre', 'Tunis', 'Avenue Habib Bourguiba'))
cur.execute('INSERT IGNORE INTO agences VALUES (%s,%s,%s,%s)', ('AG02', 'Agence Sfax', 'Sfax', 'Rue de la Republique'))

pwds = {'G123': 'password123', 'G456': 'password456', 'G789': 'password789', 'G321': 'password321'}
gestionnaires = [
    ('G123', 'Trabelsi', 'Ahmed', 'ahmed.trabelsi', 'eya.khadhraoui@esprit.tn', 'sinistres', 'AG01'),
    ('G456', 'Khelifi', 'Sarra', 'sarra.khelifi', 'eyakhadhraoui249@gmail.com', 'assurances', 'AG01'),
    ('G789', 'Bouazizi', 'Karim', 'karim.bouazizi', 'karim.test@example.com', 'sinistres', 'AG02'),
    ('G321', 'Mansour', 'Lina', 'lina.mansour', 'lina.test@example.com', 'assurances', 'AG02'),
]
for gid, nom, prenom, username, email, role, agence in gestionnaires:
    h = bcrypt.hashpw(pwds[gid].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cur.execute('INSERT IGNORE INTO gestionnaires (id, nom, prenom, username, email, password_hash, role, agence_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                (gid, nom, prenom, username, email, h, role, agence))

clients = [
    ('CL01', 'Ben Ayed', 'Sonia', 'sonia.ba@mail.com', '20111111', 'Tunis'),
    ('CL02', 'Hammami', 'Amine', 'amine.h@mail.com', '20222222', 'Ariana'),
    ('CL03', 'Maromi', 'Jalva', 'jalva.m@mail.com', '20333333', 'Sfax'),
    ('CL04', 'Trabelsi', 'Martra', 'martra.t@mail.com', '20444444', 'Tunis'),
    ('CL05', 'Mansour', 'Karem', 'karem.m@mail.com', '20555555', 'Sousse'),
]
for cid, nom, prenom, email, tel, adresse in clients:
    cur.execute('INSERT IGNORE INTO clients (id, nom, prenom, email, telephone, adresse) VALUES (%s,%s,%s,%s,%s,%s)',
                (cid, nom, prenom, email, tel, adresse))

contrats = [
    ('CSTR00001', 'CL01', 'auto', 150000000, 'actif', '2024-03-15', '2024-03-15', 'G456', 'AG01'),
    ('CSTR00002', 'CL02', 'habitation', 120000000, 'actif', '2024-02-10', '2024-02-10', 'G456', 'AG01'),
    ('CSTR00003', 'CL03', 'auto', 80000000, 'suspendu', '2024-01-01', '2024-01-01', 'G456', 'AG01'),
    ('CSTR00004', 'CL04', 'auto', 200000000, 'actif', '2023-12-20', '2023-12-20', 'G321', 'AG02'),
    ('CSTR00005', 'CL05', 'habitation', 50000000, 'resilie', '2023-11-05', '2023-11-05', 'G321', 'AG02'),
]
for cid, client, type_c, garantie, statut, dcreation, dmodif, gest, agence in contrats:
    cur.execute('INSERT IGNORE INTO contrats (id, client_id, type_contrat, garantie_max, statut, date_creation, date_derniere_modif, gestionnaire_createur_id, agence_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (cid, client, type_c, garantie, statut, dcreation, dmodif, gest, agence))

sinistres = [
    ('CSIN00001', 'CSTR00001', 'Auto - Carambolage', 120000000, '2022-03-31', 'en_cours', 'G123', 'AG01'),
    ('CSIN00002', 'CSTR00002', 'Habitation - Inondation', 100000000, '2022-03-21', 'traitement', 'G123', 'AG01'),
    ('CSIN00003', 'CSTR00003', 'Habitation - Inondation', 35000000, '2022-03-22', 'rejete', 'G789', 'AG02'),
    ('CSIN00004', 'CSTR00002', 'Auto - Carambolage', 30000000, '2022-03-22', 'en_cours', 'G123', 'AG01'),
    ('CSIN00005', 'CSTR00001', 'Auto - Carambolage', 100000000, '2022-03-21', 'en_cours', 'G123', 'AG01'),
    ('CSIN00006', 'CSTR00003', 'Auto - Carambolage', 14000000, '2023-02-02', 'complete', 'G789', 'AG02'),
    ('CSIN00007', 'CSTR00004', 'Auto - Carambolage', 30000000, '2023-02-02', 'traitement', 'G789', 'AG02'),
    ('CSIN00008', 'CSTR00001', 'Auto - Carambolage', 40000000, '2023-03-02', 'complete', 'G123', 'AG01'),
]
for sid, contrat, type_s, montant, date, statut, gest, agence in sinistres:
    cur.execute('INSERT IGNORE INTO sinistres (id, contrat_id, type_sinistre, montant_declare, date_declaration, statut, gestionnaire_traitant_id, agence_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                (sid, contrat, type_s, montant, date, statut, gest, agence))

conn.commit()
cur.close()
conn.close()
print('Donnees de test (format CSTR) inserees avec succes.')
