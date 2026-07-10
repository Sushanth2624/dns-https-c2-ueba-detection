#!/usr/bin/env python3
"""Screenshot an authenticated Kibana dashboard via the DevTools Protocol.

Logs in through the Kibana API to get a session cookie, injects it into a headless Chrome, then
captures a full-page PNG. Usage: kbn_shot.py <dashboard_id> <out.png>
"""
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pychrome

KBN = "https://localhost:5601"
_SSL = ssl._create_unverified_context()


def elastic_pw():
    pw = os.environ.get("ELASTIC_PASSWORD")
    if not pw:
        for line in (Path(__file__).resolve().parent.parent / "config" / "secrets.env").read_text().splitlines():
            if line.startswith("ELASTIC_PASSWORD="):
                pw = line.split("=", 1)[1].strip()
    return pw


def login_cookie():
    body = json.dumps({"providerType": "basic", "providerName": "basic",
                       "currentURL": f"{KBN}/login",
                       "params": {"username": "elastic", "password": elastic_pw()}}).encode()
    req = urllib.request.Request(f"{KBN}/internal/security/login", data=body, method="POST",
        headers={"kbn-xsrf": "true", "Content-Type": "application/json",
                 "x-elastic-internal-origin": "kibana"})
    with urllib.request.urlopen(req, context=_SSL) as r:
        for h, v in r.getheaders():
            if h.lower() == "set-cookie" and v.startswith("sid="):
                return v.split(";")[0].split("=", 1)[1]
    raise SystemExit("login failed")


def main():
    dash_id, out = sys.argv[1], sys.argv[2]
    sid = login_cookie()
    chrome = subprocess.Popen(
        ["google-chrome", "--headless=new", "--no-sandbox", "--ignore-certificate-errors",
         "--remote-debugging-port=9333", "--hide-scrollbars", "--window-size=1650,1500"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(3)
        browser = pychrome.Browser(url="http://127.0.0.1:9333")
        tab = browser.new_tab()
        tab.start()
        tab.call_method("Network.enable")
        tab.call_method("Network.setCookie", name="sid", value=sid, domain="localhost",
                        path="/", httpOnly=True, secure=True)
        tab.call_method("Page.enable")
        url = (f"{KBN}/app/dashboards#/view/{dash_id}"
               "?_g=(time:(from:'now-30h',to:'now%2B1h'))")
        tab.call_method("Page.navigate", url=url)
        time.sleep(38)  # let the SPA + all panels render
        res = tab.call_method("Page.captureScreenshot", captureBeyondViewport=True,
                              format="png")
        import base64
        Path(out).write_bytes(base64.b64decode(res["data"]))
        tab.stop()
        browser.close_tab(tab)
        print(f"wrote {out} ({Path(out).stat().st_size} bytes)")
    finally:
        chrome.terminate()


if __name__ == "__main__":
    main()
