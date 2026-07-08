.PHONY: setup test run dataset evaluate dashboards demo health
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
# One-path reproducible demo: capture -> evaluate (A/B/C) -> alerts to ES -> dashboards
demo: dataset evaluate
	-curl -s -X DELETE "http://localhost:9200/c2-alerts" >/dev/null
	PYTHONPATH=src $(PY) -m c2detect.cli run --config config/config.demo.yaml
	$(PY) scripts/build_dashboards.py
	@echo "Open Kibana: http://localhost:5601/app/dashboards -> 'DNS/HTTPS C2 — Behavioral Detection'"
health:
	bash scripts/healthcheck.sh
