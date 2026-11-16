import io, re
p = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\CarPlayer\BuiltinSources.swift"
lines = io.open(p, encoding="utf-8").read().split("\n")
# 1..433 保留；434..796 是重复块；797 起是类结尾与工具类型
head = lines[:433]
tail = lines[796:]
out = "\n".join(head + tail)
io.open(p, "w", encoding="utf-8").write(out)
print("rebuilt lines:", len(out.split("\n")))
for name in ["private func get(_ urlString", "private func fill(", "func search(source", "func hotChart(", "func lyric(song", "func hotPlaylists(", "private func wyHotPlaylists", "private func qqHotPlaylists", "func wyPlaylistSongs", "private func extractLyric"]:
    print(f"  {name}: {out.count(name)}")
print("  class close count:", out.count("\n}\n"))
