import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "README.md")
t = io.open(p, encoding="utf-8").read()
section = """
## 7. 青听网关（播放地址）—— 从 smali 还原的签名协议

`QingGateway.swift` 完全按 `com.carplayer.source.qing.QingGate` 的反汇编结果实现：

| 项 | 值 |
|---|---|
| 网关域名（失败轮换） | `https://musicserver.haitangw.cc` / `https://qt.haitangw.net` |
| appId / 版本 | `qingmusic-android` / `1.4.0` |
| HMAC 密钥 | `qm-gw-7c1f4e9a2b8d5360e1a7c4f9b2d8036c` |
| 签名串 | `join("\\n", [appId, ts, nonce, "POST", path, sha256(body)])` |
| 签名 | `HMAC-SHA256(secret, 签名串)` 的 hex，放到 `X-Qing-Sign` |
| 其它头 | `X-Request-Id`(32hex) `X-Qing-App-Id` `X-Qing-App-Version` `X-Qing-Device-Id`(32hex，持久化) `X-Qing-Ts`(毫秒) `X-Qing-Nonce`(32hex) |
| 授权 | `POST /v1/gateway/ticket` body `{"deviceId","appVersion","platform":"android"}` → `{"ticket":"<JWT>"}`，之后带 `Authorization: Bearer <ticket>` |
| 取地址 | `POST /v1/music/resolve-url` body `{"source","rid","level"}` → `{"code":0,"data":{"url":"…"}}` |

实测（本机直连）：tx `002uaCOF3Euu5V` → `isure.stream.qqmusic.qq.com/...vkey...` HEAD 200 `audio/mpeg` 3,969,554 B；
kw `51685512` → 4,318,872 B；wy `2668397359` → 4,332,717 B；kw lossless → 1.6 MB。

rid 取值：QQ = songmid、酷我 = rid、酷狗 = hash、网易/咪咕/汽水/B站 = 各自歌曲 ID。

"""
if "## 7. 青听网关" not in t:
    t = t.rstrip() + "\n" + section
    io.open(p, "w", encoding="utf-8").write(t)
    print("README + gateway section")
