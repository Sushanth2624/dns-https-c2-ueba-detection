"""Read Suricata eve.json events, optionally filtered by event_type (dns, tls, http, alert)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator, Dict, Optional


def read_eve(path: str | Path, event_type: Optional[str] = None) -> Iterator[Dict]:
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event_type is None or ev.get("event_type") == event_type:
                yield ev
