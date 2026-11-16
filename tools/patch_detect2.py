import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
m = os.path.join(root, "CarPlayer", "Models.swift")
t = io.open(m, encoding="utf-8").read()

start = t.index("    /// 从链接/分享文本里解析歌单 ID（兼容路径式、query 式、纯数字）")
end = t.index("    /// 短链识别：先按原文匹配，不行就跟随 302 跳转，再按跳转后的网址识别")
new = '''    /// 从链接/分享文本里解析歌单 ID（兼容路径式、query 式、短链、纯数字）
    static func detect(_ text: String) -> (PlaylistImportPlatform, String)? {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return nil }

        let lower = t.lowercased()
        // 1) QQ 音乐
        if lower.contains("qq.com") {
            if let id = firstID(in: t, pattern: #"playlist/(\\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: t, pattern: #"[?&](?:id|disstid|songlistid)=(\\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: t, pattern: #"(?:disstid|songlistid)=(\\d{4,})"#) { return (.tx, id) }
        }
        // 2) 网易云（含 y.music.163.com、music.163.com/…、163cn.tv 短链）
        if lower.contains("163.com") || lower.contains("163cn.tv") {
            if let id = firstID(in: t, pattern: #"/playlist/(\\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: t, pattern: #"[?&]id=(\\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: t, pattern: #"playlist[^\\s]*?id=(\\d{4,})"#) { return (.wy, id) }
        }
        // 3) 纯数字：先按网易试，失败由上层退回 QQ
        if t.count >= 4, t.allSatisfy({ $0.isNumber }) { return (.wy, t) }
        return nil
    }

'''
t = t[:start] + new + t[end:]
io.open(m, "w", encoding="utf-8").write(t)
print("Models: detect() rewritten with host split + safe id boundary")
