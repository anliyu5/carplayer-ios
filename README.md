# Music for iOS（CarPlayer iOS 版）

Android 版 `com.carplayer.music`（`base.apk`，versionName **1.9.14** / versionCode **27**）的 iOS 复刻工程。
**布局、配色、图标、文案、交互全部沿用原版资源，不做任何风格改造。**

- 工程名：`CarPlayer.xcodeproj`
- Bundle ID：`com.carplayer.music`（与 Android 包名一致）
- 最低系统：iOS 16.0（SwiftUI + AVFoundation + JavaScriptCore）
- 已验证编译：GitHub Actions `macos-15-intel` + Xcode 16.4，产出 `CarPlayer-1.9.14-unsigned.ipa`
- 语言：Swift 5.9 / 无第三方依赖

---

## 1. 目录

```
carplayer-ios/
├── CarPlayer.xcodeproj/           # 已生成，双击即可在 Xcode 打开
├── CarPlayer/
│   ├── CarPlayerApp.swift         # 入口 + 路由（对应 Android Activity 栈）
│   ├── MainShell.swift            # 主界面 activity_main（header / content / miniPlayer / navBar）
│   ├── HomeView.swift             # 首页 view_home（搜索条 + 热歌榜 + 小Q/小云双列）
│   ├── LibraryView.swift          # 歌单 view_library（播放历史入口 + 我的歌单）
│   ├── SearchView.swift           # 搜索 view_search（音源 chips + 历史 + 结果）
│   ├── DownloadView.swift         # 下载 view_download（音质行 + 列表/空态）
│   ├── PlayerView.swift           # 播放页（原版为代码构建视图，此处按同一设计令牌还原）
│   ├── PlaylistView.swift         # 歌单详情 activity_playlist + 播放历史 activity_history
│   ├── SettingsView.swift         # 设置 activity_settings（下载管理 / 音源 / 导入歌单 / 诊断）
│   ├── SongActions.swift          # 歌曲「⋮」菜单 + 加入歌单选择器
│   ├── Components.swift           # item_song / item_history / item_playlist_row / item_chart / item_hot_column / item_playlist_card
│   ├── Theme.swift                # 颜色、圆角、字号、格式器（全部取自 resources.arsc）
│   ├── Icons.swift                # Material vector pathData → SwiftUI Shape（图标 1:1）
│   ├── Models.swift               # Song / Playlist / HistoryEntry / Quality / PlayMode / ScriptMeta / QingConfig
│   ├── AppStore.swift             # 状态与持久化（对应 data/Store），JSON 落盘
│   ├── PlayerEngine.swift         # AVPlayer + 后台播放 + 锁屏/CarPlay 遥控（对应 PlaybackService + PlayerManager）
│   ├── Downloader.swift           # 下载到 文件 App → CarPlayer/Music（对应 repo/Downloader）
│   ├── BuiltinSources.swift       # 内置搜索/榜单适配（对应 source/SourceEngine）+ 可换的接口模板
│   ├── QingGate.swift             # 青听网关（对应 source/qing/*）
│   ├── LxRuntime.swift            # LX 自定义音源脚本引擎（JavaScriptCore，对应 source/custom/LxRuntime）
│   ├── CoverImage.swift           # 封面加载与缓存（对应 util/CoverLoader + ImageLoader）
│   ├── Resources/lx-runtime.js    # 直接复用 APK 内 assets/lx/runtime.js
│   └── Assets.xcassets            # AppIcon（由 APK 启动图标生成）
├── scripts/build_ipa.sh           # 一键出 ipa（Mac 上运行）
├── .github/workflows/ios-build.yml# 没 Mac 也能在 GitHub 上出未签名 ipa
└── tools/gen_project.py           # 工程文件生成器（新增 Swift 文件后重跑即可）
```

## 2. 构建

### 2.1 有 Mac / Xcode

```bash
open CarPlayer.xcodeproj
# Xcode → 选中 CarPlayer target → Signing & Capabilities → 选你的 Team
# 真机运行：⌘R，或 Product → Archive 出包
```

一键出包：

```bash
./scripts/build_ipa.sh                  # 未签名 ipa（dist/CarPlayer-1.9.14-unsigned.ipa）
TEAM_ID=你的团队ID ./scripts/build_ipa.sh signed   # 带签名 ipa
```

### 2.2 没有 Mac（已跑通，ipa 已产出）

仓库：https://github.com/anliyu5/carplayer-ios

```powershell
$env:GH_TOKEN = "你的token"
python tools\push_github.py --public   # 建库 + 推送 + 触发编译 + 抓回 ipa + 更新下载页
python tools\fetch_ipa.py              # 只重新下载最新一次成功构建的 ipa
```

Runner 实测（2026-11）：

| label | 结果 |
|---|---|
| `macos-14` | 立即 cancelled：`configuration 'macos-14-arm64-us-default' is not supported` |
| `macos-13` | 一直 queued 不出机（镜像已退役） |
| `macos-15-intel` | 可用：macOS 15.6 + Xcode 16.4，编译约 2 分半 |
| `macos-15` | 可用（arm64 宿主，出包同样可用） |

产物：`dist/CarPlayer-1.9.14-unsigned.ipa`（1.01 MB，`Payload/CarPlayer.app` 内含 2.7 MB arm64 主二进制）。

未签名 ipa 用 **Sideloadly / AltStore / TrollStore** 以你自己的 Apple ID 自签后即可装机：

1. 打开 Sideloadly，连接 iPhone；
2. 拖入 `CarPlayer-1.9.14-unsigned.ipa`，填 Apple ID；
3. Start → 手机上「设置 → 通用 → VPN与设备管理」信任证书。

## 3. 音源（与 Android 版同样的用法）

Android 版本身不带内置播放音源，播放地址来自：

| 途径 | 入口 | iOS 实现 |
|---|---|---|
| LX 自定义音源脚本（`.js`） | 设置 → 导入音源 | `LxRuntime.swift`，JavaScriptCore 跑 `assets/lx/runtime.js` 同一份 runtime |
| 青听网关（`music.json`） | 设置 → 青听音源配置 | `QingGate.swift`（`lines[].url` 为网关根地址） |
| 内置搜索/榜单 | 首页 / 搜索 | `BuiltinSources.swift`，接口模板集中在 `EndpointBook`，可整体替换 |

`EndpointBook` 里的地址是占位模板，替换成你自己的部署即可，解析逻辑不用改：

```swift
// BuiltinSources.swift
struct EndpointBook {
    var search: [String: String] = ["kw": "...", "wy": "...", "tx": "...", "mg": "...", "kg": "..."]
    var resolve: [String: String] = [:]   // 形如 "kw": "https://your.api/url?id={id}&q={quality}"
    var lyric:  [String: String] = [:]
}
```

## 4. 与 Android 版的差异（仅平台强制项，无功能删减）

| 项 | Android | iOS |
|---|---|---|
| 开机自启 | `BootReceiver` 拉起 | iOS 无第三方开机自启权限；改为「启动时自动播放」+ CarPlay 上次播放，设置页已标注 |
| 下载目录 | `手机存储/Music/Music` | `文件 App → 我的 iPhone → Music → Music`（已开启 `UIFileSharingEnabled`） |
| 前台服务 | `PlaybackService`（FGS） | `AVAudioSession(.playback)` + `UIBackgroundModes: audio`，行为等价 |
| 明文 HTTP | `usesCleartextTraffic=true` | `NSAllowsArbitraryLoads=true`（音源接口多为 http） |
| RSA 工具 | `utils_rsa_encrypt` | 返回空串，脚本会走降级分支（AES/MD5/Base64 已完整实现） |

## 5. 已知待你补齐的点

1. `EndpointBook.resolve` 为空时，内置源搜到歌但不会出声 —— 这是 Android 版设计（"没导入之前：歌能搜到，但点了放不出声"），导入脚本/青听配置后即可播放。
2. 少数脚本使用 RSA 签名，需要你在 `LxRuntime.swift` 的 `__lx_native_call__utils_rsa_encrypt` 里接 `Security.framework`（函数已留空实现）。
3. 播放页在 Android 侧是 `PlayerActivity` 代码构建（无 layout XML），iOS 版按同一套颜色/圆角/字号还原：封面 16 圆角、进度条 8 高（#353947 底槽 + #FFD25A→#FFB020→#FF9500 渐变）、主按钮 80 圆底 #FFB020、图标全部使用原版 Material pathData。

## 6. 青听音源配置（music.json）实测结构

官方配置长这样（`https://13413.kstore.vip/QingMusic/music.json`）：

```jsonc
/**
 * @name 青听音源
 * @version 1.1
 * @author 微信公众号: 元力菌
 */
{
  "lines": [
    { "id": "kw", "name": "小窝源", "enabled": true,
      "searchApi": "fetchSearchMusic", "detailApi": "fetchMusicDetail",
      "levels": ["standard","exhigh","lossless","atmos","atmos_plus","master"] },
    { "id": "kg", "name": "小狗源", "levels": ["standard","exhigh","lossless","hires","atmos","clear"] },
    { "id": "wy", "name": "小云源", "levels": ["standard","exhigh","lossless","hires","sky","jyeffect","jymaster"] },
    { "id": "tx", "name": "小Q源", "levels": ["standard","exhigh","lossless","sur","jymaster"] },
    { "id": "qs", "name": "汽水源", "levels": ["standard","exhigh","lossless","hires","atmos"] },
    { "id": "bili", "name": "哔哩哔哩", "levels": ["bili192"] },
    { "id": "mg", "name": "小粉源", "levels": ["standard"] }
  ]
}
```

要点：

- **lines 里没有 url 字段**；网关根地址由配置自身网址推导：`https://13413.kstore.vip/QingMusic/music.json` → `https://13413.kstore.vip`。
- 头部 `/** @name … */` 会被解析成音源标题/版本/作者并显示在设置页。
- `id` 映射到平台（kw/kg/wy/tx/qs/bili/mg → 酷我/酷狗/网易/QQ/汽水/哔哩哔哩/咪咕）；
- `levels` 映射到音质：`standard→128K`、`exhigh→320K`、`lossless→FLAC`、`hires→Hi-Res`、`atmos/atmos_plus/clear→全景声`、`master/jymaster→母带`、`sky/sur/jyeffect→沉浸环绕`、`bili192→FLAC`。
- 播放地址走网关：`GET {base}/v1/music/resolve-url`（依次尝试 `source/id/level`、`platform/musicId/quality`、`api/source/id/level` 等参数组合，返回体里任意 http 链接都会被采纳），授权走 `{base}/v1/gateway/ticket`（拿不到 ticket 不阻断）。
- 搜索不依赖网关：按配置里启用的线路直接用各平台公开接口搜（`SourceEngine` 那套），保证「导入即可搜」。

## 7. 青听网关（播放地址）—— 从 smali 还原的签名协议

`QingGateway.swift` 完全按 `com.carplayer.source.qing.QingGate` 的反汇编结果实现：

| 项 | 值 |
|---|---|
| 网关域名（失败轮换） | `https://musicserver.haitangw.cc` / `https://qt.haitangw.net` |
| appId / 版本 | `qingmusic-android` / `1.4.0` |
| HMAC 密钥 | `qm-gw-7c1f4e9a2b8d5360e1a7c4f9b2d8036c` |
| 签名串 | `join("\n", [appId, ts, nonce, "POST", path, sha256(body)])` |
| 签名 | `HMAC-SHA256(secret, 签名串)` 的 hex，放到 `X-Qing-Sign` |
| 其它头 | `X-Request-Id`(32hex) `X-Qing-App-Id` `X-Qing-App-Version` `X-Qing-Device-Id`(32hex，持久化) `X-Qing-Ts`(毫秒) `X-Qing-Nonce`(32hex) |
| 授权 | `POST /v1/gateway/ticket` body `{"deviceId","appVersion","platform":"android"}` → `{"ticket":"<JWT>"}`，之后带 `Authorization: Bearer <ticket>` |
| 取地址 | `POST /v1/music/resolve-url` body `{"source","rid","level"}` → `{"code":0,"data":{"url":"…"}}` |

实测（本机直连）：tx `002uaCOF3Euu5V` → `isure.stream.qqmusic.qq.com/...vkey...` HEAD 200 `audio/mpeg` 3,969,554 B；
kw `51685512` → 4,318,872 B；wy `2668397359` → 4,332,717 B；kw lossless → 1.6 MB。

rid 取值：QQ = songmid、酷我 = rid、酷狗 = hash、网易/咪咕/汽水/B站 = 各自歌曲 ID。

