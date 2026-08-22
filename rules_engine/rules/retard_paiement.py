from datetime import date, datetime

from rules_engine.base_rule import BaseRule
from config.settings import RETARD_PAIEMENT_JOURS_LIMITE


def _coerce_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            try:
                return datetime.strptime(text, "%Y-%m-%d")
            except ValueError:
                return None
    return None


class RetardPaiement(BaseRule):
    name = "retard_paiement"

    def check(self, contrat: dict, sinistres: list) -> dict | None:
        derniere_modif = contrat.get("date_derniere_modif")
        if not derniere_modif:
            return None

        parsed_date = _coerce_datetime(derniere_modif)
        if not parsed_date:
            return None

        jours_ecoules = (datetime.now() - parsed_date).days
        if jours_ecoules > RETARD_PAIEMENT_JOURS_LIMITE and contrat.get("statut") == "actif":
            return {
                "rule": self.name,
                "message": f"Aucune mise à jour depuis {jours_ecoules} jours sur un contrat actif",
                "severity": "faible"
            }
        return None