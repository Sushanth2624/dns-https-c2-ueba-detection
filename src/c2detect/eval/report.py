"""Render evaluation results as a markdown report + comparison charts (matplotlib, headless)."""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _bar(ax, labels, values, title, ylabel, color):
    ax.bar(labels, values, color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 1.05)
    for i, v in enumerate(values):
        ax.text(i, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=8)


def write_charts(results: dict, out_dir: str | Path) -> list[str]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    a = results["config_A_signature"]
    b = results["config_B_best"]
    c = results["config_C_multi_ueba"]
    configs = ["A: signature", f"B: best ({b['indicator']})", "C: multi+UEBA"]
    written = []

    # A/B/C precision-recall-F1-FPR grouped
    fig, axes = plt.subplots(1, 4, figsize=(15, 4))
    for ax, metric in zip(axes, ["precision", "recall", "f1", "fpr"]):
        vals = [a[metric], b[metric], c[metric]]
        colors = ["#b3b3b3", "#6fa8dc", "#e06666" if metric == "fpr" else "#93c47d"]
        _bar(ax, ["A", "B", "C"], vals, metric.upper(), metric, colors)
    fig.suptitle("Config A (signature) vs B (best single indicator) vs C (multi-indicator + UEBA)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    p = out_dir / "abc_comparison.png"
    fig.savefig(p, dpi=110); plt.close(fig)
    written.append(str(p))

    # per-single-indicator F1
    b_all = results["config_B_single"]
    inds = list(b_all.keys())
    f1s = [b_all[k]["f1"] for k in inds]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(inds, f1s, color="#6fa8dc")
    ax.axhline(c["f1"], color="#e06666", linestyle="--", label=f"C (multi+UEBA) F1={c['f1']:.2f}")
    ax.set_title("Single-indicator F1 vs full pipeline")
    ax.set_ylabel("F1"); ax.set_ylim(0, 1.05); ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    p = out_dir / "single_indicator_f1.png"
    fig.savefig(p, dpi=110); plt.close(fig)
    written.append(str(p))
    return written


def write_markdown(results: dict, out_path: str | Path) -> str:
    a = results["config_A_signature"]
    bb = results["config_B_best"]
    c = results["config_C_multi_ueba"]

    def row(name, m):
        return (f"| {name} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} "
                f"| {m['fpr']:.2f} | {m['tp']} | {m['fp']} | {m['fn']} | {m['tn']} |")

    lines = [
        "# Evaluation results — A/B/C comparison",
        "",
        f"Entities: **{results['n_entities']}** "
        f"({results['n_benign']} benign, {results['n_attacks']} attack). "
        "Single-host lab corpus; ground truth per entity.",
        "",
        "## Headline comparison",
        "",
        "| Config | Precision | Recall | F1 | FPR | TP | FP | FN | TN |",
        "|---|---|---|---|---|---|---|---|---|",
        row("A — signature-only (Suricata)", a),
        row(f"B — best single indicator ({bb['indicator']})", bb),
        row("C — multi-indicator + UEBA (this project)", c),
        "",
        f"**Result:** F1  C={c['f1']:.2f}  vs  B={bb['f1']:.2f}  vs  A={a['f1']:.2f}. "
        f"False-positive rate  C={c['fpr']:.2f}  vs  B={bb['fpr']:.2f}  vs  A={a['fpr']:.2f}.",
        "",
        "## Every single indicator (Config B)",
        "",
        "| Indicator | Precision | Recall | F1 | FPR |",
        "|---|---|---|---|---|",
    ]
    for k, m in results["config_B_single"].items():
        lines.append(f"| {k} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} | {m['fpr']:.2f} |")

    lines += ["", "## Detection latency (Config C, per attack entity)", "",
              "| Attack entity | Attack type | Latency to first alert (s) |",
              "|---|---|---|"]
    gt = results["ground_truth"]
    atypes = results.get("attack_type", {})
    for e, lat in results["detection_latency_sec"].items():
        lines.append(f"| {e} | {atypes.get(e, '')} | {lat if lat is not None else 'n/a'} |")

    lines += ["", "## Per-entity confidence (Config C)", "",
              "| Entity | Truth | UEBA anomaly | Confidence | Predicted |",
              "|---|---|---|---|---|"]
    for e in sorted(results["C_confidence"]):
        lines.append(f"| {e} | {gt.get(e)} | {results['ueba_anomaly'].get(e)} "
                     f"| {results['C_confidence'][e]} | {results['C_predictions'][e]} |")

    text = "\n".join(lines) + "\n"
    Path(out_path).write_text(text)
    return text
