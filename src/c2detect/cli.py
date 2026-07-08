"""Command-line entrypoint: `python -m c2detect.cli run --config config/config.yaml`."""
from __future__ import annotations
import json
import click
from .config import Config
from . import pipeline


@click.group()
def main():
    """c2detect — behavioral DNS/HTTPS C2 detection."""


@main.command()
@click.option("--config", "config_path", required=True, help="Path to config.yaml")
@click.option("--dry-run", is_flag=True, help="Print alerts instead of writing to Elasticsearch")
def run(config_path, dry_run):
    cfg = Config.load(config_path)
    alerts = pipeline.run(cfg)
    if dry_run or not cfg.get("elasticsearch", "hosts"):
        click.echo(json.dumps(alerts, indent=2))
        return
    from .output.elastic import AlertWriter
    es = cfg.get("elasticsearch")
    writer = AlertWriter(
        hosts=es["hosts"], index=es.get("alert_index", "c2-alerts"),
        user=es.get("user"), password=es.get("password"),
        verify_certs=es.get("verify_certs", False),
    )
    writer.ensure_index()
    n = writer.write_many(alerts)
    click.echo(f"wrote {n} alerts to {es.get('alert_index')}")


if __name__ == "__main__":
    main()
