#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载指定 workflow run 的最新 artifact（ipa），落到 dist/ 并同步更新本地下载页。"""
import base64
import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER, REPO = "anliyu5", "carplayer-ios"
TOKEN = os.environ.get("GH_TOKEN") or ""
API = "https://api.github.com"


class StripAuth(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers.pop("Authorization", None)
            new.unredirected_hdrs.pop("Authorization", None)
        return new


OPENER = urllib.request.build_opener(StripAuth)


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "carplayer-fetch",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def main():
    runs = api(f"/repos/{OWNER}/{REPO}/actions/runs?per_page=10")["workflow_runs"]
    run = next((r for r in runs if r["name"].startswith("iOS Build") and r["conclusion"] == "success"), None)
    if not run:
        raise SystemExit("没有成功的 run")
    print(f"run #{run['run_number']} {run['html_url']}")

    arts = api(f"/repos/{OWNER}/{REPO}/actions/runs/{run['id']}/artifacts")["artifacts"]
    if not arts:
        raise SystemExit("该 run 没有 artifact")
    art = arts[0]
    print(f"artifact {art['name']} {art['size_in_bytes']/1024/1024:.2f} MB")

    req = urllib.request.Request(art["archive_download_url"], headers={
        "Authorization": f"Bearer {TOKEN}", "User-Agent": "carplayer-fetch"})
    with OPENER.open(req, timeout=300) as r:
        blob = r.read()

    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    ipa_path = None
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for info in z.infolist():
            if info.filename.lower().endswith(".ipa"):
                ipa_path = os.path.join(dist, os.path.basename(info.filename))
                with z.open(info) as src, open(ipa_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    if not ipa_path:
        raise SystemExit("artifact 内没有 ipa")

    size_mb = os.path.getsize(ipa_path) / 1024 / 1024
    print(f"ipa: {ipa_path} ({size_mb:.2f} MB)")

    site = os.path.join(dist, "site")
    if os.path.isdir(site):
        name = os.path.basename(ipa_path)
        shutil.copy2(ipa_path, os.path.join(site, name))
        index = os.path.join(site, "index.html")
        html = open(index, encoding="utf-8").read()
        placeholder = '<span class="btn plain" aria-disabled="true">待构建</span>'
        if placeholder in html:
            html = html.replace(placeholder, f'<a class="btn" href="{name}" download>下载 ipa</a>')
            html = html.replace(
                "未签名 ipa · 需在 macOS 上编译产出（本机为 Windows，不产出二进制包）<br>\n          产出后可用 Sideloadly / AltStore 用你的 Apple ID 自签安装",
                f"未签名 ipa · GitHub Actions（{run['head_branch']} / macos-15-intel / Xcode 16.4）编译产物 · {size_mb:.2f} MB<br>\n          用 Sideloadly / AltStore 以你的 Apple ID 自签后安装")
            open(index, "w", encoding="utf-8").write(html)
            print("下载页已更新")
        print(f"http://127.0.0.1:8791/{name}")


if __name__ == "__main__":
    main()
