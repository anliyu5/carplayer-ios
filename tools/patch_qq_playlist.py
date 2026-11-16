import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ 1) Models：歌单 ID 识别重写（支持 QQ 的 /playlist/<id>、id=、disstid=） ============
m = os.path.join(root, "CarPlayer", "Models.swift")
t = io.open(m, encoding="utf-8").read()
start = t.index("/// 歌单导入用的平台")
new_block = '''/// 歌单导入用的平台
enum PlaylistImportPlatform: String {
    case wy, tx
    var display: String { self == .wy ? "网易云歌单" : "QQ 歌单" }

    /// 从链接/分享文本里解析歌单 ID（兼容路径式、query 式、纯数字）
    static func detect(_ text: String) -> (PlaylistImportPlatform, String)? {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return nil }

        // QQ：y.qq.com/n/ryqq/playlist/7944390462 、?id=xxx 、disstid=xxx
        if let id = firstID(in: t, pattern: #"y\\.qq\\.com[^\\s]*(?:playlist/|id=|disstid=)(\\d{4,})"#) {
            return (.tx, id)
        }
        if let id = firstID(in: t, pattern: #"(?:disstid|songlistid)=(\\d{4,})"#) {
            return (.tx, id)
        }
        // 网易云：music.163.com/playlist?id=xxx 、/playlist/xxx 、#/playlist?id=xxx
        if let id = firstID(in: t, pattern: #"music\\.163\\.com[^\\s]*(?:playlist[/?#]|id=)(\\d{4,})"#) {
            return (.wy, id)
        }
        // 纯数字：先按网易试，失败再由上层退回 QQ
        if t.count >= 4, t.allSatisfy({ $0.isNumber }) {
            return (.wy, t)
        }
        return nil
    }

    private static func firstID(in text: String, pattern: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let ns = text as NSString
        guard let match = regex.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)),
              match.numberOfRanges >= 2 else { return nil }
        let range = match.range(at: 1)
        guard range.location != NSNotFound else { return nil }
        return ns.substring(with: range)
    }
}
'''
t = t[:start] + new_block
io.open(m, "w", encoding="utf-8").write(t)
print("Models: playlist detect rewritten")

# ============ 2) SettingsView：导入歌单（QQ 接口 + 内联状态 + 纯数字回退） ============
p = os.path.join(root, "CarPlayer", "SettingsView.swift")
s = io.open(p, encoding="utf-8").read()

# 2.1 新增内联状态
s = s.replace("    @State private var busy = false",
              "    @State private var busy = false\n    @State private var sheetStatus: String?")

# 2.2 importPlaylist 重写
start = s.index("    private func importPlaylist() {")
end = s.index("\n    }\n", start) + len("\n    }\n")
new_import = '''    private func importPlaylist() {
        let text = playlistText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            sheetStatus = "请粘贴歌单链接或 ID"
            store.show("请粘贴歌单链接或 ID")
            return
        }
        guard let (platform, id) = PlaylistImportPlatform.detect(text) else {
            sheetStatus = "没识别到歌单 ID：支持 y.qq.com/…/playlist/<id> 或 music.163.com/playlist?id=<id>"
            store.show("未识别到歌单 ID")
            return
        }
        busy = true
        sheetStatus = "正在导入歌单…"
        store.show("正在导入歌单…")
        Task { @MainActor in
            defer { busy = false }
            var result = try? await PlaylistImporter.fetch(platform: platform, id: id)
            // 纯数字时平台可能猜错：另一个平台再试一次
            if result == nil {
                let other: PlaylistImportPlatform = platform == .wy ? .tx : .wy
                result = try? await PlaylistImporter.fetch(platform: other, id: id)
            }
            guard let imported = result, !imported.songs.isEmpty else {
                sheetStatus = "歌单取不到歌曲：可能不存在、为空、或需要登录"
                store.show("歌单不存在、为空或需要登录")
                return
            }
            let playlist = Playlist(id: "\\(platform.rawValue)-\\(id)",
                                    name: imported.name,
                                    songs: imported.songs,
                                    picUrl: imported.cover,
                                    source: platform == .wy ? .wy : .tx,
                                    isRemote: true,
                                    trackCount: imported.songs.count)
            store.replacePlaylist(playlist)
            sheetStatus = "已导入「\\(imported.name)」· \\(imported.songs.count) 首"
            store.show("已导入「\\(imported.name)」· \\(imported.songs.count) 首")
            activeSheet = nil
        }
    }
'''
s = s[:start] + new_import + s[end:]

# 2.3 PlaylistImporter 重写（QQ 走 fcg_ucc，网易走 v6）
start = s.index("/// 歌单导入（网易云 / QQ 公开歌单）")
new_importer = '''/// 歌单导入（网易云 / QQ 公开歌单）
struct ImportedPlaylist {
    var name: String
    var cover: String?
    var songs: [Song]
}

enum PlaylistImporter {
    static func fetch(platform: PlaylistImportPlatform, id: String) async throws -> ImportedPlaylist? {
        switch platform {
        case .wy:
            let url = URL(string: "https://music.163.com/api/v6/playlist/detail?id=\\(id)&n=1000&s=0")!
            var request = URLRequest(url: url, timeoutInterval: 20)
            request.setValue("https://music.163.com/", forHTTPHeaderField: "Referer")
            request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
            guard let (data, _) = try? await URLSession.shared.data(for: request),
                  let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let playlist = dict["playlist"] as? [String: Any],
                  let tracks = playlist["tracks"] as? [[String: Any]] else { return nil }
            let songs: [Song] = tracks.compactMap { item in
                guard let sid = item["id"].map({ "\\($0)" }) else { return nil }
                let artists = (item["ar"] as? [[String: Any]])?.compactMap { $0["name"] as? String }
                    ?? (item["artists"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                let album = (item["al"] as? [String: Any]) ?? (item["album"] as? [String: Any])
                return Song(id: sid, source: .wy,
                            name: item["name"] as? String ?? "",
                            singer: artists.joined(separator: "/"),
                            albumName: album?["name"] as? String,
                            picUrl: album?["picUrl"] as? String,
                            interval: Double(item["dt"] as? Int ?? item["duration"] as? Int ?? 0) / 1000,
                            qualitys: [.k128, .k320, .flac, .hires])
            }
            let name = playlist["name"] as? String ?? "网易云歌单 \\(id)"
            let cover = playlist["coverImgUrl"] as? String
            return ImportedPlaylist(name: name, cover: cover, songs: songs)

        case .tx:
            // 就是 Android 用的同一个接口：fcg_ucc_getcdinfo_byids_cp.fcg
            let raw = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?type=1&json=1&utf8=1&onlysong=0&disstid=\\(id)&format=json&g_tk=5381"
            guard let url = URL(string: raw) else { return nil }
            var request = URLRequest(url: url, timeoutInterval: 20)
            request.setValue("https://y.qq.com/", forHTTPHeaderField: "Referer")
            request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
            guard let (data, _) = try? await URLSession.shared.data(for: request),
                  let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let cdlist = dict["cdlist"] as? [[String: Any]],
                  let cd = cdlist.first,
                  let list = cd["songlist"] as? [[String: Any]] else { return nil }
            let songs: [Song] = list.compactMap { item in
                let mid = item["songmid"] as? String ?? item["mid"] as? String ?? ""
                guard !mid.isEmpty else { return nil }
                let singers = (item["singer"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                let albumMid = item["albummid"] as? String
                return Song(id: mid, source: .tx,
                            name: item["songname"] as? String ?? item["name"] as? String ?? "",
                            singer: singers.joined(separator: "/"),
                            albumName: item["albumname"] as? String,
                            picUrl: albumMid.flatMap { "https://y.qq.com/music/photo_new/T002R300x300M000\\($0).jpg" },
                            interval: Double(item["interval"] as? Int ?? 0),
                            qualitys: [.k128, .k320, .flac],
                            extra: ["mid": mid])
            }
            let name = cd["dissname"] as? String ?? "QQ 歌单 \\(id)"
            let cover = cd["logo"] as? String
            return ImportedPlaylist(name: name, cover: cover, songs: songs)
        }
    }
}
'''
s = s[:start] + new_importer
io.open(p, "w", encoding="utf-8").write(s)
print("SettingsView: QQ playlist import rewritten")

# 2.4 两个弹窗都显示内联状态
s = io.open(p, encoding="utf-8").read()
s = s.replace('''        .safeAreaInset(edge: .bottom) {
            Button(action: importScript) {''',
'''        .safeAreaInset(edge: .bottom) {
            VStack(spacing: 8) {
                if let sheetStatus {
                    Text(sheetStatus)
                        .font(FType.subSm())
                        .foregroundColor(sheetStatus.hasPrefix("已导入") ? Palette.accent : Palette.danger)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: .infinity)
                }
                Button(action: importScript) {''')
s = s.replace('''            .buttonStyle(.borderless)
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

    private var playlistImportSheet: some View {''',
'''                .buttonStyle(.borderless)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

    private var playlistImportSheet: some View {''')

s = s.replace('''        .safeAreaInset(edge: .bottom) {
            Button(action: importPlaylist) {''',
'''        .safeAreaInset(edge: .bottom) {
            VStack(spacing: 8) {
                if let sheetStatus {
                    Text(sheetStatus)
                        .font(FType.subSm())
                        .foregroundColor(sheetStatus.hasPrefix("已导入") ? Palette.accent : Palette.danger)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: .infinity)
                }
                Button(action: importPlaylist) {''')
s = s.replace('''            .buttonStyle(.borderless)
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

    private var helpSheet: some View {''',
'''                .buttonStyle(.borderless)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

    private var helpSheet: some View {''')
io.open(p, "w", encoding="utf-8").write(s)
print("SettingsView: inline status in sheets")
