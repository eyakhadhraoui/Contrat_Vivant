from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import json
import os

router = APIRouter()

EVENTS_QUEUE_FILE = os.path.join(os.getcwd(), 'data', 'events_queue.jsonl')

class EventModel(BaseModel):
    event_type: str
    contrat_id: str
    payload: dict = {}
    timestamp: str | None = None
    source: str | None = None


@router.post('/events', status_code=202)
def post_event(evt: EventModel):
    event_id = str(uuid.uuid4())
    record = {
        'event_id': event_id,
        'event_type': evt.event_type,
        'contrat_id': evt.contrat_id,
        'payload': evt.payload,
        'timestamp': evt.timestamp,
        'source': evt.source,
    }
    try:
        os.makedirs(os.path.dirname(EVENTS_QUEUE_FILE), exist_ok=True)
        with open(EVENTS_QUEUE_FILE, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {'status': 'accepted', 'event_id': event_id}
