from tools.cross_notification_tool import (
    get_gestionnaires_sinistres_concernes,
    get_gestionnaire_assurances_du_contrat,
)
from tools.notification_tool import send_email, send_teams
from tools.audit_log_tool import log_decision
from tools.analysis_helpers import run_cross_analysis
from tools.email_templates import render_contrat_modification_email, render_sinistre_email
from tools.si_contrats_tool import get_contrat
from tools.si_sinistres_tool import get_sinistres


def cross_notify(state):
    contrat_id = state["contrat_id"]
    modification_type = state.get("modification_type")
    role = state.get("gestionnaire_role")

    destinataires = []
    sujet = None
    plain = None
    html = None

    if modification_type == "contrat" and role == "assurances":
        destinataires = get_gestionnaires_sinistres_concernes(contrat_id)
        contrat = state.get("contrat_data") or get_contrat(contrat_id) or {}
        nb_sinistres = len(state.get("sinistres_data") or get_sinistres(contrat_id) or [])
        sujet = f"Modification du contrat {contrat_id}"
        plain, html = render_contrat_modification_email(
            contrat_id,
            contrat.get("client", "N/A"),
            state["gestionnaire_id"],
            nb_sinistres,
        )

    elif modification_type == "sinistre" and role == "sinistres":
        gestionnaire = get_gestionnaire_assurances_du_contrat(contrat_id)
        destinataires = [gestionnaire] if gestionnaire else []
        sujet = f"Modification sinistre — contrat {contrat_id}"

        contrat_data = state.get("contrat_data") or get_contrat(contrat_id)
        sinistres_data = state.get("sinistres_data") or get_sinistres(contrat_id)
        if contrat_data and sinistres_data is not None:
            risk = run_cross_analysis(contrat_data, sinistres_data)
            state["risk_analysis"] = risk
            state["anomalies"] = risk.get("anomalies", [])
            state["analysis_triggered"] = True

        plain, html = render_sinistre_email(
            event="Modification sinistre",
            sinistre_id=state.get("sinistre_id") or "N/A",
            contrat_id=contrat_id,
            montant=(sinistres_data[0].get("montant_declare") if sinistres_data else 0),
            gestionnaire_id=state["gestionnaire_id"],
            risk=state.get("risk_analysis"),
        )

    for destinataire in destinataires:
        if destinataire.get("email") and plain:
            send_email(destinataire["email"], sujet, plain, html)

    if plain:
        try:
            send_teams(plain)
        except Exception as e:
            print(f"Notification Teams non envoyee : {e}")

    state["gestionnaires_a_notifier"] = destinataires
    log_decision("cross_notify", {
        "modification_type": modification_type,
        "role": role,
        "destinataires": [d["id"] for d in destinataires],
        "analysis_triggered": state.get("analysis_triggered", False),
    })
    return state
