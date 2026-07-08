#!/usr/bin/env python3
"""Generate benign DNS + HTTPS activity for baselining. Lab-only.
Resolves common domains and makes normal HTTPS requests (via curl, so the client JA3 matches a
real browser/tool baseline rather than the Python-based attack sims) at human-like irregular
intervals to varied destinations — so no single (src->dst) pair looks like a regular beacon.

Usage:
  generate_benign.py --minutes 60                 # time-bounded (baseline window)
  generate_benign.py --count 40 --min-sleep 0.2 --max-sleep 1.5   # count-bounded (compressed lab)
"""
import argparse, random, time, socket, subprocess

DOMAINS = ["google.com", "wikipedia.org", "github.com", "cloudflare.com",
           "ubuntu.com", "microsoft.com", "reddit.com", "stackoverflow.com",
           "python.org", "debian.org", "mozilla.org", "kernel.org",
           "wikipedia.org", "apache.org", "nginx.org", "gnu.org"]


def one_request(min_sleep, max_sleep):
    d = random.choice(DOMAINS)
    try:
        socket.gethostbyname(d)
        subprocess.run(["curl", "-s", "-o", "/dev/null", "--max-time", "8", f"https://{d}/"],
                       timeout=10)
    except Exception:
        pass
    time.sleep(random.uniform(min_sleep, max_sleep))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=None)
    ap.add_argument("--count", type=int, default=None)
    ap.add_argument("--min-sleep", type=float, default=5.0)
    ap.add_argument("--max-sleep", type=float, default=45.0)
    args = ap.parse_args()

    n = 0
    if args.count is not None:
        for _ in range(args.count):
            one_request(args.min_sleep, args.max_sleep)
            n += 1
    else:
        minutes = args.minutes if args.minutes is not None else 60
        end = time.time() + minutes * 60
        while time.time() < end:
            one_request(args.min_sleep, args.max_sleep)
            n += 1
    print(f"generate_benign: {n} benign requests across {len(set(DOMAINS))} domains")


if __name__ == "__main__":
    main()
