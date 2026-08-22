from datetime import datetime, date

SEVERITY_FAIBLE = 'faible'
SEVERITY_MOYEN = 'moyen'
SEVERITY_ELEVE = 'eleve'
SEVERITY_CRITIQUE = 'critique'

RISK_WEIGHTS = {
    'recurrence': 0.20,
    'delai': 0.20,
    'montant_plafond': 0.25,
    'anciennete': 0.15,
    'pattern_suspect': 0.20,
}

URGENCY_THRESHOLDS = {
    'critique': 81,
    'eleve': 61,
    'moyen': 31,
    'faible': 0,
}

# Seuils metier legacy (regles deterministes)
URGENCY_THRESHOLD_ECART = 0.4
URGENCY_THRESHOLD_SINISTRES_REPETES = 2
SINISTRES_REPETES_PERIODE_JOURS = 30
RETARD_PAIEMENT_JOURS_LIMITE = 15

DELAI_RAPPROCHE_JOURS = 180
DELAI_ESPACE_JOURS = 730
ANCIENNETE_FRAUDE_JOURS = 90
