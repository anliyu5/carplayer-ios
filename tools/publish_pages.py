#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/ 下的分发件上传到仓库并开启 GitHub Pages（https 静态站点，itms-services 需要 https）。"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER, REPO = "anliyu5", "carplayer-ios"
TOKEN = os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"

FILES = [
    "docs/index.html",
    "docs/install.html",
    "docs/manifest.plist",
    "docs/altstore-source.json",
    "docs/AppIcon.png",
    "docs/CarPlayer.mobileconfig",
    "docs/CarPlayer-1.9.14-unsigned.ipa",
    "docs/CarPlayer-iOS-1.9.14-src.zip",
    "docs/README.md",
    "docs/iOS适配说明.md",
    "docs/INSTALL.md",
]


def call(method, path, payload=None, expect=(200, 201, 204)):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "carplayer-pages",
    })
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if e.code in expect:
            return e.code, {}
        raise SystemExit(f"{method} {path} -> {e.code}: {body[:300]}")


def upload(repo_path, message):
    quoted = urllib.parse.quote(repo_path)
    local = os.path.join(ROOT, repo_path)
    if not os.path.exists(local):
        print(f"  skip (missing) {repo_path}")
        return
    content = base64.b64encode(open(local, "rb").read()).decode()
    sha = None
    try:
        _, cur = call("GET", f"/repos/{OWNER}/{REPO}/contents/{quoted}")
        sha = cur.get("sha")
    except SystemExit:
        sha = None
    payload = {"message": message, "content": content, "branch": "main"}
    if sha:
        payload["sha"] = sha
    call("PUT", f"/repos/{OWNER}/{REPO}/contents/{quoted}", payload)
    print(f"  ok {repo_path} ({os.path.getsize(local)/1024:.1f} KB)")


def main():
    if not TOKEN:
        raise SystemExit("缺 GH_TOKEN")
    print("上传 docs/ …")
    for path in FILES:
        upload(path, f"site: {os.path.basename(path)}")

    print("开启 GitHub Pages …")
    status, pages = call("GET", f"/repos/{OWNER}/{REPO}/pages", expect=(200, 404))
    if status == 404:
        status, _ = call("POST", f"/repos/{OWNER}/{REPO}/pages",
                         {"source": {"branch": "main", "path": "/docs"}})
        print(f"  pages created -> {status}")
    else:
        call("PUT", f"/repos/{OWNER}/{REPO}/pages",
             {"source": {"branch": "main", "path": "/docs"}})
        print("  pages updated")

    url = f"https://{OWNER}.github.io/{REPO}/"
    for _ in range(20):
        time.sleep(6)
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                print(f"  site up: {url} (HTTP {r.status})")
                break
        except Exception as exc:
            print(f"  waiting… {exc}")
    print("install page:", url + "install.html")
    print("altstore source:", url + "altstore-source.json")


if __name__ == "__main__":
    main()


