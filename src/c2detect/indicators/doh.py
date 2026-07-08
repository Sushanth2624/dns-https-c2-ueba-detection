"""DNS-over-HTTPS detection.
Match SNI/IP against known DoH resolvers and HTTPS requests to /dns-query; flag hosts whose port-53
DNS dropped while DoH rose. Maintain a resolver list in config/data.
Data source: Zeek ssl.log / http.log; Suricata tls/http.
"""
from __future__ import annotations
from typing import Mapping, Set

# Seed list of well-known public DoH resolvers (SNI / Host header).
KNOWN_DOH_HOSTS: Set[str] = {
    "dns.google", "cloudflare-dns.com", "mozilla.cloudflare-dns.com",
    "dns.quad9.net", "doh.opendns.com", "chrome.cloudflare-dns.com",
    "dns.nextdns.io", "doh.cleanbrowsing.org", "dns.adguard.com",
    "one.one.one.one",
}


def _host_is_doh(host: str) -> bool:
    host = (host or "").lower().strip(".")
    if not host:
        return False
    if host in KNOWN_DOH_HOSTS:
        return True
    # subdomain of a known resolver (e.g. family.cloudflare-dns.com)
    return any(host == h or host.endswith("." + h) for h in KNOWN_DOH_HOSTS)


def subscore(tls_event: Mapping) -> float:
    """1.0 if the flow is DoH to a known resolver / a /dns-query endpoint, else 0.0.

    Accepts a Zeek ssl.log record (server_name), a Zeek http.log record (host/uri), or a
    normalized Suricata tls/http event.
    """
    sni = tls_event.get("server_name") or tls_event.get("sni") or ""
    host = tls_event.get("host") or ""
    if _host_is_doh(sni) or _host_is_doh(host):
        return 1.0
    uri = str(tls_event.get("uri") or "").lower()
    if "/dns-query" in uri or "dns=" in uri:
        return 1.0
    ct = str(tls_event.get("content_type") or tls_event.get("resp_mime_types") or "").lower()
    if "application/dns-message" in ct:
        return 1.0
    return 0.0
