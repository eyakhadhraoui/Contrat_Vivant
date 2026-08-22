from rules_engine.rules.ecart_garantie_montant import EcartGarantieMontant
from rules_engine.rules.sinistres_repetes import SinistresRepetes
from rules_engine.rules.retard_paiement import RetardPaiement

RULES = [
    EcartGarantieMontant(),
    SinistresRepetes(),
    RetardPaiement()
]

def run_rules(contrat: dict, sinistres: list) -> list:
    anomalies = []
    for rule in RULES:
        result = rule.check(contrat, sinistres)
        if result:
            anomalies.append(result)
    return anomalies