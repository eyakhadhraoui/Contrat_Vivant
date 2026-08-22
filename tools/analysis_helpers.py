from config.constants import SEVERITY_CRITIQUE, SEVERITY_ELEVE, SEVERITY_MOYEN
from rules_engine.risk_analyzer import analyze_risk


def classify_event_deterministic(contrat: dict, sinistres: list, risk: dict, modification_type: str | None) -> tuple[str, str]:
    """Classification basee sur le score de risque et le contexte metier."""
    score = risk.get("score", 0)
    level = risk.get("urgency_level", "faible")

    if level in (SEVERITY_CRITIQUE, SEVERITY_ELEVE) or score >= 61:
        return "risque", f"Score de risque {score}/100 ({level}) — dossier a traiter en priorite"

    if modification_type == "sinistre":
        return "sinistre", "Evenement lie a un sinistre"

    if modification_type == "contrat":
        if sinistres and score >= 31:
            return "risque", "Modification contrat avec sinistres actifs et score modere"
        return "contrat", "Evenement lie au contrat"

    if len(sinistres) >= 2 and score >= 31:
        return "risque", "Recurrence sinistres avec score modere ou superieur"

    if len(sinistres) == 1:
        return "sinistre", "Un sinistre isole a traiter"

    return "contrat", "Dossier contrat sans sinistre actif"


def build_alert_explanation(contrat: dict, sinistres: list, risk: dict) -> str:
    card = risk.get("alert_card") or {}
    client = contrat.get("client", "Client inconnu")
    score = risk.get("score", 0)
    level = risk.get("urgency_level", "faible")
    confidence = risk.get("confidence", "moyenne")

    lines = [
        f"Dossier {contrat.get('id', 'N/A')} — {client}",
        f"Score de risque : {score}/100 | Urgence : {level.upper()} | Confiance : {confidence}",
        f"Sinistres analyses : {len(sinistres)}",
    ]

    top = risk.get("top_factors") or []
    if top:
        lines.append("Facteurs principaux :")
        for i, factor in enumerate(top[:3], 1):
            lines.append(f"  {i}. {factor['label']} ({factor['contribution']} pts) — {factor['detail']}")

    missing = risk.get("missing_data") or []
    if missing:
        lines.append("Limites de l'analyse :")
        for item in missing:
            lines.append(f"  • {item}")

    reco = risk.get("recommendation") or {}
    if reco.get("detail"):
        lines.append(f"Recommandation : {reco['label']} — {reco['detail']}")

    disclaimer = card.get("disclaimer")
    if disclaimer:
        lines.append(disclaimer)

    return "\n".join(lines)


def build_recommendations_list(contrat: dict, sinistres: list, risk: dict) -> tuple[str, list]:
    """Genere recommandation graduee et cartes UI a partir de l'analyse de risque."""
    score = risk.get("score", 0)
    level = risk.get("urgency_level", "faible")
    reco = risk.get("recommendation") or {}
    primary = reco.get("detail") or "Surveiller le dossier."
    top = risk.get("top_factors") or []
    confidence = risk.get("confidence", "moyenne")
    montant_total = sum(float(s.get("montant_declare") or 0) for s in sinistres)

    factor_text = (
        " | ".join(f"{f['label']} ({f['contribution']} pts)" for f in top[:3])
        if top else "Aucun facteur de risque significatif"
    )

    cards = [
        {
            "id": 1,
            "title": "1. Score et urgence",
            "text": f"Score {score}/100 — urgence {level.upper()} — confiance {confidence}.",
            "icon": "🎯",
        },
        {
            "id": 2,
            "title": "2. Synthese du dossier",
            "text": (
                f"Contrat {contrat.get('id', 'N/A')} ({contrat.get('client', 'Client')}) : "
                f"{len(sinistres)} sinistre(s), {montant_total:,.0f} DT cumules."
            ),
            "icon": "🔍",
        },
        {
            "id": 3,
            "title": "3. Facteurs determinants",
            "text": factor_text,
            "icon": "⚠️",
        },
        {
            "id": 4,
            "title": f"4. {reco.get('label', 'Plan d action')}",
            "text": primary,
            "icon": "🕒",
        },
    ]

    return primary, cards


def run_cross_analysis(contrat: dict, sinistres: list) -> dict:
    """Point unique pour l'analyse metier — moteur de risque sinistres."""
    return analyze_risk(contrat, sinistres)
