"""
Prompt structure pour l'analyse complementaire LLM.
Objectif : detecter des signaux que le moteur de regles deterministe
(rules_engine/risk_analyzer.py) ne capture pas nativement.
"""

import json

# Garde ce texte synchronise avec RISK_WEIGHTS dans config/constants.py :
# si un nouvel axe de scoring est ajoute au moteur de regles, ajoute-le ici aussi,
# sinon le LLM risque de "redecouvrir" un axe deja couvert.
COVERED_RULES_DESCRIPTION = """
Le moteur de regles evalue deja automatiquement ces axes — NE LES REPETE PAS :
1. Recurrence des sinistres (nombre total, meme cause ou causes differentes)
2. Delai entre sinistres (rapproches / espaces, en jours)
3. Montant cumule vs plafond de garantie (ratio, progression croissante, outlier portefeuille)
4. Anciennete du contrat au premier sinistre (fraude precoce potentielle)
5. Patterns suspects (circonstances similaires, sinistre juste apres un avenant, frequence elevee)
""".strip()


def build_cross_analysis_prompt(contrat: dict, sinistres: list, today: str) -> str:
    contrat_summary = {
        "id": contrat.get("id"),
        "statut": contrat.get("statut"),
        "type_contrat": contrat.get("type_contrat"),
        "garantie_max": contrat.get("garantie_max"),
        "prime_annuelle": contrat.get("prime_annuelle"),
        "franchise": contrat.get("franchise"),
        "date_souscription": contrat.get("date_souscription"),
        "date_derniere_modif": contrat.get("date_derniere_modif"),
        "score_risque_declare": contrat.get("score_risque"),
        "niveau_fraude_declare": contrat.get("niveau_fraude"),
        "probabilite_resiliation": contrat.get("probabilite_resiliation"),
        "historique_sinistres_texte": contrat.get("historique_sinistres"),
    }

    return f"""### ROLE
Tu es un analyste senior anti-fraude en assurance vie. Tu interviens EN COMPLEMENT
d'un moteur de regles deterministe qui a deja score ce dossier. Ta valeur ajoutee
est de reperer des signaux non triviaux : incoherences entre champs, contradictions
narratives, correlations que des regles fixes ne peuvent pas exprimer.

### CONTEXTE METIER
{COVERED_RULES_DESCRIPTION}

### DONNEES DU CONTRAT
{json.dumps(contrat_summary, ensure_ascii=False, indent=2)}

### SINISTRES LIES ({len(sinistres)} au total)
{json.dumps(sinistres, ensure_ascii=False, indent=2)}

### DATE DU JOUR
{today}

### TACHE
Identifie UNIQUEMENT des anomalies complementaires aux 5 axes deja couverts ci-dessus.
Exemples de signaux valides : incoherence entre profession declaree et nature du
sinistre, montant declare disproportionne par rapport au bien assure, description
de sinistre vague ou contradictoire avec une autre declaration, changement recent
de beneficiaire ou de coordonnees juste avant un sinistre.
N'invente aucun fait absent des donnees fournies ci-dessus.

### CONTRAINTES STRICTES
- Chaque anomalie doit citer un chiffre ou un fait precis tire des donnees fournies.
- Ne jamais repeter un des 5 axes deja couverts par le moteur de regles.
- Si aucune anomalie complementaire fiable n'est identifiable, retourne une liste
  vide plutot que de forcer un signal faible ou generique.
- "severity" doit refleter un risque reel de fraude/erreur, pas une simple
  bizarrerie administrative sans consequence financiere.

### FORMAT DE SORTIE — JSON STRICT UNIQUEMENT, AUCUN TEXTE AUTOUR
{{
  "anomalies": [
    {{"rule": "nom_court_snake_case", "message": "description precise avec chiffres/faits", "severity": "faible|moyen|eleve"}}
  ]
}}

Si rien a signaler, retourne exactement : {{"anomalies": []}}"""
