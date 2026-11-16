import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ 1) Models：支持短链（163cn.tv / c6.y.qq.com/u 等）跳转后识别 ============
m = os.path.join(root, "CarPlayer", "Models.swift")
t = io.open(m, encoding="utf-8").read()

anchor = """    private static func firstID(in text: String, pattern: String) -> String? {"""
addition = """    /// 短链识别：先按原文匹配，不行就跟随 302 跳转，再按跳转后的网址识别
    static func resolve(_ text: String) async -> (PlaylistImportPlatform, String)? {
        if let hit = detect(text) { return hit }
        guard let urlString = firstURL(in: text), let url = URL(string: urlString) else { return nil }
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        guard let (data, response) = try? await URLSession.shared.data(for: request) else { return nil }
        if let final = response.url?.absoluteString, let hit = detect(final) { return hit }
        // 仍不行：从落地页 HTML 里抠 playlist id
        if let html = String(data: data, encoding: .utf8),
           let id = firstID(in: html, pattern: #"playlist[^"'\\s]*?[?&]id=(\\d{6,})"#) {
            return (.wy, id)
        }
        if let final = response.url?.absoluteString,
           let id = firstID(in: final, pattern: #"[?&]id=(\\d{6,})"#) {
            return (final.contains("y.qq.com") ? .tx : .wy, id)
        }
        return nil
    }

    private static func firstURL(in text: String) -> String? {
        guard let range = text.range(of: #"https?://[^\\s"'<>]+"#, options: .regularExpression) else { return nil }
        return String(text[range])
    }

""" + anchor
assert anchor in t, "detect anchor missing"
t = t.replace(anchor, addition)
io.open(m, "w", encoding="utf-8").write(t)
print("Models: short-link resolver added")

# ============ 2) SettingsView：导入歌单用异步识别 ============
p = os.path.join(root, "CarPlayer", "SettingsView.swift")
s = io.open(p, encoding="utf-8").read()

old = """        guard let (platform, id) = PlaylistImportPlatform.detect(text) else {
            sheetStatus = "没识别到歌单 ID：支持 y.qq.com/…/playlist/<id> 或 music.163.com/playlist?id=<id>"
            store.show("未识别到歌单 ID")
            return
        }
        busy = true
        sheetStatus = "正在导入歌单…"
        store.show("正在导入歌单…")
        Task { @MainActor in
            defer { busy = false }
            var result = try? await PlaylistImporter.fetch(platform: platform, id: id)"""
new = """        busy = true
        sheetStatus = "正在识别歌单链接…"
        store.show("正在识别歌单链接…")
        Task { @MainActor in
            defer { busy = false }
            guard let (platform, id) = await PlaylistImportPlatform.resolve(text) else {
                sheetStatus = "没识别到歌单 ID：支持 163cn.tv 短链、music.163.com/playlist?id=…、y.qq.com/…/playlist/…"
                store.show("未识别到歌单 ID")
                return
            }
            sheetStatus = "正在导入歌单…"
            store.show("正在导入歌单…")
            var result = try? await PlaylistImporter.fetch(platform: platform, id: id)"""
assert old in s, "import anchor missing"
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("SettingsView: async resolve in importPlaylist")
