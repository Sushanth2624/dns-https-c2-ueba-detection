#!/usr/bin/env python3
"""Generate benign DNS + HTTPS activity for baselining. Lab-only.
Resolves common domains and makes normal HTTPS requests at human-like irregular intervals.
Run from an ENDPOINT VM (routing through the Analysis VM) during the baseline window.
"""
import random, time, socket, subprocess, sys

DOMAINS = ["google.com", "wikipedia.org", "github.com", "cloudflare.com",
           "ubuntu.com", "microsoft.com", "reddit.com", "stackoverflow.com"]

def main(minutes=60):
    end = time.time() + minutes * 60
    while time.time() < end:
        d = random.choice(DOMAINS)
        try:
            socket.gethostbyname(d)
            subprocess.run(["curl", "-s", "-o", "/dev/null", f"https://{d}"], timeout=10)
        except Exception:
            pass
        time.sleep(random.uniform(5, 45))   # irregular, human-like

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
