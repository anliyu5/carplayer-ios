#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/ 一次性提交（单 commit），再触发一次 GitHub Pages 构建并等待完成。
避免逐文件 PUT 导致 Pages 构建被反复取消（status=errored）。
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER, REPO = "anliyu5", "carplayer-ios"
TOKEN = os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"


def call(method, path, payload=None, expect=(200, 201, 204)):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "carplayer-docs",
    })
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if e.code in expect:
            return e.code, {}
        raise SystemExit(f"{method} {path} -> {e.code}: {body[:300]}")


def main():
    if not TOKEN:
        raise SystemExit("缺 GH_TOKEN")

    ref = call("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/main")[1]
    head = ref["object"]["sha"]
    base_tree = call("GET", f"/repos/{OWNER}/{REPO}/git/commits/{head}")[1]["tree"]["sha"]
    print("head:", head[:7], "tree:", base_tree[:7])

    docs = os.path.join(ROOT, "docs")
    entries = []
    for name in sorted(os.listdir(docs)):
        full = os.path.join(docs, name)
        if not os.path.isfile(full):
            continue
        content = base64.b64encode(open(full, "rb").read()).decode()
        blob = call("POST", f"/repos/{OWNER}/{REPO}/git/blobs", {"content": content, "encoding": "base64"})[1]
        entries.append({"path": f"docs/{name}", "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  blob {name} ({os.path.getsize(full)/1024:.1f} KB)")

    tree = call("POST", f"/repos/{OWNER}/{REPO}/git/trees",
                {"base_tree": base_tree, "tree": entries})[1]
    commit = call("POST", f"/repos/{OWNER}/{REPO}/git/commits",
                  {"message": "site: 更新下载页与安装件（single commit）",
                   "tree": tree["sha"], "parents": [head]})[1]
    call("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/main", {"sha": commit["sha"], "force": True})
    print("committed:", commit["sha"][:7])

    print("触发 Pages 构建…")
    try:
        call("POST", f"/repos/{OWNER}/{REPO}/pages/builds", expect=(200, 201, 204))
    except SystemExit as e:
        print("  trigger:", e)

    for i in range(40):
        time.sleep(10)
        pages = call("GET", f"/repos/{OWNER}/{REPO}/pages")[1]
        build = call("GET", f"/repos/{OWNER}/{REPO}/pages/builds/latest")[1]
        print(f"  [{i}] pages={pages.get('status')} build={build.get('status')} {build.get('error', {})}")
        if pages.get("status") == "built":
            break
    print("done:", f"https://{OWNER}.github.io/{REPO}/")


if __name__ == "__main__":
    main()
