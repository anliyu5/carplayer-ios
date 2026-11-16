#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 carplayer-ios 推到 GitHub 并用 GitHub Actions（macos-14 runner）出 ipa，最后把 ipa 抓回本地下载页。

不需要本机装 git：全程走 GitHub REST API（Git Data API 上传文件 → workflow_dispatch → 轮询 → 下载 artifact）。

用法：
    python tools/push_github.py --token ghp_xxx                  # 默认仓库名 carplayer-ios
    python tools/push_github.py --token ghp_xxx --repo my-music --public
    GH_TOKEN=ghp_xxx python tools/push_github.py                 # 从环境变量读 token

token 权限：
    经典 token：repo + workflow
    细粒度 token：Administration(Write, 建库) + Contents(Write) + Actions(Write) + Workflows(Write)
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "DerivedData"}
SKIP_EXT = {".pyc", ".pyo", ".zip", ".ipa"}
WORKFLOW = ".github/workflows/ios-build.yml"


def log(msg):
    print(msg, flush=True)


class StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """artifact 下载会 302 到对象存储，SAS 链接不能再带 Authorization 头，否则 401"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers.pop("Authorization", None)
            new.unredirected_hdrs.pop("Authorization", None)
        return new


_OPENER = urllib.request.build_opener(StripAuthOnRedirect)


class GH:
    def __init__(self, token):
        self.token = token

    def call(self, method, path, payload=None, raw=False, expect=(200, 201, 204)):
        url = path if path.startswith("http") else API + path
        data = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "carplayer-ios-push",
        }
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        if raw:
            with _OPENER.open(req, timeout=180) as resp:
                body = resp.read()
                if resp.status not in expect:
                    raise SystemExit(f"{method} {path} -> HTTP {resp.status}: {body[:400]!r}")
                return body
        last_error = None
        for attempt in range(4):
            try:
                return self._send(req, method, path, expect, raw)
            except SystemExit:
                raise
            except Exception as exc:      # 网络抖动：退避重试
                last_error = exc
                time.sleep(2 + attempt * 3)
        raise SystemExit(f"{method} {path} failed after retries: {last_error}")

    def _send(self, req, method, path, expect, raw):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read()
                if resp.status not in expect:
                    raise SystemExit(f"{method} {path} -> HTTP {resp.status}: {body[:400]!r}")
                if raw:
                    return body
                return json.loads(body or b"{}")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code in expect:
                return json.loads(body or "{}")
            raise SystemExit(f"{method} {path} -> HTTP {e.code}: {body[:600]}")


def collect_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            if os.path.splitext(name)[1].lower() in SKIP_EXT:
                continue
            if rel.startswith("dist/"):
                continue
            files.append((rel, full))
    files.sort()
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    ap.add_argument("--repo", default="carplayer-ios")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--public", action="store_true", help="建公开仓库（私有仓库的 Actions 分钟数受限）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = collect_files()
    log(f"待上传文件：{len(files)} 个，共 {sum(os.path.getsize(p) for _, p in files)/1024:.1f} KB")
    for rel, _ in files[:8]:
        log("  " + rel)
    if len(files) > 8:
        log(f"  … 其余 {len(files)-8} 个")

    if not args.token:
        raise SystemExit("缺少 token：用 --token 传，或设置环境变量 GH_TOKEN")
    if args.dry_run:
        log("dry-run：文件清单校验通过")
        return

    gh = GH(args.token)
    me = gh.call("GET", "/user")
    owner = me["login"]
    log(f"已登录：{owner}")

    # 1) 建仓（已存在就复用）
    payload = {"name": args.repo, "private": not args.public,
               "description": "Music iOS 1.9.14 — Android com.carplayer.music 的 iOS 复刻", "auto_init": False}
    try:
        gh.call("GET", f"/repos/{owner}/{args.repo}")
        log(f"仓库已存在：{owner}/{args.repo}")
    except SystemExit:
        gh.call("POST", "/user/repos", payload)
        log(f"已创建仓库：{owner}/{args.repo}")
        time.sleep(1.5)

    # 2) 空仓库先用 Contents API 落一个初始提交（否则 Git Data API 会返回 409 Git Repository is empty）
    try:
        gh.call("GET", f"/repos/{owner}/{args.repo}/git/ref/heads/{args.branch}")
        log("仓库已有分支，直接覆盖")
    except SystemExit:
        log("仓库为空，先做初始提交…")
        try:
            gh.call("PUT", f"/repos/{owner}/{args.repo}/contents/.gitkeep", {
                "message": "chore: init",
                "content": base64.b64encode(b"carplayer-ios\n").decode(),
                "branch": args.branch,
            })
        except SystemExit as e:
            log(f"  初始提交返回：{e}")
        time.sleep(1.0)

    # 3) 上传（Git Data API：blob → tree → commit → ref）
    log("上传 blob…")
    tree = []
    for rel, full in files:
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode()
        blob = gh.call("POST", f"/repos/{owner}/{args.repo}/git/blobs",
                       {"content": content, "encoding": "base64"})
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    log(f"  {len(tree)} 个 blob 完成")

    log("建 tree / commit…")
    new_tree = gh.call("POST", f"/repos/{owner}/{args.repo}/git/trees", {"tree": tree})
    commit = gh.call("POST", f"/repos/{owner}/{args.repo}/git/commits", {
        "message": "feat: CarPlayer iOS 1.9.14（Android com.carplayer.music 1:1 适配）",
        "tree": new_tree["sha"],
    })

    ref_path = f"/repos/{owner}/{args.repo}/git/refs/heads/{args.branch}"
    try:
        gh.call("PATCH", ref_path, {"sha": commit["sha"], "force": True})
        log(f"已更新分支 {args.branch}")
    except SystemExit:
        gh.call("POST", f"/repos/{owner}/{args.repo}/git/refs",
                {"ref": f"refs/heads/{args.branch}", "sha": commit["sha"]})
        log(f"已创建分支 {args.branch}")

    repo_url = f"https://github.com/{owner}/{args.repo}"
    log(f"仓库地址：{repo_url}")

    # 3) 触发 workflow
    log("触发 iOS Build workflow…")
    time.sleep(3)
    gh.call("POST", f"/repos/{owner}/{args.repo}/actions/workflows/ios-build.yml/dispatches",
            {"ref": args.branch}, expect=(204, 200, 201))

    run = None
    for _ in range(24):
        time.sleep(5)
        runs = gh.call("GET", f"/repos/{owner}/{args.repo}/actions/runs?per_page=5")
        for item in runs.get("workflow_runs", []):
            if item.get("name", "").startswith("iOS Build"):
                run = item
                break
        if run:
            break
    if not run:
        raise SystemExit(f"没找到 workflow run，去 {repo_url}/actions 看看")
    log(f"run #{run['run_number']}：{run['html_url']}")

    # 4) 等编译结束
    deadline = time.time() + 45 * 60
    while time.time() < deadline:
        time.sleep(15)
        cur = gh.call("GET", f"/repos/{owner}/{args.repo}/actions/runs/{run['id']}")
        status, concl = cur.get("status"), cur.get("conclusion")
        log(f"  状态：{status}" + (f" / {concl}" if concl else ""))
        if status == "completed":
            run = cur
            break
    else:
        raise SystemExit("编译超时（45 分钟）")

    if run.get("conclusion") != "success":
        raise SystemExit(f"编译失败：{run['html_url']}（看日志最后一步）")

    # 5) 下载 artifact
    arts = gh.call("GET", f"/repos/{owner}/{args.repo}/actions/runs/{run['id']}/artifacts")
    if not arts.get("artifacts"):
        raise SystemExit("没有 artifact 产出")
    art = arts["artifacts"][0]
    log(f"下载产物：{art['name']} ({art['size_in_bytes']/1024/1024:.1f} MB)")

    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    zip_path = os.path.join(dist, "artifact.zip")
    data = gh.call("GET", art["archive_download_url"], raw=True)
    with open(zip_path, "wb") as fh:
        fh.write(data)

    ipa_path = None
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.filename.lower().endswith(".ipa"):
                target = os.path.join(dist, os.path.basename(info.filename))
                with z.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                ipa_path = target
    os.remove(zip_path)

    if not ipa_path:
        raise SystemExit("artifact 里没有 .ipa")

    size_mb = os.path.getsize(ipa_path) / 1024 / 1024
    log(f"✅ ipa 已就绪：{ipa_path}（{size_mb:.1f} MB）")

    # 6) 发布到本地下载页
    site = os.path.join(dist, "site")
    if os.path.isdir(site):
        import shutil
        name = os.path.basename(ipa_path)
        shutil.copy2(ipa_path, os.path.join(site, name))
        index = os.path.join(site, "index.html")
        html = open(index, encoding="utf-8").read()
        placeholder = '<span class="btn plain" aria-disabled="true">待构建</span>'
        if placeholder in html:
            html = html.replace(placeholder, f'<a class="btn" href="{name}" download>下载 ipa</a>')
            html = html.replace(
                "未签名 ipa · 需在 macOS 上编译产出（本机为 Windows，不产出二进制包）<br>\n          产出后可用 Sideloadly / AltStore 用你的 Apple ID 自签安装",
                f"未签名 ipa · GitHub Actions（macos-14）编译产物 · {size_mb:.1f} MB<br>\n          用 Sideloadly / AltStore 以你的 Apple ID 自签后安装")
            open(index, "w", encoding="utf-8").write(html)
            log("下载页已更新")
        log(f"下载页：http://127.0.0.1:8791/{name}")

    log(f"GitHub Actions 记录：{repo_url}/actions/runs/{run['id']}")


if __name__ == "__main__":
    main()
