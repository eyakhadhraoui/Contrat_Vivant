"""
AlertNotificationAgent : Agent Communication & Alertes.
Rôle : Synthèse rédactionnelle, ciblage des équipes, construction des cartes d'alerte,
formulation des recommandations et diffusion des notifications multicanales.
"""

from typing import Dict, Any
from nodes.summarizer_node import summarize_dossier
from nodes.alert_node import build_alert
from nodes.recommendation_node import generate_recommendation
from nodes.routing_node import route_to_gestionnaire
from nodes.cross_notification_node import cross_notify
from tools.audit_log_tool import log_decision


class AlertNotificationAgent:
    """Agent spécialisé dans la rédaction des synthèses, la structuration des cartes d'alerte et les notifications multicanales."""

    def __init__(self, name: str = "AlertNotificationAgent"):
        self.name = name

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute le workflow de communication et d'alerte :
        - Synthèse du dossier par LLM
        - Construction de la carte d'alerte
        - Génération des recommandations d'action
        - Routage vers les gestionnaires cibles (Assurances / Sinistres)
        - Notification proactive multicanal (Email / Teams)
        """
        # 1. Résumé du dossier
        state = summarize_dossier(state)

        # 2. Construction de la carte d'alerte
        state = build_alert(state)

        # 3. Génération des recommandations
        state = generate_recommendation(state)

        # 4. Routage vers l'équipe / le gestionnaire adéquat
        state = route_to_gestionnaire(state)

        # 5. Diffusion des notifications multicanales si nécessaire
        state = cross_notify(state)

        # Traçabilité des métadonnées de l'agent
        routed_gestionnaires = [
            g.get("id") for g in (state.get("routed_to") or [])
            if isinstance(g, dict) and "id" in g
        ]

        agent_log = {
            "agent": self.name,
            "status": "success",
            "routed_to": routed_gestionnaires,
            "routing_alerte": state.get("routing_alerte", False),
            "notified_count": len(state.get("gestionnaires_a_notifier") or []),
            "has_summary": bool(state.get("resume_dossier")),
        }

        metadata = state.get("agent_metadata") or {}
        metadata["alert_agent"] = agent_log
        state["agent_metadata"] = metadata

        log_decision("alert_agent_executed", agent_log)
        print(f"[{self.name}] Alertes & Notifications prêtes : {len(routed_gestionnaires)} gestionnaire(s) ciblé(s)")
        return state


def run_alert_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Point d'entrée utilisable comme nœud LangGraph pour l'agent de communication & alerte."""
    agent = AlertNotificationAgent()
    return agent.execute(state)
