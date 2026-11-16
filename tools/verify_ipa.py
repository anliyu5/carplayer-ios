import zipfile, os
p = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\dist\CarPlayer-1.9.14-unsigned.ipa"
print("size", os.path.getsize(p))
z = zipfile.ZipFile(p)
names = z.namelist()
print("entries", len(names))
top = sorted({n.split("/")[0] for n in names})
print("top:", top)
app = [n for n in names if n.endswith(".app/") or n.count("/")==2]
print("app files (first 20):")
for n in [x for x in names if x.startswith("Payload/")][:20]: print("  ", n)
info = [n for n in names if n.endswith("Payload/CarPlayer.app/Info.plist")]
print("Info.plist present:", bool(info))
exe = [n for n in names if n.endswith("Payload/CarPlayer.app/CarPlayer")]
print("binary present:", bool(exe), (z.getinfo(exe[0]).file_size if exe else 0))
# 关键资源
for k in ["lx-runtime.js","Assets.car","AppIcon"]:
    hits=[n for n in names if k in n]
    print(f"{k}:", hits[:2])
