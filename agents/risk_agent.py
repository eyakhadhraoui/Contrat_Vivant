"""
RiskAnalysisAgent : Agent Expert Risques & Moteur de Règles.
Rôle : Évaluation croisée des risques, détection des incohérences et calcul de criticité.
"""

from typing import Dict, Any
from nodes.cross_analysis_node import cross_analysis
from nodes.classify_node import classify_event
from nodes.urgency_node import calculate_urgency
from tools.audit_log_tool import log_decision


class RiskAnalysisAgent:
    """Agent expert en analyse des risques, exécution du moteur de règles et qualification d'urgence."""

    def __init__(self, name: str = "RiskAnalysisAgent"):
        self.name = name

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute la chaîne d'évaluation des risques :
        - Analyse croisée (règles métier déterministes + IA contextuelle LLM)
        - Classification de l'événement
        - Calcul du score et du niveau d'urgence (0-100)
        """
        # 1. Analyse croisée des données SI
        state = cross_analysis(state)

        # 2. Classification du type d'événement (contrat, sinistre, risque)
        state = classify_event(state)

        # 3. Calcul précis du score et niveau d'urgence
        state = calculate_urgency(state)

        # Traçabilité des métadonnées de l'agent
        agent_log = {
            "agent": self.name,
            "status": "success",
            "event_type": state.get("event_type"),
            "urgency_score": state.get("urgency_score"),
            "urgency_level": state.get("urgency_level"),
            "dominant_rule": state.get("dominant_rule"),
            "nb_anomalies": len(state.get("anomalies") or []),
            "confidence": state.get("confidence"),
        }

        metadata = state.get("agent_metadata") or {}
        metadata["risk_agent"] = agent_log
        state["agent_metadata"] = metadata

        log_decision("risk_agent_executed", agent_log)
        print(f"[{self.name}] Analyse terminée : Score={state.get('urgency_score')} | Urgence={state.get('urgency_level')}")
        return state


def run_risk_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Point d'entrée utilisable comme nœud LangGraph pour l'agent de risque."""
    agent = RiskAnalysisAgent()
    return agent.execute(state)
