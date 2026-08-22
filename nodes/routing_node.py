from tools.cross_notification_tool import (
    get_gestionnaires_sinistres_concernes,
    get_gestionnaire_assurances_du_contrat
)
from tools.audit_log_tool import log_decision

def route_to_gestionnaire(state):
    contrat_id = state['contrat_id']
    event_type = state.get('event_type', 'contrat')

    if event_type in ['sinistre', 'risque']:
        gestionnaires = get_gestionnaires_sinistres_concernes(contrat_id)
        raison = 'evenement de type ' + event_type + ' : routage vers gestionnaires sinistres avec dossier en cours'
    else:
        gestionnaire = get_gestionnaire_assurances_du_contrat(contrat_id)
        gestionnaires = [gestionnaire] if gestionnaire else []
        raison = 'evenement de type contrat : routage vers le gestionnaire assurances createur'

    if not gestionnaires:
        state['routed_to'] = []
        state['routing_alerte'] = True
        log_decision('routing_echec', {
            'contrat_id': contrat_id,
            'event_type': event_type,
            'raison': 'aucun gestionnaire trouve pour ce contrat/evenement'
        })
        return state

    state['routed_to'] = gestionnaires
    state['routing_alerte'] = False

    noms_complets = []
    for g in gestionnaires:
        prenom = g.get('prenom', '')
        nom = g.get('nom', '')
        noms_complets.append((prenom + ' ' + nom).strip())

    log_decision('routing', {
        'contrat_id': contrat_id,
        'event_type': event_type,
        'raison': raison,
        'gestionnaires_ids': [g['id'] for g in gestionnaires],
        'gestionnaires_noms': noms_complets
    })

    print('[ROUTING]', len(gestionnaires), 'gestionnaire(s) cible(s) :', ', '.join(noms_complets))
    return state
