import json
import os
import argparse
from collections import Counter

AUDIT_FILE = os.path.join(os.getcwd(), 'data', 'audit_log.jsonl')


def load_audit():
    if not os.path.exists(AUDIT_FILE):
        return []
    with open(AUDIT_FILE, 'r', encoding='utf-8') as fh:
        return [json.loads(l) for l in fh.read().splitlines() if l.strip()]


def report(from_ts=None, to_ts=None):
    rows = load_audit()
    by_type = Counter()
    total = len(rows)
    for r in rows:
        etype = r.get('event_type') or r.get('result', {}).get('event_type') or 'unknown'
        by_type[etype] += 1

    print('Total processed events:', total)
    for k, v in by_type.items():
        print(f'- {k}: {v}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--from')
    parser.add_argument('--to')
    args = parser.parse_args()
    report(args.from, args.to)
