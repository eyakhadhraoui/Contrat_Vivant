from tools.audit_log_tool import log_decision
from tools.analysis_helpers import classify_event_deterministic


def classify_event(state):
    contrat = state.get("contrat_data", {})
    sinistres = state.get("sinistres_data", [])
    risk = state.get("risk_analysis") or {}
    modification_type = state.get("modification_type")

    event_type, justification = classify_event_deterministic(
        contrat, sinistres, risk, modification_type
    )

    state["event_type"] = event_type
    log_decision("classify_event", {
        "event_type": event_type,
        "justification": justification,
        "risk_score": risk.get("score"),
        "source": "risk_based",
    })
    return state
