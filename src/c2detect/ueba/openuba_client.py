"""Adapter connecting OpenUBA as the UEBA engine, behind the fixed UEBA contract.

OpenUBA (GACWR/OpenUBA) is the real UEBA producer: this adapter pushes the parsed per-entity
behavioral feature vectors to OpenUBA, runs an anomaly model (an IsolationForest hosted *inside*
OpenUBA) via its Python SDK, then reads OpenUBA's per-entity anomaly / risk / severity back and maps
them onto `UebaRecord` — the same shape the IsolationForest fallback emits. The rest of the pipeline
(indicators, correlation, explainability, alerts, dashboards) is unchanged and never knows which
producer ran.

Flow (see `.prime()`):
  1. write the feature vectors to a CSV in OpenUBA's shared model-runner volume,
  2. (optionally) train the model on the benign entities so "normal" is baselined,
  3. run inference on all entities — OpenUBA's model-runner container fits/scores and stores results,
  4. read the anomalies back via the SDK and cache one `UebaRecord` per entity.

`.score(entity, features)` then returns the cached record, honoring the BaselineUEBA interface.
Config lives under `ueba.openuba` in config.yaml; switch engines with `ueba.source`.
"""
from __future__ import annotations
import csv
import os
from typing import Iterator, Optional
from .baseline_model import UebaRecord, _severity


class OpenUBAClient:
    def __init__(self, api_url: str = "http://localhost:8000", username: str = "openuba",
                 password: str = "password", model_id: Optional[str] = None,
                 saved_models_dir: str = "/home/analysis/openuba-src/core/storage/saved_models",
                 runner_dir: str = "/opt/openuba/saved_models",
                 train_on_benign: bool = True, es_index: str = "openuba-anomalies",
                 es_client=None, hosts=None):
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        # default to OpenUBA's built-in sklearn IsolationForest model
        self.model_id = model_id or "ffa8ddb1-a6b3-41af-8354-422609c37fb7"
        self.saved_models_dir = saved_models_dir     # host path where we write the CSV
        self.runner_dir = runner_dir                 # path the model-runner sees that dir at
        self.train_on_benign = train_on_benign
        self.es_index = es_index                     # kept for the legacy fetch() path
        self.es = es_client
        self._hosts = hosts
        self._token: Optional[str] = None
        self._cache: dict[str, UebaRecord] = {}
        self._primed = False

    # ---- auth ----
    def _login(self) -> str:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode({"username": self.username, "password": self.password}).encode()
        req = urllib.request.Request(
            f"{self.api_url}/api/v1/auth/login", data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        import json
        with urllib.request.urlopen(req, timeout=30) as r:
            self._token = json.load(r).get("access_token")
        if not self._token:
            raise RuntimeError("OpenUBA login failed (no access_token)")
        return self._token

    def _write_csv(self, path: str, features: dict, keys: list) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["entity_id"] + keys)
            w.writeheader()
            for entity, fv in features.items():
                w.writerow({"entity_id": entity, **{k: round(float(fv.get(k, 0.0)), 6) for k in keys}})

    # ---- the integration ----
    def prime(self, features: dict, benign_entities: Optional[set] = None,
              feature_keys: Optional[list] = None) -> None:
        """Push feature vectors to OpenUBA, run its model, and cache the per-entity scores."""
        if not features:
            self._primed = True
            return
        import openuba
        self._login()
        openuba.configure(api_url=self.api_url, token=self._token)
        keys = feature_keys or sorted(next(iter(features.values())).keys())

        all_csv = "c2_features.csv"
        self._write_csv(os.path.join(self.saved_models_dir, all_csv), features, keys)

        # 1) optionally baseline the model on benign entities (learn "normal")
        if self.train_on_benign and benign_entities:
            benign = {e: v for e, v in features.items() if e in benign_entities}
            if benign:
                self._write_csv(os.path.join(self.saved_models_dir, "c2_benign.csv"), benign, keys)
                try:
                    tjob = openuba.start_training(model_id=self.model_id, wait=False, input_data={
                        "data_source": "local_csv", "file_path": self.runner_dir,
                        "file_name": "c2_benign.csv"})
                    self._wait_job(tjob.get("id"))   # wait=False + own poller (SDK hang, see below)
                except Exception:
                    pass  # fall back to fit-on-infer if training path is unavailable

        # 2) run inference on all entities.  NOTE: we submit with wait=False and poll the job
        #    ourselves.  The SDK's wait_for_job() only treats {"completed","failed","error"} as
        #    terminal, but the backend reports success as "succeeded" -> its wait loop would hang
        #    until timeout.  Polling here also lets us read results straight from the job record.
        job = openuba.start_inference(model_id=self.model_id, wait=False, input_data={
            "data_source": "local_csv", "file_path": self.runner_dir, "file_name": all_csv})
        job = self._wait_job(job.get("id"))

        # 3) read OpenUBA's per-entity anomalies -> UebaRecord.  An *untrained* (fit-on-infer) run
        #    returns them inline in metrics.anomalies; a *trained* run persists them to the
        #    anomalies store instead (metrics carries only anomalies_created), so we read the store.
        anomalies = ((job.get("metrics") or {}).get("anomalies")) or []
        if not anomalies:
            anomalies = self._query_anomalies_store(limit=1000)
        raw_risk: dict[str, float] = {}
        for a in anomalies:
            e = a.get("entity_id") or a.get("entity")
            if not e or e not in features or e in raw_risk:
                continue          # keep the first record per entity
            raw_risk[e] = float(a.get("risk_score", a.get("risk", 0.0)) or 0.0)

        # Calibrate OpenUBA's native risk into the contract's 0..1 anomaly by normalizing against
        # the benign peer cohort -- the same one-sided z-score the IsolationForest baseline uses.
        # OpenUBA still produces the anomaly signal (isolation risk); this only maps it onto the
        # scale the correlation layer expects.  Raw risk/100 alone compresses every host into a
        # narrow band (~0.16-0.51) so the UEBA term can't lift subtle beacon/DoH-only attackers.
        anomaly_by_entity = self._calibrate(raw_risk, benign_entities)
        for e, risk in raw_risk.items():
            anomaly = anomaly_by_entity[e]
            ri = int(round(anomaly * 100))
            self._cache[e] = UebaRecord(e, anomaly, ri, _severity(ri), features[e])
        self._primed = True

    def _query_anomalies_store(self, limit: int = 1000) -> list:
        """Read persisted anomalies from OpenUBA's REST store, newest first, filtered to our model.
        (The bundled SDK hardcodes limit=5000, which the API rejects with 422 -- cap is 1000.)"""
        import json as _json
        import urllib.parse
        import urllib.request
        params = urllib.parse.urlencode({"model_id": self.model_id, "limit": min(int(limit), 1000)})
        req = urllib.request.Request(
            f"{self.api_url}/api/v1/anomalies?{params}",
            headers={"Authorization": f"Bearer {self._token}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.load(r)
        return data if isinstance(data, list) else data.get("items", data.get("anomalies", []))

    @staticmethod
    def _calibrate(raw_risk: dict, benign_entities: Optional[set]) -> dict:
        """Map OpenUBA's native risk scores to 0..1 anomalies via a one-sided z-score against a
        'normal' reference cohort (labelled benign if known, else a robust median/MAD over all
        hosts for the unsupervised production path).  6-sigma saturates to 1.0 -- mirrors
        BaselineUEBA._zscore_anomaly so the two engines are directly comparable."""
        if not raw_risk:
            return {}
        vals = list(raw_risk.values())
        ref = [raw_risk[e] for e in raw_risk if benign_entities and e in benign_entities]
        if ref:
            center = sum(ref) / len(ref)
            var = sum((v - center) ** 2 for v in ref) / len(ref)
            scale = max(var ** 0.5, 0.5)          # std of benign risk, floored off zero
        else:
            s = sorted(vals)                       # unsupervised: robust center/spread over all hosts
            center = s[len(s) // 2]
            mad = sorted(abs(v - center) for v in vals)[len(vals) // 2]
            scale = max(1.4826 * mad, 0.5)
        out = {}
        for e, v in raw_risk.items():
            pos_z = max(0.0, (v - center) / scale)
            out[e] = min(1.0, pos_z / 6.0)
        return out

    def _wait_job(self, job_id: Optional[str], poll: float = 2.0, timeout: float = 900.0) -> dict:
        """Poll /api/v1/jobs/{id} until the job reaches a terminal state, then return it.

        Accepts "succeeded" as a success state (the backend's actual terminal value), which the
        bundled SDK's wait_for_job() does not — see the note in prime()."""
        import json as _json
        import time as _time
        import urllib.request
        if not job_id:
            raise RuntimeError("OpenUBA inference did not return a job id")
        terminal = {"succeeded", "completed", "failed", "error"}
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            req = urllib.request.Request(
                f"{self.api_url}/api/v1/jobs/{job_id}",
                headers={"Authorization": f"Bearer {self._token}"})
            with urllib.request.urlopen(req, timeout=30) as r:
                job = _json.load(r)
            status = (job.get("status") or "").lower()
            if status in terminal:
                if status in ("failed", "error"):
                    raise RuntimeError(f"OpenUBA inference job {job_id} {status}: {job.get('metrics')}")
                return job
            _time.sleep(poll)
        raise TimeoutError(f"OpenUBA inference job {job_id} did not finish within {timeout:.0f}s")

    # ---- contract ----
    def score(self, entity: str, feature_vec: dict) -> UebaRecord:
        """Return OpenUBA's cached record for `entity` (call prime() first for the batch)."""
        rec = self._cache.get(entity)
        if rec is not None:
            return rec
        return UebaRecord(entity, 0.0, 0, "info", feature_vec)

    # ---- legacy: read pre-computed OpenUBA results from an Elasticsearch index ----
    def _connect(self):
        if self.es is None and self._hosts:
            from elasticsearch import Elasticsearch
            self.es = Elasticsearch(self._hosts)
        return self.es

    def fetch(self, window_start: Optional[str] = None,
              window_end: Optional[str] = None) -> Iterator[UebaRecord]:
        es = self._connect()
        if es is None:
            return
        resp = es.search(index=self.es_index, size=10000, query={"match_all": {}})
        for hit in resp.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            e = src.get("entity") or src.get("entity_id")
            if not e:
                continue
            risk = int(src.get("risk_score", 0) or 0)
            rec = UebaRecord(e, float(src.get("anomaly_score", risk / 100.0) or 0.0), risk,
                             src.get("severity") or _severity(risk), src.get("features", {}) or {})
            self._cache[e] = rec
            yield rec
