#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「装到 iOS 桌面」所需的全部分发件：

  1. CarPlayer.mobileconfig      —— 配置描述文件（Web Clip），装完桌面直接出现图标（不需要签名/开发者账号）
  2. manifest.plist              —— OTA 安装清单（配合已签名 ipa，Safari 打开 itms-services 链接即装到桌面）
  3. install.html                —— OTA 安装页（点击按钮走 itms-services）
  4. altstore-source.json        —— AltStore / SideStore 源（免费 Apple ID，在手机上签名安装，图标上桌面）

用法：
  python tools/gen_install_assets.py --base-url https://raw.githubusercontent.com/anliyu5/carplayer-ios/main/releases --webclip-url https://github.com/anliyu5/carplayer-ios
"""
import argparse
import base64
import hashlib
import io
import json
import os
import plistlib
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(ROOT, "CarPlayer", "Assets.xcassets", "AppIcon.appiconset", "AppIcon.png")
IPA_NAME = "CarPlayer-1.9.14-unsigned.ipa"
BUNDLE_ID = "com.carplayer.music"
APP_NAME = "Music"
VERSION = "1.9.14"
BUILD = "27"
DEVELOPER = "carplayer"


def stable_uuid(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest().upper()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def build_webclip(url: str, label: str, out_path: str) -> None:
    icon = base64.b64encode(open(ICON, "rb").read()).decode()
    payload = {
        "PayloadType": "com.apple.webClip.managed",
        "PayloadIdentifier": f"{BUNDLE_ID}.webclip",
        "PayloadUUID": stable_uuid("webclip-payload"),
        "PayloadVersion": 1,
        "PayloadDisplayName": label,
        "Label": label,
        "URL": url,
        "Icon": base64.b64decode(icon),
        "IsRemovable": True,
        "Precomposed": False,
        "FullScreen": False,
    }
    profile = {
        "PayloadType": "Configuration",
        "PayloadIdentifier": f"{BUNDLE_ID}.profile",
        "PayloadUUID": stable_uuid("profile-root"),
        "PayloadVersion": 1,
        "PayloadDisplayName": f"{label} · 桌面图标",
        "PayloadOrganization": DEVELOPER,
        "PayloadDescription": "安装后在桌面生成 Music 图标，点击直达下载/安装页。来源：" + url,
        "PayloadContent": [payload],
    }
    with open(out_path, "wb") as fh:
        plistlib.dump(profile, fh)
    print(f"[mobileconfig] {out_path}")


def build_manifest(ipa_url: str, bundle_id: str, version: str, out_path: str) -> None:
    manifest = {
        "items": [{
            "assets": [
                {"kind": "software-package", "url": ipa_url},
                {"kind": "display-image", "needs-shine": False,
                 "url": ipa_url.rsplit("/", 1)[0] + "/AppIcon.png"},
                {"kind": "full-size-image", "needs-shine": False,
                 "url": ipa_url.rsplit("/", 1)[0] + "/AppIcon.png"},
            ],
            "metadata": {
                "bundle-identifier": bundle_id,
                "bundle-version": version,
                "kind": "software",
                "title": APP_NAME,
            },
        }]
    }
    with open(out_path, "wb") as fh:
        plistlib.dump(manifest, fh)
    print(f"[manifest.plist] {out_path}")


def build_altstore_source(base_url: str, out_path: str, ipa_size: int) -> None:
    icon_url = f"{base_url}/AppIcon.png"
    source = {
        "name": "CarPlayer Source",
        "identifier": "com.carplayer.source",
        "subtitle": "Music iOS 自签安装源",
        "description": "Music iOS 1.9.14（Android com.carplayer.music 的 iOS 复刻）",
        "iconURL": icon_url,
        "headerURL": icon_url,
        "website": "https://github.com/anliyu5/carplayer-ios",
        "tintColor": "#FFB020",
        "featuredApps": [BUNDLE_ID],
        "apps": [{
            "name": APP_NAME,
            "bundleIdentifier": BUNDLE_ID,
            "developerName": DEVELOPER,
            "subtitle": "多音源音乐播放器 · iOS 版",
            "localizedDescription": "布局、配色、图标、文案与 Android 版 1:1 一致；支持 LX 自定义音源脚本、青听网关、五平台搜索、后台播放与锁屏遥控。",
            "iconURL": icon_url,
            "tintColor": "#FFB020",
            "category": "music",
            "versions": [{
                "version": VERSION,
                "buildVersion": BUILD,
                "date": "2026-11-16",
                "downloadURL": f"{base_url}/{IPA_NAME}",
                "size": ipa_size,
                "minOSVersion": "16.0",
                "localizedDescription": "首个 iOS 版本，功能与 Android 1.9.14 对齐。",
            }],
            "appPermissions": {"entitlements": [], "privacy": {}},
        }],
        "news": [],
    }
    with io.open(out_path, "w", encoding="utf-8") as fh:
        json.dump(source, fh, ensure_ascii=False, indent=2)
    print(f"[altstore-source.json] {out_path}")


def build_ota_page(manifest_url: str, base_url: str, out_path: str) -> None:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>安装 Music</title>
<style>
body{{margin:0;background:#0E0F13;color:#F2F4F8;font-family:-apple-system,"PingFang SC",sans-serif;
display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;gap:18px;padding:24px}}
img{{width:96px;height:96px;border-radius:22px;box-shadow:0 10px 30px rgba(0,0,0,.6)}}
h1{{font-size:20px;margin:0}}
p{{color:#9AA0AC;font-size:13px;line-height:1.7;text-align:center;margin:0}}
a.btn{{display:inline-flex;align-items:center;justify-content:center;height:46px;padding:0 26px;border-radius:999px;
background:rgba(255,176,32,.2);border:1px solid rgba(255,176,32,.4);color:#FFB020;font-size:15px;text-decoration:none}}
.note{{font-size:12px;color:#9AA0AC;max-width:420px;text-align:center;line-height:1.8}}
code{{color:#F2F4F8}}
</style></head><body>
<img src="AppIcon.png" alt="Music">
<h1>Music 1.9.14</h1>
<a class="btn" href="itms-services://?action=download-manifest&url={manifest_url}">安装到 iPhone</a>
<p class="note">点击后系统会弹出「安装」确认，装完图标直接出现在桌面。<br>
该方式要求 ipa 已用开发者证书签名（含本机 UDID），未签名包会提示无法安装。</p>
<p class="note">不想签名？用描述文件方式：<a href="CarPlayer.mobileconfig" style="color:#FFB020">下载 CarPlayer.mobileconfig</a> →
设置里安装 → 桌面出现图标。</p>
</body></html>
"""
    with io.open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"[install.html] {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="https://raw.githubusercontent.com/anliyu5/carplayer-ios/main/releases",
                    help="ipa / 图标 所在的公网目录")
    ap.add_argument("--webclip-url", default="https://github.com/anliyu5/carplayer-ios",
                    help="桌面图标点开后的地址")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist", "site"))
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    build_webclip(args.webclip_url, APP_NAME, os.path.join(args.out, "CarPlayer.mobileconfig"))
    build_manifest(f"{args.base_url}/{IPA_NAME}", BUNDLE_ID, VERSION, os.path.join(args.out, "manifest.plist"))
    ipa_path = os.path.join(ROOT, "dist", IPA_NAME)
    size = os.path.getsize(ipa_path) if os.path.exists(ipa_path) else 0
    build_altstore_source(args.base_url, os.path.join(args.out, "altstore-source.json"), size)
    build_ota_page(f"{args.base_url}/manifest.plist", args.base_url, os.path.join(args.out, "install.html"))


if __name__ == "__main__":
    main()
