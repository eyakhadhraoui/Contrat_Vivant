from datetime import date, datetime

from rules_engine.base_rule import BaseRule
from config.settings import URGENCY_THRESHOLD_SINISTRES_REPETES, SINISTRES_REPETES_PERIODE_JOURS


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


class SinistresRepetes(BaseRule):
    name = "sinistres_repetes"

    def check(self, contrat, sinistres):
        """Détecte si 2+ sinistres en 30 jours"""
        today = datetime.now()
        recent_sinistres = []
        for s in sinistres:
            parsed_date = _coerce_datetime(s.get("date"))
            if parsed_date and (today - parsed_date).days <= SINISTRES_REPETES_PERIODE_JOURS:
                recent_sinistres.append(s)

        if len(recent_sinistres) >= URGENCY_THRESHOLD_SINISTRES_REPETES:
            return {
                "rule": self.name,
                "message": f"{len(recent_sinistres)} sinistres en {SINISTRES_REPETES_PERIODE_JOURS} jours",
                "severity": "moyen"
            }

        return None


# Pour C001 avec S001 et S002:
# recent_sinistres = [S001 (01/07), S002 (10/07)]
# Résultat: ALERTE "2 sinistres en 30 jours"
    


# Pour C001 avec S001 et S002:
# recent_sinistres = [S001 (01/07), S002 (10/07)]
# Résultat: ALERTE "2 sinistres en 30 jours