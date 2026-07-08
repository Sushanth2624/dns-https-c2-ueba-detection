"""Adapter mapping OpenUBA outputs onto the UEBA contract.

OpenUBA writes anomalies/risk to its own store (an Elasticsearch index). This adapter reads those
docs and returns UebaRecord objects identical in shape to the fallback, so the rest of the pipeline
never needs to know which producer was used. It exposes the same `.score(entity, feature_vec)`
method as BaselineUEBA (looking the entity up in the fetched window) plus a streaming `.fetch()`.

Per RESEARCH_AND_PLAN.md §6 the Sprint-0 spike decides whether OpenUBA is used at all; when it is
not, the pipeline uses BaselineUEBA and this adapter stays dormant. It is implemented and tested so
the contract is genuinely interchangeable.
"""
from __future__ import annotations
from typing import Iterator, Optional
from .baseline_model import UebaRecord, _severity


class OpenUBAClient:
    def __init__(self, es_index: str, es_client=None, hosts=None):
        self.es_index = es_index
        self.es = es_client
        self._hosts = hosts
        self._cache: dict[str, UebaRecord] = {}
        self._fetched = False

    def _connect(self):
        if self.es is None and self._hosts:
            from elasticsearch import Elasticsearch  # lazy import
            self.es = Elasticsearch(self._hosts)
        return self.es

    @staticmethod
    def _to_record(src: dict) -> UebaRecord:
        anomaly = float(src.get("anomaly_score", 0.0) or 0.0)
        risk = src.get("risk_score")
        risk = int(risk) if risk is not None else int(round(anomaly * 100))
        severity = src.get("severity") or _severity(risk)
        return UebaRecord(
            entity=src.get("entity") or src.get("host") or src.get("src_ip", ""),
            anomaly_score=anomaly,
            risk_score=risk,
            severity=severity,
            features=src.get("features", {}) or {},
        )

    def fetch(self, window_start: Optional[str] = None,
              window_end: Optional[str] = None) -> Iterator[UebaRecord]:
        """Query OpenUBA's index for the window and yield one UebaRecord per entity."""
        es = self._connect()
        if es is None:
            return
        query: dict = {"match_all": {}}
        if window_start or window_end:
            rng: dict = {}
            if window_start:
                rng["gte"] = window_start
            if window_end:
                rng["lte"] = window_end
            query = {"range": {"window_start": rng}}
        resp = es.search(index=self.es_index, size=10000, query=query)
        for hit in resp.get("hits", {}).get("hits", []):
            rec = self._to_record(hit.get("_source", {}))
            if rec.entity:
                self._cache[rec.entity] = rec
                yield rec
        self._fetched = True

    def score(self, entity: str, feature_vec: dict) -> UebaRecord:
        """Return OpenUBA's record for `entity`, or a benign default if none was produced."""
        if not self._fetched:
            list(self.fetch())
        rec = self._cache.get(entity)
        if rec is not None:
            return rec
        return UebaRecord(entity, 0.0, 0, "info", feature_vec)
