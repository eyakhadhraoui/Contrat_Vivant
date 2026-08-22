"""
Workflow LangGraph Multi-Agents avec Superviseur — Le Contrat Vivant.
Orchestration hiérarchique des sous-agents métiers (Collector, RiskAnalysis, AlertNotification)
sous le contrôle du Superviseur et avec validation humaine (HITL).
"""

from langgraph.graph import StateGraph
from state.state import ContratVivantState
from agents.collector_agent import run_collector_agent
from agents.risk_agent import run_risk_agent
from nodes.summarizer_node import summarize_dossier
from agents.alert_agent import run_alert_agent
from agents.multi_agent_system import supervisor_orchestrate
from nodes.human_validation_node import human_validation
from nodes.history_update_node import update_history


# Construction du graphe multi-agents sous LangGraph
builder = StateGraph(ContratVivantState)

# 1. Ajout des sous-agents spécialisés et étapes de validation
builder.add_node("collector_agent", run_collector_agent)
builder.add_node("risk_agent", run_risk_agent)
builder.add_node("alert_agent", run_alert_agent)
builder.add_node("human_validation", human_validation)
builder.add_node("history_update", update_history)

# 2. Définition des transitions d'entrée et de sortie
builder.set_entry_point("collector_agent")

# Flux hiérarchique contrôlé par le système multi-agents :
# Collector -> Risk -> Alert (avec synthèse & recommandations) -> Validation HITL -> Timeline SI
builder.add_edge("collector_agent", "risk_agent")
builder.add_edge("risk_agent", "alert_agent")
builder.add_edge("alert_agent", "human_validation")
builder.add_edge("human_validation", "history_update")

builder.set_finish_point("history_update")

# Compilation du graphe
graph = builder.compile()