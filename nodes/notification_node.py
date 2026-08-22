from tools.notification_tool import send_email, send_teams
from tools.email_templates import render_alert_email


def notify_if_urgent(state):
    level = state.get("urgency_level", "faible")
    if level in ("eleve", "critique"):
        plain, html = render_alert_email(state)
        send_email(
            state["routed_to"],
            f"Alerte {level.upper()} — dossier {state.get('contrat_id', 'N/A')}",
            plain,
            html,
        )
        try:
            send_teams(plain)
        except Exception as e:
            print(f"Notification Teams non envoyee : {e}")
        state["notified"] = True
    else:
        state["notified"] = False
    return state
