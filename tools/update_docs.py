import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
readme = os.path.join(root, "README.md")
text = io.open(readme, encoding="utf-8").read()

old = """### 2.2 没有 Mac

把仓库推到 GitHub → Actions → `iOS Build (unsigned ipa)` → Run workflow，
产物在 Artifact：`CarPlayer-unsigned-ipa`（`CarPlayer-1.9.14-unsigned.ipa`）。"""

new = """### 2.2 没有 Mac（已跑通，ipa 已产出）

仓库：https://github.com/anliyu5/carplayer-ios

```powershell
$env:GH_TOKEN = "你的token"
python tools\\push_github.py --public   # 建库 + 推送 + 触发编译 + 抓回 ipa + 更新下载页
python tools\\fetch_ipa.py              # 只重新下载最新一次成功构建的 ipa
```

Runner 实测（2026-11）：

| label | 结果 |
|---|---|
| `macos-14` | 立即 cancelled：`configuration 'macos-14-arm64-us-default' is not supported` |
| `macos-13` | 一直 queued 不出机（镜像已退役） |
| `macos-15-intel` | 可用：macOS 15.6 + Xcode 16.4，编译约 2 分半 |
| `macos-15` | 可用（arm64 宿主，出包同样可用） |

产物：`dist/CarPlayer-1.9.14-unsigned.ipa`（1.01 MB，`Payload/CarPlayer.app` 内含 2.7 MB arm64 主二进制）。"""

assert old in text, "anchor not found"
text = text.replace(old, new)
text = text.replace(
    "- 最低系统：iOS 16.0（SwiftUI + AVFoundation + JavaScriptCore）",
    "- 最低系统：iOS 16.0（SwiftUI + AVFoundation + JavaScriptCore）\n- 已验证编译：GitHub Actions `macos-15-intel` + Xcode 16.4，产出 `CarPlayer-1.9.14-unsigned.ipa`")
text = text.replace(
    "├── tools/gen_project.py           # 工程文件生成器（新增 Swift 文件后重跑即可）",
    "├── tools/gen_project.py           # 工程文件生成器（新增 Swift 文件后重跑即可）\n├── tools/push_github.py           # 建库+推送+触发 CI+抓 ipa（不需要本机 git）\n├── tools/fetch_ipa.py             # 重新下载最新构建产物\ndocs/GITHUB.md                     # 无 Mac 出包全流程")
io.open(readme, "w", encoding="utf-8").write(text)
print("README ok,", len(text), "chars")
