"""Write explainable alerts to Elasticsearch. Import guarded so the pipeline can run offline
(e.g. during unit tests) without a live ES.
"""
from __future__ import annotations
from typing import Iterable, Mapping


class AlertWriter:
    def __init__(self, hosts, index: str, user=None, password=None, verify_certs=False):
        from elasticsearch import Elasticsearch  # lazy import
        kwargs = {"verify_certs": verify_certs}
        if not verify_certs:
            kwargs["ssl_show_warn"] = False           # quiet self-signed-lab TLS warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        if user and password:
            kwargs["basic_auth"] = (user, password)
        self.es = Elasticsearch(hosts, **kwargs)
        self.index = index

    #: Explicit mapping so Kibana can aggregate on keyword fields without .keyword suffixes.
    MAPPING = {
        "properties": {
            "@timestamp": {"type": "date"},
            "alert_id": {"type": "keyword"},
            "entity": {"type": "keyword"},
            "verdict": {"type": "keyword"},
            "confidence": {"type": "float"},
            "severity": {"type": "keyword"},
            "mitre": {"type": "keyword"},
            "recommended_actions": {"type": "text"},
            "ueba": {"properties": {"anomaly_score": {"type": "float"},
                                    "risk_score": {"type": "integer"}}},
            "score_breakdown": {"properties": {"ueba_component": {"type": "float"},
                                               "indicator_component": {"type": "float"},
                                               "boost": {"type": "float"}}},
            "contributing_indicators": {"type": "nested", "properties": {
                "name": {"type": "keyword"}, "value": {"type": "float"},
                "why": {"type": "text"}}},
        }
    }

    def ensure_index(self) -> None:
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index, mappings=self.MAPPING)

    def write(self, alert: Mapping) -> None:
        self.es.index(index=self.index, id=alert.get("alert_id"), document=alert)

    def write_many(self, alerts: Iterable[Mapping]) -> int:
        n = 0
        for a in alerts:
            self.write(a)
            n += 1
        return n
