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
    prime_annuelle = float(contrat.get('prime_annuelle', prime_mensuelle * 12 if prime_mensuelle else 0))
    total_sinistres_montant = sum(float(s.get('montant_declare', 0)) for s in sinistres)
    ratio_sinistralite = (total_sinistres_montant / garantie_max * 100) if garantie_max > 0 else 0.0

    # 1. Détail des sinistres
    if sinistres:
        items_sin = []
        for s in sinistres:
            s_id = s.get('id', 'N/A')
            s_type = s.get('type_sinistre', s.get('type', 'Sinistre'))
            s_m = float(s.get('montant_declare', 0))
            s_st = s.get('statut', 'en_cours')
            s_d = s.get('date', s.get('date_declaration', 'N/A'))
            items_sin.append(f"   • **Sinistre #{s_id}** ({s_type}) : **{s_m:,.2f} DT** — Statut : `{s_st}` (Déclaré le : {s_d})")
        sinistres_str = f"Le dossier répertorie **{len(sinistres)} sinistre(s)** pour un cumul déclaré de **{total_sinistres_montant:,.2f} DT** (consommation du plafond : **{ratio_sinistralite:.1f}%**) :\n" + "\n".join(items_sin)
    else:
        sinistres_str = "Aucun sinistre n'a été déclaré à ce jour sur ce contrat."

    # 2. Détail des anomalies
    if anomalies:
        anomalies_items = "\n".join([
            f"   • [{a.get('severity', 'moyen').upper()}] **{a.get('rule', 'Anomalie')}** : {a.get('message', '')}"
            for a in anomalies
        ])
        anomalies_str = f"Des signaux et règles métier ont été levés par le moteur d'analyse :\n{anomalies_items}"
    else:
        anomalies_str = "Aucune anomalie ni dépassement de plafond n'a été détecté. Le dossier présente un niveau de risque nominal."

    # 3. Recommandation
    if urgency_level in ["eleve", "critique"]:
        reco = (
            "⚠️ **Action Prioritaire Recommandée (Sous 24h)** :\n"
            "   1. Geler à titre conservatoire toute nouvelle indemnisation ou modification sur ce contrat.\n"
            "   2. Mandater une expertise d'assurance ou demander un contrôle approfondi des pièces justificatives.\n"
            "   3. Évaluer l'opportunité d'une révision du montant de garantie ou d'un réajustement de la franchise."
        )
    elif urgency_level == "moyen":
        reco = (
            "🔍 **Surveillance & Vérification Recommandées** :\n"
            "   1. Réclamer les factures et constatations d'experts pour les sinistres en cours.\n"
            "   2. Vérifier l'adéquation entre les garanties souscrites et le niveau d'exposition du souscripteur."
        )
    else:
        reco = (
            "✅ **Conformité Validée (Revue à 90 jours)** :\n"
            "   1. Le contrat s'inscrit dans les ratios normaux de gestion.\n"
            "   2. Maintien de la couverture aux conditions contractuelles actuelles."
        )

    return (
        f"### 📌 1. Fiche Synthétique & Cadre Contractuel\n"
        f"Le contrat **{contrat_id}** (Formule : **{c_type}**) souscrit par **{client_name}** est actuellement **{statut}**.\n"
        f"- **Garantie Maximale** : {garantie_max:,.2f} DT | **Franchise** : {franchise:,.2f} DT\n"
        f"- **Tarification** : {prime_mensuelle:,.2f} DT / mois ({prime_annuelle:,.2f} DT / an)\n\n"
        f"### 📊 2. Bilan Financier et Sinistralité\n"
        f"{sinistres_str}\n\n"
        f"### ⚠️ 3. Diagnostic de Sécurité et Signaux d'Alerte (Urgence : {urgency_level.upper()})\n"
        f"{anomalies_str}\n\n"
        f"### 💡 4. Plan d'Action & Préconisations Stratégiques\n"
        f"{reco}\n\n"
        f"### ✋ 5. Procédure de Validation Manuelle (HITL)\n"
        f"En tant que gestionnaire, vous disposez des actions suivantes :\n"
        f"  • **Valider & Appliquer** : Confirme l'analyse et applique l'ajustement préconisé sur le SI.\n"
        f"  • **Rejeter** : Invalide l'alerte si le risque est jugé tolérable.\n"
        f"  • **Pas maintenant** : Conserve le dossier en attente avec rappel ultérieur."
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