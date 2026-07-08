"""Load and validate pipeline configuration from YAML."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class Config:
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        with open(path, "r") as fh:
            return cls(raw=yaml.safe_load(fh) or {})

    # convenience accessors
    def get(self, *keys, default=None):
        node = self.raw
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    @property
    def weights(self) -> dict[str, float]:
        return self.get("weights", default={}) or {}

    @property
    def ueba_weight(self) -> float:
        return float(self.get("ueba_weight", default=0.4))

    @property
    def thresholds(self) -> dict[str, float]:
        return self.get("thresholds", default={}) or {}

    @property
    def mitre_map(self) -> dict[str, list[str]]:
        return self.get("mitre_map", default={}) or {}
