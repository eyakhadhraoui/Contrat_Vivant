from tools.permissions_tool import peut_valider_alerte
from tools.audit_log_tool import log_decision

def human_validation(state):
    if state.get('routing_alerte'):
        state['validation_status'] = 'escalade_aucun_gestionnaire'
        log_decision('human_validation_escalade', {'raison': 'aucun gestionnaire routable, escalade superviseur'})
        print('[ESCALADE] Aucun gestionnaire trouve pour ce dossier — escalade necessaire.')
        return state

    if not peut_valider_alerte(state.get('gestionnaire_role', ''), state.get('event_type', '')):
        state['validation_status'] = 'en_attente_bon_gestionnaire'
        log_decision('human_validation_bloquee', {'raison': 'role non autorise pour ce type d evenement'})
        return state

    state['validation_status'] = 'en_attente_validation'
    log_decision('human_validation', {'status': 'en_attente_validation'})
    return state
