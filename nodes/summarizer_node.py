from llm.gemini_client import ask_gemini
from llm.prompts.summarize_dossier import build_summary_prompt
from tools.audit_log_tool import log_decision
import json


def _generate_expert_summary(contrat: dict, sinistres: list, anomalies: list, urgency_level: str) -> str:
    """Génère une synthèse experte, structurée et professionnelle du dossier basée sur les règles métier du SI."""
    client_name = contrat.get('client') or contrat.get('client_id') or 'Client Assuré'
    contrat_id = contrat.get('id', 'N/A')
    c_type = str(contrat.get('type_contrat', contrat.get('type', 'Auto'))).upper()
    statut = str(contrat.get('statut', 'actif')).upper()
    garantie_max = float(contrat.get('garantie_max', 0))
    franchise = float(contrat.get('franchise', 0))
    prime_mensuelle = float(contrat.get('prime_mensuelle', 0))
    total_sinistres_montant = sum(float(s.get('montant_declare', 0)) for s in sinistres)

    # 1. Analyse des sinistres
    if sinistres:
        sinistres_str = f"Le dossier comporte {len(sinistres)} sinistre(s) déclaré(s) pour un montant total cumulé de {total_sinistres_montant:,.2f} DT."
    else:
        sinistres_str = "Aucun sinistre n'a été déclaré à ce jour sur ce contrat."

    # 2. Analyse des anomalies
    if anomalies:
        anomalies_items = "\n".join([
            f"   • [{a.get('severity', 'moyen').upper()}] {a.get('rule', 'Anomalie')} : {a.get('message', '')}"
            for a in anomalies
        ])
        anomalies_str = f"Des signaux d'alerte ont été identifiés par le moteur de règles métier :\n{anomalies_items}"
    else:
        anomalies_str = "Aucune anomalie ni dépassement de plafond détecté. Le dossier est en parfaite conformité avec les règles de gestion."

    # 3. Recommandation
    if urgency_level == "eleve":
        reco = "⚠️ **Action requise sous 24h** : Blocage conservatoire recommandé ou expertise approfondie avant tout décaissement."
    elif urgency_level == "moyen":
        reco = "🔍 **Surveillance recommandée** : Vérification des pièces justificatives et contrôle des plafonds par le gestionnaire référent."
    else:
        reco = "✅ **Revue planifiée à 90 jours** : Aucune anomalie bloquante. Le contrat peut être maintenu dans ses conditions actuelles."

    return (
        f"### 📌 Synthèse Générale du Dossier\n"
        f"Le contrat **{contrat_id}** ({c_type}) souscrit par **{client_name}** est actuellement **{statut}** avec une garantie maximale de **{garantie_max:,.2f} DT** (franchise : {franchise:,.2f} DT, prime : {prime_mensuelle:,.2f} DT/mois).\n"
        f"{sinistres_str}\n\n"
        f"### ⚠️ Signaux et Règles Métier (Niveau d'urgence : {urgency_level.upper()})\n"
        f"{anomalies_str}\n\n"
        f"### 💡 Recommandation Actionnable\n"
        f"{reco}\n\n"
        f"### ✋ Validation Manuelle du Gestionnaire (HITL)\n"
        f"Le gestionnaire peut utiliser les boutons ci-dessous pour **Valider & Appliquer** la décision, la **Rejeter** ou choisir **Pas maintenant**."
    )


def summarize_dossier(state):
    contrat = state.get("contrat_data", {})
    sinistres = state.get("sinistres_data", [])
    anomalies = state.get("anomalies", [])
    urgency_level = state.get("urgency_level", "faible")

    prompt = build_summary_prompt(contrat, sinistres, anomalies, urgency_level)
    expert_fallback = _generate_expert_summary(contrat, sinistres, anomalies, urgency_level)

    llm_error = None
    try:
        raw_resume = ask_gemini(prompt, fallback_default=expert_fallback)
        # Si la réponse est un JSON brut ou contient une mention quota, utiliser la synthèse experte
        if not raw_resume or raw_resume.strip().startswith("{") or "Quota LLM" in raw_resume or raw_resume == "__LLM_QUOTA_EXHAUSTED__":
            resume = expert_fallback
        else:
            resume = raw_resume
    except Exception as exc:
        llm_error = str(exc)
        resume = expert_fallback

    state["resume_dossier"] = resume
    log_decision("summarize_dossier", {
        "contrat_id": state.get("contrat_id"),
        "llm_error": llm_error,
    })
    return state