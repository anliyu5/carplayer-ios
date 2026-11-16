# 推到 GitHub 并出 ipa（Windows 无 Mac 版）

> 本机没有 git、没有 GitHub CLI、没有 token。**全程不需要装 git**：`tools/push_github.py` 直接走 GitHub REST API。

## 一次性准备：一个 token

打开 https://github.com/settings/tokens → 生成 token，两种都行：

- **经典 token**：勾 `repo` + `workflow`
- **细粒度 token**：仓库权限里给 `Administration: Read and write`（建库）+ `Contents: Read and write` + `Actions: Read and write` + `Workflows: Read and write`

把 token 放进环境变量（PowerShell，当前窗口有效）：

```powershell
$env:GH_TOKEN = "ghp_你的token"
```

## 一条命令：建库 + 推代码 + 云端编译 + 抓回 ipa + 更新下载页

```powershell
cd carplayer-ios
& "C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" -X utf8 tools\push_github.py --public
```

公共仓库的 Actions 免费额度不限（私有仓库 macOS 每分钟按 10 倍折算）。实测：一次出包约 2 分半，产物 1.01 MB。

脚本做的事：

1. `GET /user` 验证 token，拿到你的 GitHub 用户名；
2. 建仓库 `carplayer-ios`（已存在就复用）；
3. 用 Git Data API 逐个上传 blob → 建 tree → 建 commit → 更新 `main`；
4. `workflow_dispatch` 触发 `.github/workflows/ios-build.yml`（`macos-15-intel`，免签名编译；macos-14 在该账号下报 configuration not supported，macos-13 已退役）；
5. 每 15 秒轮询 run 状态，完成后下载 artifact zip；
6. 解出 `CarPlayer-1.9.14-unsigned.ipa` 到 `dist/`，并复制进下载页 `dist/site/`、把页面上的「待构建」换成下载按钮；
7. 打印 ipa 路径、仓库地址、Actions 记录地址。

## 装到手机

1. 手机装 **Sideloadly**（Windows 版）或 **AltStore**；
2. 拖入 `dist/CarPlayer-1.9.14-unsigned.ipa`；
3. 填你的 Apple ID → Start（免费账号 7 天有效，需重签）；
4. iPhone「设置 → 通用 → VPN与设备管理」信任开发者证书。

签名失败常见原因：Bundle ID 已被占用 → 在 Xcode 里改 `PRODUCT_BUNDLE_IDENTIFIER`（如 `com.你的名字.carplayer`）后重推即可。

## 出带签名的包（可选，需付费开发者账号）

在仓库 Settings → Secrets 里加 `TEAM_ID`、`CERT_P12_BASE64`、`PROVISION_PROFILE_BASE64`、`P12_PASSWORD`，再把 workflow 的构建步骤换成 `scripts/build_ipa.sh signed` 分支（脚本已支持）。
