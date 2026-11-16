import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
p = os.path.join(root, "CarPlayer", "Models.swift")
t = io.open(p, encoding="utf-8").read()
start = t.find("/// 青听网关音源配置（QingConfig / QingLine）")
end = t.find("/// 歌单导入用的平台")
assert start > 0 and end > start
t = t[:start] + t[end:]
io.open(p, "w", encoding="utf-8").write(t)
print("duplicate QingConfig removed from Models.swift; chars:", len(t))
print("  still has QingConfig:", "struct QingConfig" in t)

q = os.path.join(root, "CarPlayer", "AppStore.swift")
a = io.open(q, encoding="utf-8").read()
a = a.replace("        if let qing {\n            let list = qing.supportedSources",
              "        if let qing = self.qing {\n            let list = qing.supportedSources")
a = a.replace("        if let qing, let lrc = try? await QingGate.lyric(song: song, config: qing) {",
              "        if let qing = self.qing, let lrc = try? await QingGate.lyric(song: song, config: qing) {")
io.open(q, "w", encoding="utf-8").write(a)
print("AppStore shorthand bindings normalised")
