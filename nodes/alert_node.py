from tools.audit_log_tool import log_decision
from tools.analysis_helpers import build_alert_explanation


def build_alert(state):
    contrat = state["contrat_data"]
    sinistres = state["sinistres_data"]
    risk = state.get("risk_analysis") or {}

    explication = build_alert_explanation(contrat, sinistres, risk)
    reco = risk.get("recommendation") or {}

    state["alert"] = {
        "contrat_id": state["contrat_id"],
        "client": contrat.get("client"),
        "event_type": state.get("event_type"),
        "urgency_level": state.get("urgency_level"),
        "urgency_score": state.get("urgency_score"),
        "confidence": state.get("confidence"),
        "top_factors": state.get("top_factors"),
        "anomalies": state.get("anomalies"),
        "missing_data": state.get("missing_data"),
        "recommendation_action": reco.get("action"),
        "recommendation_label": reco.get("label"),
        "explication_llm": explication,
        "alert_card": state.get("alert_card"),
    }
    log_decision("alert_built", {
        "urgency_level": state.get("urgency_level"),
        "score": state.get("urgency_score"),
        "confidence": state.get("confidence"),
    })
    return state
