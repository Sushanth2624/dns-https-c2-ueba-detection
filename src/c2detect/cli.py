"""Command-line entrypoint: `python -m c2detect.cli run --config config/config.yaml`."""
from __future__ import annotations
import json
import os
import click
from .config import Config
from . import pipeline


def _elastic_password():
    """ELASTIC_PASSWORD from env, else parsed from config/secrets.env (gitignored)."""
    pw = os.environ.get("ELASTIC_PASSWORD")
    if pw:
        return pw
    from pathlib import Path
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        sec = base / "config" / "secrets.env"
        if sec.exists():
            for line in sec.read_text().splitlines():
                if line.startswith("ELASTIC_PASSWORD="):
                    return line.split("=", 1)[1].strip()
    return None


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
    # password precedence: config value, else ELASTIC_PASSWORD env / config/secrets.env
    password = es.get("password") or _elastic_password()
    writer = AlertWriter(
        hosts=es["hosts"], index=es.get("alert_index", "c2-alerts"),
        user=es.get("user"), password=password,
        verify_certs=es.get("verify_certs", False),
    )
    writer.ensure_index()
    n = writer.write_many(alerts)
    click.echo(f"wrote {n} alerts to {es.get('alert_index')}")


@main.command()
@click.option("--captures", default="data/captures", help="Dir of per-scenario captures")
@click.option("--out", "out_dir", default="data/eval/corpus", help="Corpus output dir")
def corpus(captures, out_dir):
    """Build the labeled multi-entity evaluation corpus from single-host captures."""
    from .eval.corpus import build_corpus
    summary = build_corpus(captures, out_dir)
    click.echo(json.dumps(summary, indent=2))


@main.command("evaluate-lab")
@click.option("--config", "config_path", required=True, help="Path to config.yaml")
@click.option("--lab", "lab_dir", default="data/captures/lab", help="Container-lab capture dir")
@click.option("--out", "out_dir", default="data/eval/lab", help="Results output dir")
def evaluate_lab_cmd(config_path, lab_dir, out_dir):
    """A/B/C evaluation over the real container-lab inline capture (distinct source IPs)."""
    from pathlib import Path
    from .eval.lab import evaluate_lab
    from .eval import report as report_mod
    cfg = Config.load(config_path)
    model_path = cfg.get("ueba", "baseline", "model_path", default="models/isoforest.joblib")
    results = evaluate_lab(lab_dir, cfg, model_path=model_path)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2))
    report_mod.write_markdown(results, out / "report.md")
    report_mod.write_charts(results, out / "charts")
    a = results["config_A_signature"]; b = results["config_B_best"]; c = results["config_C_multi_ueba"]
    click.echo(f"{results['n_entities']} real hosts ({results['n_benign']} benign, "
               f"{results['n_attacks']} attack)")
    click.echo(f"F1  A={a['f1']:.2f}  B={b['f1']:.2f} ({b['indicator']})  C={c['f1']:.2f}")
    click.echo(f"FPR A={a['fpr']:.2f}  B={b['fpr']:.2f}  C={c['fpr']:.2f}")


@main.command()
@click.option("--config", "config_path", required=True, help="Path to config.yaml")
@click.option("--captures", default="data/captures", help="Dir of per-scenario captures")
@click.option("--corpus", "corpus_dir", default="data/eval/corpus", help="Corpus dir")
@click.option("--out", "out_dir", default="data/eval", help="Results output dir")
@click.option("--rebuild/--no-rebuild", default=True, help="Rebuild corpus before evaluating")
def evaluate(config_path, captures, corpus_dir, out_dir, rebuild):
    """Run the A/B/C comparison and write results.json, report.md, and charts."""
    from pathlib import Path
    from .eval.corpus import build_corpus
    from .eval.evaluate import evaluate as run_eval
    from .eval import report as report_mod

    cfg = Config.load(config_path)
    if rebuild:
        build_corpus(captures, corpus_dir)
    model_path = cfg.get("ueba", "baseline", "model_path", default="models/isoforest.joblib")
    results = run_eval(captures, corpus_dir, cfg, model_path=model_path)

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2))
    report_mod.write_markdown(results, out / "report.md")
    charts = report_mod.write_charts(results, out / "charts")
    a = results["config_A_signature"]; b = results["config_B_best"]; c = results["config_C_multi_ueba"]
    click.echo(f"F1  A={a['f1']:.2f}  B={b['f1']:.2f} ({b['indicator']})  C={c['f1']:.2f}")
    click.echo(f"FPR A={a['fpr']:.2f}  B={b['fpr']:.2f}  C={c['fpr']:.2f}")
    click.echo(f"wrote {out/'results.json'}, {out/'report.md'}, {', '.join(charts)}")


if __name__ == "__main__":
    main()
