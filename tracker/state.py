from __future__ import annotations

import json
from pathlib import Path

from .config import ROOT


STATE_PATH = ROOT / "state" / "seen.json"


def empty_state() -> dict:
    return {"schema_version": 1, "stores": {}, "last_digest_local_date": None}


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return empty_state()
    data = json.loads(path.read_text())
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported state schema")
    data.setdefault("stores", {})
    data.setdefault("last_digest_local_date", None)
    return data


def save_state(data: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)

