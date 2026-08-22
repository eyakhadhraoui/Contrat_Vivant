from graph.workflow import graph

state = {
    'token': None,
    'contrat_id': 'C001',
    'modification_type': 'contrat',
}

res = graph.invoke(state)
print('event_type =', res.get('event_type'))
print('urgency_level =', res.get('urgency_level'))
print('anomalies =', res.get('anomalies'))
print('alert =', res.get('alert'))
print('recommendation =', res.get('recommendation'))
