import json
from pathlib import Path
from datetime import datetime
import uuid

_REVERTS_PATH = Path("data/reverts.json")


def _ensure_path():
    _REVERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _REVERTS_PATH.exists():
        with _REVERTS_PATH.open('w', encoding='utf-8') as f:
            json.dump([], f)


def save_revert(kind: str, target_id: str, previous: dict, actor: str) -> str:
    """Sauvegarde un snapshot permettant de revenir en arrière. Retourne un revert_id."""
    _ensure_path()
    with _REVERTS_PATH.open('r', encoding='utf-8') as f:
        items = json.load(f)

    revert_id = str(uuid.uuid4())
    entry = {
        "id": revert_id,
        "kind": kind,
        "target_id": target_id,
        "previous": previous,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat()
    }
    items.append(entry)
    with _REVERTS_PATH.open('w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return revert_id


def get_revert(revert_id: str) -> dict | None:
    _ensure_path()
    with _REVERTS_PATH.open('r', encoding='utf-8') as f:
        items = json.load(f)
    return next((i for i in items if i.get('id') == revert_id), None)


def list_reverts() -> list:
    _ensure_path()
    with _REVERTS_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)
    