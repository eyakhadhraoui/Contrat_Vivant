"""
SupervisorAgent & Système Multi-Agents — Le Contrat Vivant.
Rôle : Agent Superviseur & Orchestrateur général coordonnant les sous-agents métiers
(CollectorAgent, RiskAnalysisAgent, AlertNotificationAgent) et la boucle de validation humaine (HITL).
"""

from typing import Dict, Any
from agents.collector_agent import CollectorAgent
from agents.risk_agent import RiskAnalysisAgent
from agents.alert_agent import AlertNotificationAgent
from nodes.human_validation_node import human_validation
from nodes.history_update_node import update_history
from tools.audit_log_tool import log_decision


class SupervisorAgent:
    """
    Agent Superviseur / Orchestrateur :
    - Pilote la séquence d'exécution des agents spécialisés selon l'état du dossier.
    - Consolide la traçabilité complète de l'exécution multi-agents dans `agent_metadata`.
    - Gère la boucle d'approbation humaine (Human In The Loop) et le contrôle d'accès SI.
    """

    def __init__(
        self,
        name: str = "SupervisorAgent",
        collector: CollectorAgent = None,
        risk_agent: RiskAnalysisAgent = None,
        alert_agent: AlertNotificationAgent = None,
    ):
        self.name = name
        self.collector = collector or CollectorAgent()
        self.risk_agent = risk_agent or RiskAnalysisAgent()
        self.alert_agent = alert_agent or AlertNotificationAgent()

    def run_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestration complète du workflow multi-agents de A à Z.
        """
        if "agent_metadata" not in state or state["agent_metadata"] is None:
            state["agent_metadata"] = {}

        state["agent_metadata"]["supervisor_status"] = "started"

        # Step 1: Collecte & Intégration SI
        print(f"[{self.name}] Step 1 -> Invocation du CollectorAgent...")
        state = self.collector.execute(state)

        # Step 2: Analyse des Risques & Règles
        print(f"[{self.name}] Step 2 -> Invocation du RiskAnalysisAgent...")
        state = self.risk_agent.execute(state)

        # Step 3: Structuration Alertes & Notifications
        print(f"[{self.name}] Step 3 -> Invocation du AlertNotificationAgent...")
        state = self.alert_agent.execute(state)

        # Step 4: Soumission à la boucle de Validation Humaine (HITL)
        print(f"[{self.name}] Step 4 -> Contrôle de la validation humaine (HITL)...")
        state = human_validation(state)

        # Step 5: Mise à jour de l'historique SI (si statut valide)
        state = update_history(state)

        state["agent_metadata"]["supervisor_status"] = "completed"
        log_decision("supervisor_workflow_completed", {
            "contrat_id": state.get("contrat_id"),
            "urgency_level": state.get("urgency_level"),
            "validation_status": state.get("validation_status"),
        })

        print(f"[{self.name}] Workflow terminé avec succès pour le contrat {state.get('contrat_id')}.")
        return state


def supervisor_orchestrate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Point d'entrée du superviseur pour orchestrer l'ensemble des agents."""
    supervisor = SupervisorAgent()
    return supervisor.run_workflow(state)
