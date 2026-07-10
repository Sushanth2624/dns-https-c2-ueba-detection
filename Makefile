.PHONY: setup test run dataset evaluate dashboards demo health lab-up lab-capture evaluate-lab lab-demo lab-down
PY?=./.venv/bin/python
setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
test:
	PYTHONPATH=src ./.venv/bin/pytest -q
run:
	PYTHONPATH=src $(PY) -m c2detect.cli run --config config/config.yaml
dataset:
	bash scripts/build_dataset.sh
evaluate:
	PYTHONPATH=src $(PY) -m c2detect.cli evaluate --config config/config.yaml --out data/eval
ingest:
	PYTHONPATH=src $(PY) scripts/ingest_es.py
dashboards:
	$(PY) scripts/build_dashboards.py
health:
	bash scripts/healthcheck.sh

# ---- Container lab: real multi-host inline capture (distinct source IPs) ----
lab-up:
	bash scripts/lab_up.sh
lab-capture:
	bash scripts/lab_capture.sh
evaluate-lab:
	PYTHONPATH=src $(PY) -m c2detect.cli evaluate-lab --config config/config.lab.yaml --out data/eval/lab

# Full lab demo: create hosts -> inline capture -> A/B/C -> alerts+telemetry to ES -> dashboards
lab-demo: lab-up lab-capture evaluate-lab
	-. config/secrets.env; curl -s -k -u elastic:$$ELASTIC_PASSWORD -X DELETE "https://localhost:9200/c2-alerts" >/dev/null
	PYTHONPATH=src $(PY) -m c2detect.cli run --config config/config.lab.yaml
	PYTHONPATH=src $(PY) scripts/ingest_es.py --lab data/captures/lab --config config/config.lab.yaml
	$(PY) scripts/build_dashboards.py
	@echo "Kibana: https://localhost:5601/app/dashboards -> 'C2 — Telemetry & Scores'"
lab-down:
	-docker rm -f ep-benign1 ep-benign2 ep-benign3 ep-dga ep-tunnel ep-beacon ep-doh 2>/dev/null
	-pkill -f 's_server.*8443'; pkill -f 'dnsmasq.*10.50.0.1'

# Single-host demo (no Docker): capture on host NIC -> evaluate -> ES -> dashboards
demo: dataset evaluate
	-. config/secrets.env; curl -s -k -u elastic:$$ELASTIC_PASSWORD -X DELETE "https://localhost:9200/c2-alerts" >/dev/null
	PYTHONPATH=src $(PY) -m c2detect.cli run --config config/config.demo.yaml
	$(PY) scripts/build_dashboards.py
	@echo "Kibana: https://localhost:5601/app/dashboards -> 'DNS/HTTPS C2 — Behavioral Detection'"
