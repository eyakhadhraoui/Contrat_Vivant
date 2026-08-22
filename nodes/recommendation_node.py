from tools.audit_log_tool import log_decision
from tools.analysis_helpers import build_recommendations_list


def generate_recommendation(state):
    contrat = state.get("contrat_data", {})
    sinistres = state.get("sinistres_data", [])
    risk = state.get("risk_analysis") or {}

    reco, cards = build_recommendations_list(contrat, sinistres, risk)
    state["recommendation"] = reco
    state["recommendations_list"] = cards

    log_decision("recommendation", {
        "reco": reco,
        "nb_cards": len(cards),
        "urgency_level": risk.get("urgency_level"),
        "urgency_score": risk.get("score"),
    })
    return state
