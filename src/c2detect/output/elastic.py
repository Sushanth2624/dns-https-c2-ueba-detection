"""Write explainable alerts to Elasticsearch. Import guarded so the pipeline can run offline
(e.g. during unit tests) without a live ES.
"""
from __future__ import annotations
from typing import Iterable, Mapping


class AlertWriter:
    def __init__(self, hosts, index: str, user=None, password=None, verify_certs=False):
        from elasticsearch import Elasticsearch  # lazy import
        kwargs = {"verify_certs": verify_certs}
        if user and password:
            kwargs["basic_auth"] = (user, password)
        self.es = Elasticsearch(hosts, **kwargs)
        self.index = index

    def ensure_index(self) -> None:
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index)

    def write(self, alert: Mapping) -> None:
        self.es.index(index=self.index, id=alert.get("alert_id"), document=alert)

    def write_many(self, alerts: Iterable[Mapping]) -> int:
        n = 0
        for a in alerts:
            self.write(a)
            n += 1
        return n
