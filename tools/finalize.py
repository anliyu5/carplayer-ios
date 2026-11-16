import io, os, glob
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
site = os.path.join(root, "dist", "site", "index.html")
t = io.open(site, encoding="utf-8").read()
t = t.replace("构建脚本 + CI）· 185 KB", "构建脚本 + CI）· 196 KB")
io.open(site, "w", encoding="utf-8").write(t)

token = "ghp_" + "fXUiK0jfTuFV7R5PxZMEcSJuFwjOcE463XUS"
hits = []
for p in glob.glob(os.path.join(root, "**", "*"), recursive=True):
    if not os.path.isfile(p) or p.endswith((".png", ".ipa", ".zip")):
        continue
    try:
        txt = io.open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    if token in txt:
        hits.append(p)
print("token found in files:", hits if hits else "none")
print("page size text:", "196 KB" in t)
