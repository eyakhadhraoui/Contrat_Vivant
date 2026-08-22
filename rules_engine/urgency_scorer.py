from rules_engine.risk_analyzer import analyze_risk


def compute_urgency(anomalies: list, contrat: dict | None = None, sinistres: list | None = None) -> dict:
    """
    Calcule l'urgence via le moteur d'analyse de risque (score 0-100).
    Fallback minimal si contrat absent.
    """
    if contrat is not None:
        result = analyze_risk(contrat, sinistres or [])
        return {
            "urgency_level": result["urgency_level"],
            "urgency_score": result["score"],
            "urgency_breakdown": result["urgency_breakdown"],
            "dominant_rule": result["dominant_rule"],
            "confidence": result["confidence"],
            "top_factors": result["top_factors"],
            "recommendation": result["recommendation"],
            "alert_card": result["alert_card"],
            "missing_data": result["missing_data"],
            "anomalies": result["anomalies"],
        }

    return {
        "urgency_level": "faible",
        "urgency_score": 0,
        "urgency_breakdown": [],
        "dominant_rule": None,
        "confidence": "faible",
        "top_factors": [],
        "recommendation": {
            "action": "surveiller",
            "label": "Surveiller",
            "detail": "Donnees contrat insuffisantes pour analyse complete.",
        },
        "alert_card": {},
        "missing_data": ["contrat"],
        "anomalies": anomalies or [],
    }
