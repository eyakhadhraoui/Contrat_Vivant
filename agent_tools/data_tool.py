import json
from config.settings import CONTRATS_PATH

def query_contrat_by_client(nom_client: str) -> str:
    '''Recherche les contrats d un client par son nom.'''
    with open(CONTRATS_PATH, encoding='utf-8') as f:
        contrats = json.load(f)
    resultats = [c for c in contrats if nom_client.lower() in c['client'].lower()]
    return str(resultats) if resultats else 'Aucun contrat trouve.'
