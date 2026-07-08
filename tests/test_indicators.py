"""Unit tests for the implemented indicators and the correlation/explain path."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from c2detect.indicators.entropy import shannon_entropy, longest_label_entropy, subscore as ent_sub
from c2detect.indicators.nxdomain import nxdomain_ratio
from c2detect.indicators.beaconing import coefficient_of_variation, subscore as beacon_sub
from c2detect.indicators import dga, ja3ja4, doh, session, length
from c2detect.correlation.engine import correlate
from c2detect.explain.reasoner import build_alert
from c2detect.ueba.baseline_model import UebaRecord


def test_entropy_random_higher_than_word():
    assert shannon_entropy("aaaaaa") < shannon_entropy("x7q2kf9zpl")
    assert longest_label_entropy("a1b2c3d4e5f6.example.com") > longest_label_entropy("www.google.com")


def test_entropy_subscore_bounds():
    s = ent_sub("kd83jfh2ksd9fj2.example.com")
    assert 0.0 <= s <= 1.0


def test_nxdomain_ratio():
    events = [{"rcode_name": "NXDOMAIN"}] * 3 + [{"rcode_name": "NOERROR"}] * 7
    assert abs(nxdomain_ratio(events) - 0.3) < 1e-9


def test_beacon_regular_vs_random():
    regular = [i * 60.0 for i in range(20)]          # every 60s exactly
    assert coefficient_of_variation(regular) < 0.01
    assert beacon_sub(regular) > 0.9
    import random
    random.seed(1)
    noisy = sorted(random.uniform(0, 1200) for _ in range(20))
    assert beacon_sub(noisy) < beacon_sub(regular)


def test_dga_random_vs_word():
    assert dga.subscore("x9k2q7z4m1p8w3.com") > dga.subscore("google.com")
    assert 0.0 <= dga.subscore("wikipedia.org") <= 1.0
    assert dga.subscore("") == 0.0


def test_ja3_rarity_set_and_counts():
    # set semantics: unseen -> 1.0, seen -> 0.0
    assert ja3ja4.rarity_subscore("abc", {"xyz"}) == 1.0
    assert ja3ja4.rarity_subscore("xyz", {"xyz"}) == 0.0
    # counts semantics: common fingerprint is less rare than a one-off
    counts = {"common": 99, "rare": 1}
    assert ja3ja4.rarity_subscore("rare", counts) > ja3ja4.rarity_subscore("common", counts)
    assert ja3ja4.rarity_subscore("", {"x"}) == 0.0


def test_ja3_sni_mismatch():
    assert ja3ja4.sni_mismatch({"ja3": "deadbeef"}) is True
    assert ja3ja4.sni_mismatch({"ja3": "deadbeef", "server_name": "example.com"}) is False


def test_doh_detection():
    assert doh.subscore({"server_name": "cloudflare-dns.com"}) == 1.0
    assert doh.subscore({"server_name": "family.cloudflare-dns.com"}) == 1.0
    assert doh.subscore({"host": "dns.google", "uri": "/dns-query"}) == 1.0
    assert doh.subscore({"server_name": "www.google.com"}) == 0.0


def test_session_shape():
    c2 = {"duration": 600, "orig_bytes": 400, "resp_bytes": 420}   # long, trickle, even
    human = {"duration": 3, "orig_bytes": 800, "resp_bytes": 250000}  # short, download-heavy
    assert session.subscore(c2) > session.subscore(human)
    assert session.subscore({"duration": 0}) == 0.0


def test_query_length():
    long_name = "a" * 40 + ".tunnel.lab"
    assert length.subscore(long_name) > length.subscore("www.google.com")
    assert 0.0 <= length.subscore("deep.sub.domain.example.com") <= 1.0


def _write_tsv(path, fields, rows):
    with open(path, "w") as fh:
        fh.write("#fields\t" + "\t".join(fields) + "\n")
        for r in rows:
            fh.write("\t".join(str(r.get(f, "-")) for f in fields) + "\n")


def test_build_feature_vectors_separates_malicious(tmp_path):
    from c2detect.config import Config
    from c2detect import pipeline

    logdir = tmp_path / "zeek"
    logdir.mkdir()
    # Benign host 10.0.0.2: normal domain, NOERROR. Malicious host 10.0.0.9: DGA + NXDOMAIN burst.
    dns_rows = [{"id.orig_h": "10.0.0.2", "query": "google.com", "rcode_name": "NOERROR", "qtype_name": "A"}]
    dns_rows += [{"id.orig_h": "10.0.0.9", "query": f"x9k2q7z4m1p{i}abcd.com",
                  "rcode_name": "NXDOMAIN", "qtype_name": "A"} for i in range(10)]
    _write_tsv(logdir / "dns.log",
               ["id.orig_h", "query", "rcode_name", "qtype_name"], dns_rows)
    # Malicious beacon: 10.0.0.9 -> 10.0.0.50 every 60s exactly.
    conn_rows = [{"ts": i * 60.0, "id.orig_h": "10.0.0.9", "id.resp_h": "10.0.0.50",
                  "duration": 0.2, "orig_bytes": 40, "resp_bytes": 40} for i in range(12)]
    conn_rows += [{"ts": 5.0, "id.orig_h": "10.0.0.2", "id.resp_h": "1.1.1.1",
                   "duration": 2.0, "orig_bytes": 500, "resp_bytes": 40000}]
    _write_tsv(logdir / "conn.log",
               ["ts", "id.orig_h", "id.resp_h", "duration", "orig_bytes", "resp_bytes"], conn_rows)

    cfg = Config(raw={"paths": {"zeek_log_dir": str(logdir)},
                      "thresholds": {"entropy_high": 3.5, "nxdomain_ratio_high": 0.2,
                                     "beacon_cv_low": 0.10}})
    feats = pipeline.build_feature_vectors(cfg)
    assert set(feats) == {"10.0.0.2", "10.0.0.9"}
    mal, ben = feats["10.0.0.9"], feats["10.0.0.2"]
    assert mal["nxdomain_rate"] > ben["nxdomain_rate"]
    assert mal["dns_entropy"] > ben["dns_entropy"]
    assert mal["beacon_cv"] > 0.9          # exact 60s cadence -> strong beacon
    assert ben["beacon_cv"] == 0.0
    # every feature is a normalized 0..1 sub-score
    for fv in feats.values():
        for v in fv.values():
            assert 0.0 <= v <= 1.0


def test_correlation_and_alert():
    subs = {"dns_entropy": 0.9, "nxdomain_rate": 0.8, "beacon_cv": 0.95, "ja3_rarity": 0.9}
    weights = {"dns_entropy": 0.2, "nxdomain_rate": 0.15, "beacon_cv": 0.25, "ja3_rarity": 0.15}
    corr = correlate("10.0.0.5", ueba_anomaly=0.8, subscores=subs, weights=weights, ueba_weight=0.4)
    assert corr.confidence > 0.7
    assert corr.boost > 0.0  # DGA + beacon boosts should fire
    rec = UebaRecord("10.0.0.5", 0.8, 80, "high", subs)
    mitre = {"dns_entropy": ["T1568.002"], "beacon_cv": ["T1071.001"]}
    alert = build_alert(corr, rec, mitre, min_conf=0.6)
    assert alert["verdict"] in ("suspicious", "likely_c2")
    assert alert["contributing_indicators"]
    assert "T1568.002" in alert["mitre"]
