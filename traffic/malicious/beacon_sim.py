#!/usr/bin/env python3
"""Beaconing C2 simulator (lab-only). Contacts a controller at a fixed interval with small jitter,
producing the low-CV timing fingerprint the beaconing indicator detects. Performs a real TLS
handshake (with SNI) so Zeek/Suricata log a consistent client JA3 fingerprint for the implant —
distinct from a browser/curl baseline, which drives the ja3_rarity indicator.

Usage: beacon_sim.py <controller_host> <interval_sec> <jitter_frac> <count> [sni] [port]
"""
import sys, time, random, socket, ssl

def beacon_once(host, port, sni, timeout=5.0):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    raw = socket.create_connection((host, port), timeout=timeout)
    try:
        tls = ctx.wrap_socket(raw, server_hostname=sni or host)  # real ClientHello -> JA3
        try:
            tls.sendall(b"PING")   # tiny consistent payload
        except Exception:
            pass
        tls.close()
    finally:
        try:
            raw.close()
        except Exception:
            pass

def main(host, interval=60.0, jitter=0.05, count=30, sni=None, port=443):
    ok = 0
    for _ in range(count):
        try:
            beacon_once(host, port, sni)
            ok += 1
        except Exception:
            pass
        time.sleep(interval * (1 + random.uniform(-jitter, jitter)))
    print(f"beacon_sim: {ok}/{count} beacons to {host}:{port} (sni={sni or host})")

if __name__ == "__main__":
    a = sys.argv
    main(a[1],
         float(a[2]) if len(a) > 2 else 60.0,
         float(a[3]) if len(a) > 3 else 0.05,
         int(a[4]) if len(a) > 4 else 30,
         a[5] if len(a) > 5 else None,
         int(a[6]) if len(a) > 6 else 443)
