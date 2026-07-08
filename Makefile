.PHONY: setup test run lint
setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
test:
	PYTHONPATH=src pytest -q
run:
	PYTHONPATH=src python -m c2detect.cli run --config config/config.yaml
health:
	bash scripts/healthcheck.sh
