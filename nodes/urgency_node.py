from rules_engine.urgency_scorer import compute_urgency
from tools.audit_log_tool import log_decision


def calculate_urgency(state):
    risk = state.get("risk_analysis")
    if risk:
        result = {
            "urgency_level": risk["urgency_level"],
            "urgency_score": risk["score"],
            "urgency_breakdown": risk["urgency_breakdown"],
            "dominant_rule": risk["dominant_rule"],
            "confidence": risk["confidence"],
            "top_factors": risk["top_factors"],
            "recommendation": risk["recommendation"],
            "alert_card": risk["alert_card"],
            "missing_data": risk["missing_data"],
            "anomalies": risk["anomalies"],
        }
    else:
        result = compute_urgency(
            state.get("anomalies", []),
            state.get("contrat_data"),
            state.get("sinistres_data"),
        )
        state["risk_analysis"] = result

    state["urgency_level"] = result["urgency_level"]
    state["urgency_score"] = result["urgency_score"]
    state["urgency_breakdown"] = result["urgency_breakdown"]
    state["dominant_rule"] = result["dominant_rule"]
    state["confidence"] = result.get("confidence", "moyenne")
    state["top_factors"] = result.get("top_factors", [])
    state["alert_card"] = result.get("alert_card", state.get("alert_card", {}))
    state["anomalies"] = result.get("anomalies", state.get("anomalies", []))

    log_decision("urgency", {
        "urgency_level": state["urgency_level"],
        "urgency_score": state["urgency_score"],
        "confidence": state["confidence"],
        "dominant_rule": state["dominant_rule"],
    })
    return state
