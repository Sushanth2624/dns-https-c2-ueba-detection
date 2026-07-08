"""Build a labeled multi-entity evaluation corpus from single-host captures.

Single-host lab adaptation of the multi-VM design: each real capture (benign + one per attack
type) is relabeled onto a synthetic entity IP, and a slice of benign background is blended into
every attack entity so that detection is non-trivial (per the risk register: "mix with heavy
benign"). Ground truth (label, attack type, attack start) is recorded per entity, and the benign
JA3 set is frozen to a baseline file so ja3_rarity is measured against benign, not the whole mix.

Output (under out_dir):
  dns.log ssl.log conn.log http.log   merged JSON Zeek logs, one line per record, orig_h = entity
  ground_truth.json                   {entity: {label, attack_type, attack_start}}
  ja3_baseline.txt                    benign client JA3 hashes, one per line
  signature_hits.json                 {scenario: n_suricata_alert_events}
"""
from __future__ import annotations
import json
import random
from pathlib import Path

from ..parsers import zeek as zeek_parser
from ..parsers import suricata as suri_parser

LOG_KINDS = ("dns", "ssl", "conn", "http")

ATTACK_ENTITIES = {
    "beacon": "10.10.10.11",
    "dga": "10.10.10.12",
    "dns_tunnel": "10.10.10.13",
    "doh": "10.10.10.14",
}
BENIGN_ENTITIES = [f"10.10.20.{i}" for i in range(2, 8)]   # six benign hosts


def _load_logs(cap_dir: Path) -> dict:
    out = {}
    for kind in LOG_KINDS:
        p = cap_dir / f"{kind}.log"
        out[kind] = list(zeek_parser.read_log(p)) if p.exists() else []
    mp = cap_dir / "manifest.json"
    out["_manifest"] = json.loads(mp.read_text()) if mp.exists() else {}
    return out


def _signature_hits(cap_dir: Path) -> int:
    eve = cap_dir / "eve.json"
    if not eve.exists():
        return 0
    return sum(1 for _ in suri_parser.read_eve(eve, "alert"))


def _relabel(records, entity):
    out = []
    for r in records:
        r = dict(r)
        r["id.orig_h"] = entity
        out.append(r)
    return out


def build_corpus(captures_dir: str | Path, out_dir: str | Path, seed: int = 42) -> dict:
    rnd = random.Random(seed)
    captures_dir = Path(captures_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    benign = _load_logs(captures_dir / "benign")
    merged = {kind: [] for kind in LOG_KINDS}
    ground_truth: dict[str, dict] = {}
    signature_hits: dict[str, int] = {"benign": _signature_hits(captures_dir / "benign")}

    # ---- benign entities: partition benign records round-robin across BENIGN_ENTITIES ----
    for kind in LOG_KINDS:
        recs = list(benign[kind])
        rnd.shuffle(recs)
        for i, r in enumerate(recs):
            ent = BENIGN_ENTITIES[i % len(BENIGN_ENTITIES)]
            merged[kind].append({**r, "id.orig_h": ent})
    for ent in BENIGN_ENTITIES:
        ground_truth[ent] = {"label": 0, "attack_type": None, "attack_start": None}

    # ---- attack entities: attack records + a benign background slice, all under one entity ----
    for scenario, ent in ATTACK_ENTITIES.items():
        cap = captures_dir / scenario
        if not cap.exists():
            continue
        logs = _load_logs(cap)
        signature_hits[scenario] = _signature_hits(cap)
        for kind in LOG_KINDS:
            merged[kind].extend(_relabel(logs[kind], ent))
            # blend benign background so the attack host also does normal things
            bg = list(benign[kind])
            rnd.shuffle(bg)
            n_bg = {"dns": 8, "ssl": 4, "conn": 8, "http": 4}[kind]
            merged[kind].extend(_relabel(bg[:n_bg], ent))
        ground_truth[ent] = {
            "label": 1,
            "attack_type": scenario,
            "attack_start": logs["_manifest"].get("start"),
        }

    # ---- write merged JSON Zeek logs ----
    for kind in LOG_KINDS:
        with open(out_dir / f"{kind}.log", "w") as fh:
            for r in merged[kind]:
                fh.write(json.dumps(r) + "\n")

    # ---- frozen benign JA3 baseline ----
    benign_ja3 = {r.get("ja3") for r in benign["ssl"] if r.get("ja3") and r.get("ja3") != "-"}
    (out_dir / "ja3_baseline.txt").write_text(
        "\n".join(sorted(benign_ja3)) + ("\n" if benign_ja3 else ""))

    (out_dir / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2))
    (out_dir / "signature_hits.json").write_text(json.dumps(signature_hits, indent=2))

    return {
        "entities": len(ground_truth),
        "benign": len(BENIGN_ENTITIES),
        "attacks": sum(1 for v in ground_truth.values() if v["label"] == 1),
        "benign_ja3": len(benign_ja3),
        "signature_hits": signature_hits,
    }
