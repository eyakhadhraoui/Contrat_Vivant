from decimal import Decimal

from rules_engine.base_rule import BaseRule
from config.settings import URGENCY_THRESHOLD_ECART

class EcartGarantieMontant(BaseRule):
    name = "ecart_garantie_montant"

    def check(self, contrat: dict, sinistres: list) -> dict | None:
        garantie_max = contrat.get("garantie_max", 0)
        if garantie_max == 0:
            return None

        garantie_max_decimal = Decimal(str(garantie_max))

        for sinistre in sinistres:
            montant = sinistre.get("montant_declare", 0)
            montant_decimal = Decimal(str(montant))
            ecart = (montant_decimal - garantie_max_decimal) / garantie_max_decimal
            if ecart > Decimal(str(URGENCY_THRESHOLD_ECART)):
                return {
                    "rule": self.name,
                    "message": f"Écart de {round(float(ecart * Decimal('100')))}% entre le montant déclaré ({montant}) et le plafond de garantie ({garantie_max})",
                    "severity": "eleve"
                }
        return None