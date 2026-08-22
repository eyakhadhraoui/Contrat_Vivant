from abc import ABC, abstractmethod

class BaseRule(ABC):
    name: str = "base_rule"

    @abstractmethod
    def check(self, contrat: dict, sinistres: list) -> dict | None:
        """
        Retourne un dict d'anomalie si la règle se déclenche, sinon None.
        Format attendu : {"rule": self.name, "message": "...", "severity": "faible|moyen|eleve"}
        """
        pass