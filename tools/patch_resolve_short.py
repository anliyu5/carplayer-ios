import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
m = os.path.join(root, "CarPlayer", "Models.swift")
t = io.open(m, encoding="utf-8").read()

start = t.index("    /// 短链识别：先按原文匹配，不行就跟随 302 跳转，再按跳转后的网址识别")
end = t.index("    private static func firstURL(in text: String) -> String? {")
new = '''    /// 短链识别：先按原文匹配，不行就跟随 302 跳转，再按跳转后的网址 / 落地页识别
    static func resolve(_ text: String) async -> (PlaylistImportPlatform, String)? {
        if let hit = detect(text) { return hit }
        guard let urlString = firstURL(in: text), let url = URL(string: urlString) else { return nil }
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        guard let (data, response) = try? await URLSession.shared.data(for: request) else { return nil }
        let final = response.url?.absoluteString ?? ""
        if let hit = detect(final) { return hit }

        // 落地页里抠：网易 playlist?id=… / QQ playlist/<id>
        let html = String(data: data, encoding: .utf8) ?? ""
        if final.contains("qq.com") || urlString.contains("qq.com") {
            if let id = firstID(in: final, pattern: #"playlist/(\\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: html, pattern: #"playlist/(\\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: final, pattern: #"[?&]id=(\\d{4,})"#) { return (.tx, id) }
        } else {
            if let id = firstID(in: final, pattern: #"[?&]id=(\\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: html, pattern: #"playlist[^"'\\s]*?[?&]id=(\\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: html, pattern: #"[?&]id=(\\d{6,})"#) { return (.wy, id) }
        }
        return nil
    }

'''
t = t[:start] + new + t[end:]
io.open(m, "w", encoding="utf-8").write(t)
print("Models: resolve() host-aware fallbacks")
