import time
import json
import os
import sys

# ensure project root is on sys.path so imports like `graph.workflow` resolve
proj_root = os.getcwd()
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from graph.workflow import graph

QUEUE_FILE = os.path.join(os.getcwd(), 'data', 'events_queue.jsonl')
AUDIT_FILE = os.path.join(os.getcwd(), 'data', 'audit_log.jsonl')


def process_event(record):
    state = {
        'token': None,
        'contrat_id': record.get('contrat_id'),
        'modification_type': record.get('event_type')
    }
    try:
        res = graph.invoke(state)
    except Exception as e:
        res = {'error': str(e)}

    # persist audit
    out = {
        'event_id': record.get('event_id'),
        'contrat_id': record.get('contrat_id'),
        'event_type': record.get('event_type'),
        'result': res,
        'processed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    with open(AUDIT_FILE, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == '__main__':
    print('Worker started, watching', QUEUE_FILE)
    while True:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r', encoding='utf-8') as fh:
                lines = fh.read().strip().splitlines()
            if lines:
                # process first line and rewrite queue
                first = lines[0]
                rest = lines[1:]
                try:
                    record = json.loads(first)
                    process_event(record)
                except Exception as e:
                    print('worker error processing record', e)
                # rewrite remaining
                with open(QUEUE_FILE, 'w', encoding='utf-8') as fh:
                    fh.write('\n'.join(rest) + ('\n' if rest else ''))
        time.sleep(1)
