"""Read Zeek logs (TSV or JSON) into dictionaries.
Zeek can emit classic TSV or JSON (json-logs). We support both.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator, Dict


def _read_tsv(path: Path) -> Iterator[Dict]:
    fields: list[str] = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("#fields"):
                fields = line.split("\t")[1:]
                continue
            if line.startswith("#") or not line:
                continue
            values = line.split("\t")
            yield dict(zip(fields, values))


def _read_json(path: Path) -> Iterator[Dict]:
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_log(path: str | Path) -> Iterator[Dict]:
    """Auto-detect JSON vs TSV Zeek log and yield records."""
    p = Path(path)
    with open(p) as fh:
        first = fh.readline().strip()
    if first.startswith("{"):
        yield from _read_json(p)
    else:
        yield from _read_tsv(p)
