#!/usr/bin/env python3
"""Beaconing C2 simulator (lab-only). Contacts a controller at a fixed interval with small jitter,
producing the low-CV timing fingerprint the beaconing indicator detects.
Usage: beacon_sim.py <controller_ip> <interval_sec> <jitter_frac> <count>
"""
import sys, time, random, socket

def main(host, interval=60.0, jitter=0.05, count=30, port=443):
    for _ in range(count):
        try:
            s = socket.create_connection((host, port), timeout=5)
            s.sendall(b"ping")     # tiny consistent payload
            s.close()
        except Exception:
            pass
        time.sleep(interval * (1 + random.uniform(-jitter, jitter)))

if __name__ == "__main__":
    a = sys.argv
    main(a[1], float(a[2]) if len(a) > 2 else 60.0,
         float(a[3]) if len(a) > 3 else 0.05,
         int(a[4]) if len(a) > 4 else 30)
