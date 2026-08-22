"""
CollectorAgent : Agent de Collecte & Intégration SI.
Rôle : Extraction, agrégation, contrôle d'intégrité des données SI (Contrats & Sinistres),
et consolidation de l'historique chronologique du souscripteur.
"""

from typing import Dict, Any
from nodes.auth_node import authenticate
from nodes.collect_node import collect_data
from tools.audit_log_tool import log_decision


class CollectorAgent:
    """Agent spécialisé dans la collecte, la vérification d'intégrité et la consolidation des données SI."""

    def __init__(self, name: str = "CollectorAgent"):
        self.name = name

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute la collecte et l'intégration des données SI.
        """
        # 1. Authentification / résolution du rôle si token présent
        if state.get("token") and not state.get("gestionnaire_role"):
            state = authenticate(state)

        # 2. Collecte des données Contrat et Sinistres
        state = collect_data(state)

        # 3. Contrôle d'intégrité et évaluation de la complétude
        contrat = state.get("contrat_data") or {}
        sinistres = state.get("sinistres_data") or []

        missing_data = list(state.get("missing_data") or [])
        if not contrat.get("client"):
            if "Informations client manquantes" not in missing_data:
                missing_data.append("Informations client manquantes")
        if not contrat.get("garantie_max"):
            if "Plafond de garantie indéfini" not in missing_data:
                missing_data.append("Plafond de garantie indéfini")

        state["missing_data"] = missing_data

        # Évaluation du niveau de confiance de la collecte
        if not missing_data:
            confidence = "haute"
        elif len(missing_data) == 1:
            confidence = "moyenne"
        else:
            confidence = "faible"

        state["confidence"] = confidence

        # Horodatage et métadonnées d'exécution de l'agent
        agent_log = {
            "agent": self.name,
            "status": "success",
            "contrat_id": state.get("contrat_id"),
            "nb_sinistres": len(sinistres),
            "confidence": confidence,
            "missing_data": missing_data,
        }

        metadata = state.get("agent_metadata") or {}
        metadata["collector_agent"] = agent_log
        state["agent_metadata"] = metadata

        log_decision("collector_agent_executed", agent_log)
        print(f"[{self.name}] Données SI collectées pour contrat {state.get('contrat_id')} (Confiance: {confidence})")
        return state


def run_collector_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Point d'entrée utilisable comme nœud LangGraph pour l'agent de collecte."""
    agent = CollectorAgent()
    return agent.execute(state)
