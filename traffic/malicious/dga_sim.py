#!/usr/bin/env python3
"""DGA simulator (lab-only). Generates high-entropy pseudo-random domains and resolves them,
producing NXDOMAIN bursts + high-entropy queries for the entropy/NXDOMAIN indicators.
Usage: dga_sim.py <count> [tld]
"""
import sys, random, string, socket

def gen_domain(tld="com", length=16):
    label = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
    return f"{label}.{tld}"

def main(count=200, tld="com"):
    random.seed()
    for _ in range(count):
        d = gen_domain(tld)
        try:
            socket.gethostbyname(d)   # almost always NXDOMAIN
        except Exception:
            pass

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200,
         sys.argv[2] if len(sys.argv) > 2 else "com")
