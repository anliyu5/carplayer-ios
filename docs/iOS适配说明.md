# Android → iOS 适配说明（含逆向依据）

> 依据样本：`base.apk.1.apk.1_tmp.apk.1_tmp`（6.64 MB，`com.carplayer.music`，versionName 1.9.14 / versionCode 27）
> 工具链：自写 AXML 解析器 + ARSC 解析器 + DEX 解析器（无 apktool/jadx，全部本机完成）

---

## 一、样本事实（解码结果，非推测）

### 1.1 AndroidManifest（二进制 AXML 解码）

| 项 | 值 |
|---|---|
| package | `com.carplayer.music` |
| versionName / versionCode | `1.9.14` / `27` |
| minSdk / targetSdk / compileSdk | 24 / 34 / 35 |
| application | `com.carplayer.App`，`theme=@0x7f10026d`，`usesCleartextTraffic=true`，`supportsRtl=false` |
| 图标 | `@mipmap/ic_launcher`（108–192px 多密度 PNG，已用于 iOS AppIcon） |

Activities（全部 `screenOrientation=1` 竖屏、`configChanges=0x6a0`）：

| Activity | 说明 |
|---|---|
| `com.carplayer.ui.MainActivity` | 启动页，`launchMode=2`（singleTask），承载 home/library/search 三个 Fragment |
| `com.carplayer.ui.PlaylistActivity` | 歌单详情 |
| `com.carplayer.ui.PlayerActivity` | 播放页（`launchMode=1`） |
| `com.carplayer.ui.SettingsActivity` | 设置 / 音源管理 |
| `com.carplayer.ui.HistoryActivity` | 播放历史 |

服务与广播：`com.carplayer.player.PlaybackService`（`foregroundServiceType=0x2` 媒体播放，监听 `MEDIA_BUTTON`）、`com.carplayer.player.BootReceiver`（`BOOT_COMPLETED` / `QUICKBOOT_POWERON`）。

权限：INTERNET、ACCESS_NETWORK_STATE、WAKE_LOCK、RECEIVE_BOOT_COMPLETED、FOREGROUND_SERVICE(_MEDIA_PLAYBACK)、POST_NOTIFICATIONS、READ_MEDIA_AUDIO、READ/WRITE_EXTERNAL_STORAGE。

### 1.2 资源（resources.arsc 解码）

- 自有布局 17 个：`activity_main/history/player/playlist/settings`、`view_home/library/search/download`、`item_song/history/history_header/chart/hot_column/playlist_card/playlist_row`、`dialog_import`。
- 自有 drawable：`bg_card / bg_cover / bg_cover_gradient / bg_nav / bg_pill / bg_pill_accent / bg_progress_download / bg_search / bg_sheet / bg_surface`，`ic_home / ic_library / ic_search / ic_settings / ic_play / ic_pause / ic_prev / ic_next / ic_repeat / ic_repeat_one / ic_shuffle / ic_heart / ic_link / ic_close / ic_back / ic_delete / ic_check / ic_note / ic_more / ic_download / ic_chevron_right / ic_add / ic_history / ic_clock / seekbar`。
- 全部图标为 Material vector `pathData`，iOS 侧用自写 SVG path 解析器（`Icons.swift`）直接复用同一条路径字符串。

### 1.3 设计令牌（直接落进 iOS Theme.swift）

| 令牌 | 值 | 来源 |
|---|---|---|
| 背景 | `#0E0F13` | `color/bg` |
| 导航栏 | `#14161B` | `drawable/bg_nav` |
| 卡片面 | `#1F222B`（14dp 圆角） | `drawable/bg_surface` |
| 药丸 | `#22262F`（全圆角） | `drawable/bg_pill` |
| 底部弹层 | `#1B1E25`（24dp + 1dp `#2A2E38` 描边） | `drawable/bg_sheet` |
| 榜单卡 | `#17191F`（18dp） | `drawable/bg_card` |
| 封面占位 | `#262A34`（16dp） | `drawable/bg_cover` |
| 主色 | `#FFB020` / 暗 `#C98A1E` | `color/accent`、`accent_dim` |
| 主文字 / 次文字 | `#F2F4F8` / `#9AA0AC` | `color/text`、`text_sub` |
| 危险色 | `#E5534B` | `color/danger` |
| 进度条 | 槽 `#353947`，进度渐变 `#FFD25A→#FFB020→#FF9500`，高 8dp、圆角 4dp | `drawable/seekbar` |
| 主按钮药丸 | 填充 `#33FFB020`，描边 `#66FFB020` | `drawable/bg_pill_accent` |

### 1.4 关键尺寸（布局 XML 原文，单位 dp/pt 等价）

- 主界面：header 上 18 下 8、左 24 右 16；标题 24sp bold、副标题 12sp；设置按钮 52×52。
- 迷你播放器：高 72、左右各 16 外边距、内边距 14、封面 46、播放/下一首各 52；距底 8。
- 底部导航：高 78，图标 26，文字 11sp，选中 `#FFB020`。
- 首页：搜索条 56（左右内边距 18）、热歌榜标题 17sp bold、换一批 36 高、双列间距用 1dp 分隔线、列标题 14sp bold。
- 列表：`item_song` 64 / 封面 44 / 序号宽 26 / 主文 15sp / 副文 12sp / 角标 10sp / 更多 52；`item_history` 64 / 封面 44 / 更多 40；`item_playlist_row` 76 / 封面 58 / 更多 52；`item_hot_column` 56 / 序号 20 / 封面 40；`item_chart` 封面 120 / 名 13sp / 艺 11sp；`item_playlist_card` 宽 140、封面 140×140。
- 页头：`activity_playlist/history/settings` 均 64 高、返回键 52、标题 18sp bold。

### 1.5 代码结构（DEX 类表，354 个类）

| Android | 职责 | iOS 对应 |
|---|---|---|
| `data/Song` `Playlist` `HistoryEntry` `Store` | 数据与持久化 | `Models.swift`、`AppStore.swift` |
| `player/PlayerManager` `PlaybackService` `PlayerBus` | 播放状态机 / 后台服务 / 事件 | `PlayerEngine.swift` |
| `player/BootReceiver` | 开机自启 | 设置项 `bootAutoStart`（iOS 无权限，见差异表） |
| `repo/MusicRepo` `HotChart` `LocalMusic` `Downloader` | 搜索、榜单、本地、下载 | `BuiltinSources.swift`、`Downloader.swift` |
| `source/SourceEngine` | 五平台搜索/榜单 | `BuiltinSources.swift` |
| `source/custom/LxRuntime` `CustomSourceManager` `ScriptMeta` | LX 脚本引擎 | `LxRuntime.swift`（JavaScriptCore） |
| `source/qing/QingConfig` `QingGate` `QingLine` `QingSearch` | 青听网关 | `QingGate.swift` |
| `source/SecureKwApiModule` + `source/shim/*` | 酷我加密接口 / RN 模块垫片 | 由 LX 脚本或自建接口替代（`EndpointBook`） |
| `util/CoverLoader` `ImageLoader` `ScreenScale` `HistoryFormat` | 封面、图片、缩放、时间分组 | `CoverImage.swift`、`Theme.swift` 的 `Fmt` |
| `CrashGuard` | 崩溃兜底 | `SettingsView` 的诊断区读取 `crash.json` |
| `ui/*Activity` + 11 个 Adapter | 全部界面 | 10 个 SwiftUI 视图 + `Components.swift` |

## 二、逐屏对照

| Android | iOS 文件 | 复刻要点 |
|---|---|---|
| `activity_main` (v9) | `MainShell.swift` | header / content / miniPlayer / navBar 四段式，尺寸与色值原样 |
| `view_home` (EL) | `HomeView.swift` | 搜索条 56、热歌榜 + 换一批、小Q热歌 / 小云热歌 双列 + 1dp 分隔线 |
| `view_library` (o7) | `LibraryView.swift` | 播放历史卡片（30 图标 + 15/11 文本 + 箭头）、我的歌单行 76 |
| `view_search` (Fj) | `SearchView.swift` | 关闭键 44、搜索条 56、音源 chips、搜索历史、状态行、结果列表 |
| `view_download` (Mq) | `DownloadView.swift` | 音质行 58（18 圆角）、空态 46 图标 + 两段文案 |
| `activity_playlist` (vc) | `PlaylistView.swift` | 页头 64、封面 96、播放全部/全部下载 44、可选本地过滤框 42 |
| `activity_history` (XY) | `HistoryView.swift`(HistoryView) | 清空按钮 36、播放全部 40、今天/昨天/更早 分组头 12sp 主色 |
| `activity_settings` (q3) | `SettingsView.swift` | 下载管理块 / 音源折叠块 / 导入歌单 / 更多设置（搜索范围 + 诊断）/ 版本号，全部条目与文案一一对应 |
| `dialog_import` (pm) | `SettingsView` 的 `playlistImportSheet` | 标题 16、输入框 2 行、说明 12sp |
| `PlayerActivity`（代码构建） | `PlayerView.swift` | 无 XML 可依，按同一令牌还原：封面 16 圆角、歌词 5 行、渐变进度条、80 圆主按钮、模式/音质/音量 |
| 歌曲「⋮」菜单 | `SongActions.swift` | 下一首播放 / 加入歌单 / 收藏 / 下载 / 从歌单移除 |

## 三、文案

界面全部中文文案取自 DEX 字符串表（367 条 CJK 字符串），逐条落到对应视图，例如
`听你想听`、`热歌榜`、`换一批`、`小Q热歌`、`小云热歌`、`搜索歌曲、歌手`、`共 N 首`、
`还没有播放记录`、`最多保留最近 100 首`、`下载音质`、`启动时自动播放`、`开机自动启动`、
`导入音源`、`粘贴脚本导入`、`怎么获取音源？`、`导入歌单`、`QQ / 网易云链接`、
`更多设置`、`搜索范围`、`只影响搜索和歌单导入，与播放无关。`、`诊断`、`查看上次崩溃日志`、
`这款…（音源提示语）`、`标准 128K` / `较高 320K` / `无损 FLAC` / `超清母带FLAC`、
`顺序播放` / `单曲循环` / `随机播放`、`暂不播放` 等。

## 四、无法 1:1 的平台项（已在设置页标注）

1. **开机自启**：iOS 不允许第三方 App 开机自启，`bootAutoStart` 开关保留但改由「启动时自动播放 + CarPlay 续播」实现。
2. **通知栏媒体控件**：系统接管，走 `MPNowPlayingInfoCenter` + `MPRemoteCommandCenter`（已接播放/暂停/上下曲/拖动进度）。
3. **APK 内的 RSA 工具**：`utils_rsa_encrypt` 暂返回空串（AES-128-CBC/ECB、MD5、Base64、buffer 已完整实现）；只影响极少数带 RSA 签名校验的脚本。
4. **内置酷我加密接口**（`SecureKwApiModule` 走 RN 垫片 + 加密）：iOS 版不带这套加密实现，改走 `EndpointBook` 模板或脚本/青听网关。
5. **状态栏/导航栏**：Android 用主题色，iOS 固定深色（`preferredColorScheme(.dark)`，状态栏浅色文字）。
