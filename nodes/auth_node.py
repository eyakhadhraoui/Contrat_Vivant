from tools.auth_context import resolve_gestionnaire
from tools.audit_log_tool import log_decision


def authenticate(state):
    token = state.get("token")

    payload = resolve_gestionnaire(token)

    state["gestionnaire_id"] = payload.get("gestionnaire_id", "G123")
    state["gestionnaire_nom"] = payload.get("nom", "")
    state["gestionnaire_prenom"] = payload.get("prenom", "")
    state["gestionnaire_role"] = payload.get("role", "assurances")
    state["gestionnaire_agence"] = payload.get("agence_id", "AG01")

    log_decision("authenticate", {
        "gestionnaire_id": state["gestionnaire_id"],
        "role": state["gestionnaire_role"],
    })
    print(f"[AUTH] Gestionnaire {state['gestionnaire_id']} authentifie ({state['gestionnaire_role']})")
    return state
