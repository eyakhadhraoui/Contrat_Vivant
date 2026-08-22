from tools.si_contrats_tool import get_contrat
from tools.si_sinistres_tool import get_sinistres
from tools.audit_log_tool import log_decision


def collect_data(state):
    """Collecte le contrat et tous ses sinistres lies."""
    contrat_id = state["contrat_id"]
    contrat_data = get_contrat(contrat_id)

    if not contrat_data:
        raise ValueError(f"Contrat {contrat_id} introuvable")

    sinistres_data = get_sinistres(contrat_data["id"])

    state["contrat_data"] = contrat_data
    state["sinistres_data"] = sinistres_data
    state["contrat_id"] = contrat_data["id"]

    log_decision("collect_data", {
        "contrat_id": contrat_data["id"],
        "client": contrat_data.get("client"),
        "nb_sinistres": len(sinistres_data),
        "sinistres_ids": [s["id"] for s in sinistres_data],
        "acces_verifie_pour_role": state.get("gestionnaire_role", "assurances"),
    })

    print(f"[COLLECT] Contrat {contrat_data['id']} charge avec {len(sinistres_data)} sinistre(s)")
    return state
