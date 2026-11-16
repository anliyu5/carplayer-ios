import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
p = os.path.join(root, "docs", "GITHUB.md")
t = io.open(p, encoding="utf-8").read()
t = t.replace("4. `workflow_dispatch` 触发 `.github/workflows/ios-build.yml`（macos-14，免签名编译）；",
              "4. `workflow_dispatch` 触发 `.github/workflows/ios-build.yml`（`macos-15-intel`，免签名编译；macos-14 在该账号下报 configuration not supported，macos-13 已退役）；")
t = t.replace("公共仓库的 Actions 免费额度不限（私有仓库 macOS 每分钟按 10 倍折算）。",
              "公共仓库的 Actions 免费额度不限（私有仓库 macOS 每分钟按 10 倍折算）。实测：一次出包约 2 分半，产物 1.01 MB。")
io.open(p, "w", encoding="utf-8").write(t)
print("GITHUB.md ok")
