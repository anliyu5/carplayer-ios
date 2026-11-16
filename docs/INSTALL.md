# 装到 iOS 桌面（三种方式，按你的实际情况选）

> 先说清楚一条硬事实：**iOS 没有「安装配置文件 → 自动装 App」这种能力**。
> 配置文件（.mobileconfig）能做的只有：装证书、配 Wi-Fi/VPN/邮箱、加**桌面网页图标（Web Clip）**、下发 MDM 策略。
> 能把 App 图标真正放进桌面的只有三条路：**OTA 安装（需签名 ipa）**、**AltStore/SideStore 自签安装**、**MDM 推送（需企业 MDM + 设备注册）**。

---

## 方式一：描述文件 → 桌面图标（现在就能用）

文件：`CarPlayer.mobileconfig`（157 KB，内含 App 图标，安装后桌面出现 Music 图标，点了打开下载/安装页）

安装步骤：

1. iPhone 用 Safari 打开 https://anliyu5.github.io/carplayer-ios/CarPlayer.mobileconfig
2. 因为 GitHub Pages 对 `.mobileconfig` 返回的是 `application/octet-stream`，Safari 会把它下载到「文件」App；
   进「文件」App → 下载项 → 点 `CarPlayer.mobileconfig`
3. 设置 → 已下载描述文件 → 右上角「安装」→ 输入锁屏密码 → 安装
4. 回到桌面，Music 图标已就位（可长按删除）

> 如果你有自己的 HTTPS 服务器，把 MIME 设成 `application/x-apple-aspen-config`，
> Safari 点链接就会直接弹「此网站正尝试下载一个配置描述文件」，少一步。

## 方式二：AltStore / SideStore 源 → 真·App 图标上桌面（免费 Apple ID 即可）

源地址（JSON）：https://anliyu5.github.io/carplayer-ios/altstore-source.json

步骤：

1. 电脑装 AltStore（Windows 版需要装 AltServer + iTunes/iCloud）或 SideStore（需要一次配对文件）
2. 手机 AltStore → 右上「+」→ 粘贴上面的源地址 → 添加
3. 源里出现 **Music 1.9.14** → 点「安装」→ AltStore 用你的 Apple ID 在手机上完成签名并安装
4. 桌面出现真正的 App 图标，可正常启动（免费账号 7 天有效，AltStore 会自动续签）

这条是「配置文件形式 + 自动上桌面」在免费账号下最接近的实现。

## 方式三：OTA 安装（itms-services）→ 一次点击装到桌面

页面：https://anliyu5.github.io/carplayer-ios/install.html
清单：https://anliyu5.github.io/carplayer-ios/manifest.plist

点击「安装到 iPhone」后，系统会向 https 拉取 `manifest.plist` → 下载 ipa → 直接装到桌面。

**前提**：ipa 必须已用开发者证书签名，且 provisioning profile 里包含这台设备的 UDID。
现在的 `CarPlayer-1.9.14-unsigned.ipa` 是未签名包，OTA 会提示「无法安装」。

出签名包的两条命令（任选）：

```bash
# A. 有付费开发者账号：ad-hoc 签名（把设备 UDID 加进 profile）
TEAM_ID=你的团队ID ./scripts/build_ipa.sh signed

# B. 只有免费 Apple ID：用 Sideloadly 签名（一次装一台，7 天有效）
#    打开 Sideloadly → 拖入 CarPlayer-1.9.14-unsigned.ipa → 填 Apple ID → Start
```

签名后的 ipa 替换 `docs/CarPlayer-1.9.14-unsigned.ipa` 并重跑 `tools/publish_pages.py`，
`install.html` 上的按钮立即可用。

## 方式四（企业/车队场景）：MDM

如果这些车机是统一管理的，用 MDM（Jamf / 自建 MicroMDM）：
`InstallApplication` 命令 + 企业签名 ipa → 下发即自动上桌面，无需用户操作。需要 MDM 服务端与设备注册。

---

## 一句话结论

- 想**现在就有图标**：用方式一（描述文件）。
- 想让**图标点开是真 App**：用方式二（AltStore 源）。
- 想**一次点击静默装**：用方式三，但得先有签名证书；证书给我，我把签名也接进 Actions。
