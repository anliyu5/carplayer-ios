import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "AppStore.swift")
t = io.open(p, encoding="utf-8").read()
start = t.find("    private func engineSearch(_ keyword: String) async -> [Song]? {")
if start >= 0:
    end = t.index("\n    }\n", start) + len("\n    }\n")
    t = t[:start] + t[end:]
    io.open(p, "w", encoding="utf-8").write(t)
    print("engineSearch removed")
else:
    print("engineSearch not found")

# 全工程检查是否还有引用已删除 API
import glob
missing = []
for f in glob.glob(os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "*.swift")):
    src = io.open(f, encoding="utf-8").read()
    for api in ["QingGate.search(", "engineSearch("]:
        if api in src:
            missing.append((os.path.basename(f), api))
print("stale refs:", missing if missing else "none")
