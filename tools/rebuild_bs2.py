import io
p = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\CarPlayer\BuiltinSources.swift"
lines = io.open(p, encoding="utf-8").read().split("\n")
# 保留 1..477（新代码），再从 "enum SourceError" 起接上尾部
cut = next(i for i, l in enumerate(lines) if l.startswith("enum SourceError"))
head = lines[:477]
tail = lines[cut:]
out = "\n".join(head + tail)
io.open(p, "w", encoding="utf-8").write(out)
print("rebuilt lines:", len(out.split("\n")))
for k in ["private func get(_ urlString", "private func fill(", "func search(source", "func hotChart(", "func lyric(song", "func hotPlaylists(", "private func qqHotPlaylists", "static func qqSongCount", "enum SourceError", "enum KwTextParser"]:
    print(f"  {k}: {out.count(k)}")
