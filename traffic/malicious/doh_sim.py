#!/usr/bin/env python3
"""DoH-based C2 simulator (lab-only).

Sends DNS queries over HTTPS (RFC 8484) to a DoH resolver's /dns-query endpoint at beacon-like
intervals, so DNS 'disappears' from port 53 while HTTPS to a DoH host rises. This produces TLS to a
known DoH SNI plus a regular call-home cadence — exactly what the doh_endpoint + beacon_cv
indicators detect. Uses only the stdlib (urllib), no external deps.

Usage: doh_sim.py [doh_url] [interval_sec] [count] [jitter_frac]
  doh_url      default https://cloudflare-dns.com/dns-query
  interval_sec seconds between beacons (default 60)
  count        number of beacons (default 20)
  jitter_frac  timing jitter fraction (default 0.05)
"""
import base64
import random
import struct
import sys
import time
import urllib.request

DEFAULT_URL = "https://cloudflare-dns.com/dns-query"
BEACON_NAMES = ["update.lab", "cdn.lab", "sync.lab", "telemetry.lab"]


def build_dns_query(qname: str, qtype: int = 1) -> bytes:
    """Minimal DNS wire-format query (RD set), type A by default."""
    header = struct.pack(">HHHHHH", 0x0000, 0x0100, 1, 0, 0, 0)  # id=0, flags=RD, qd=1
    q = b"".join(bytes([len(p)]) + p.encode() for p in qname.split(".") if p) + b"\x00"
    q += struct.pack(">HH", qtype, 1)  # QTYPE, QCLASS=IN
    return header + q


def doh_get(url: str, wire: bytes, timeout: float = 10.0) -> int:
    dns_param = base64.urlsafe_b64encode(wire).decode().rstrip("=")
    req = urllib.request.Request(
        f"{url}?dns={dns_param}",
        headers={"Accept": "application/dns-message", "User-Agent": "c2lab-doh-sim/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        resp.read()
        return resp.status


def main(url=DEFAULT_URL, interval=60.0, count=20, jitter=0.05):
    interval, count, jitter = float(interval), int(count), float(jitter)
    ok = 0
    for i in range(count):
        name = random.choice(BEACON_NAMES)
        try:
            doh_get(url, build_dns_query(name))
            ok += 1
        except Exception as e:
            print(f"doh_sim: beacon {i} failed: {e}", file=sys.stderr)
        time.sleep(interval * (1 + random.uniform(-jitter, jitter)))
    print(f"doh_sim: {ok}/{count} DoH beacons to {url}")


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else DEFAULT_URL,
         a[2] if len(a) > 2 else 60.0,
         a[3] if len(a) > 3 else 20,
         a[4] if len(a) > 4 else 0.05)
