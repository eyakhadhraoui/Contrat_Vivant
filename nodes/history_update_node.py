import json
from config.settings import HISTORIQUE_PATH
from tools.audit_log_tool import log_decision

def update_history(state):
    statuts_sans_ecriture = ["rejete", "en_attente_bon_gestionnaire"]

    if state["validation_status"] in statuts_sans_ecriture:
        log_decision("history_update", {"status": f"aucune mise à jour ({state['validation_status']})"})
        return state

    try:
        with open(HISTORIQUE_PATH, encoding="utf-8") as f:
            historique = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        historique = []

    historique.append({
        "contrat_id": state["contrat_id"],
        "alert": state["alert"],
        "validation_status": state["validation_status"],
        "valide_par_gestionnaire_id": state["gestionnaire_id"],
        "valide_par_role": state["gestionnaire_role"]
    })

    with open(HISTORIQUE_PATH, "w", encoding="utf-8") as f:
        json.dump(historique, f, ensure_ascii=False, indent=2)

    log_decision("history_update", {"status": "historique mis à jour"})
    return state