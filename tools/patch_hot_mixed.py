import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ 1) BuiltinSources：网易 + QQ 热门歌单混排 ============
b = os.path.join(root, "CarPlayer", "BuiltinSources.swift")
t = io.open(b, encoding="utf-8").read()

start = t.index("    // MARK: - 网易云热门歌单 / 歌单详情")
end = t.index("    private func get(_ urlString: String, referer: String? = nil) async throws -> Data {")
new = '''    // MARK: - 热门歌单（网易云 + QQ 混排）
    func hotPlaylists(limit: Int = 20) async throws -> [Playlist] {
        async let wy = wyHotPlaylists(limit: limit / 2 + 1)
        async let tx = qqHotPlaylists(limit: limit / 2 + 1)
        let (wyList, txList) = await (wy, tx)
        var merged: [Playlist] = []
        for i in 0..<max(wyList.count, txList.count) {
            if i < wyList.count { merged.append(wyList[i]) }
            if i < txList.count { merged.append(txList[i]) }
        }
        if merged.isEmpty { throw SourceError.parse }
        return Array(merged.prefix(limit))
    }

    private func wyHotPlaylists(limit: Int) async -> [Playlist] {
        let data = try? await get("https://music.163.com/api/personalized/playlist?limit=\\(limit)",
                                  referer: "https://music.163.com/")
        guard let data,
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let list = dict["result"] as? [[String: Any]] else { return [] }
        return list.compactMap { item in
            guard let id = item["id"].map({ "\\($0)" }) else { return nil }
            var cover = item["coverImgUrl"] as? String ?? item["picUrl"] as? String ?? ""
            if cover.isEmpty, let creator = item["creator"] as? [String: Any] {
                cover = creator["avatarUrl"] as? String ?? ""
            }
            return Playlist(id: "wy-\\(id)",
                            name: item["name"] as? String ?? "热门歌单",
                            songs: [],
                            picUrl: cover.isEmpty ? nil : cover,
                            source: .wy,
                            isRemote: true,
                            trackCount: item["trackCount"] as? Int ?? 0)
        }
    }

    /// QQ 歌单广场（Android 用的是同一套 fcg 接口）
    private func qqHotPlaylists(limit: Int) async -> [Playlist] {
        let raw = "https://c.y.qq.com/splcloud/fcgi-bin/fcg_get_diss_by_tag.fcg?picmid=1&rnd=0.5&g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&categoryId=10000000&sortId=5&sin=0&ein=\\(max(limit - 1, 0))"
        guard let data = try? await get(raw, referer: "https://y.qq.com/"),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let dataDict = dict["data"] as? [String: Any],
              let list = dataDict["list"] as? [[String: Any]] else { return [] }
        return list.compactMap { item in
            guard let dissid = item["dissid"].map({ "\\($0)" }) else { return nil }
            var cover = item["imgurl"] as? String ?? ""
            if cover.hasPrefix("http://") {
                cover = "https://" + cover.dropFirst("http://".count)
            }
            return Playlist(id: "tx-\\(dissid)",
                            name: item["dissname"] as? String ?? "QQ 歌单",
                            songs: [],
                            picUrl: cover.isEmpty ? nil : cover,
                            source: .tx,
                            isRemote: true,
                            trackCount: 0)
        }
    }

'''
t = t[:start] + new + t[end:]
io.open(b, "w", encoding="utf-8").write(t)
print("BuiltinSources: hot playlists wy+qq")

# ============ 2) AppStore：openHotPlaylist 用全量导入，且不再自动播放 ============
a = os.path.join(root, "CarPlayer", "AppStore.swift")
s = io.open(a, encoding="utf-8").read()
start = s.index("    /// 点热门歌单：拉曲目 → 立即播放 → 返回可展示的 Playlist")
end = s.index("    func shuffleHot() {")
new = '''    /// 点热门歌单：拉全量曲目 → 写入歌单 → 返回可展示的 Playlist（不自动播放）
    func openHotPlaylist(_ playlist: Playlist) async -> Playlist? {
        let platform: PlaylistImportPlatform = playlist.source == .tx ? .tx : .wy
        let rawId: String
        if playlist.id.hasPrefix("wy-") { rawId = String(playlist.id.dropFirst(3)) }
        else if playlist.id.hasPrefix("tx-") { rawId = String(playlist.id.dropFirst(3)) }
        else { rawId = playlist.id }

        guard let imported = try? await PlaylistImporter.fetch(platform: platform, id: rawId),
              !imported.songs.isEmpty else {
            show("这个歌单没取到歌，换一个试试")
            return nil
        }
        var full = playlist
        full.songs = imported.songs
        full.trackCount = imported.songs.count
        if let cover = imported.cover, !cover.isEmpty { full.picUrl = cover }
        full.name = imported.name
        replacePlaylist(full)
        show("已加载「\\(full.name)」· \\(imported.songs.count) 首")
        return full
    }

'''
s = s[:start] + new + s[end:]
io.open(a, "w", encoding="utf-8").write(s)
print("AppStore: openHotPlaylist full import, no autoplay")

# ============ 3) HomeView：点歌单只展开列表 ============
h = os.path.join(root, "CarPlayer", "HomeView.swift")
x = io.open(h, encoding="utf-8").read()
old_tap = """                            PlaylistCardView(playlist: playlist) {
                                Task { @MainActor in
                                    if let full = await store.openHotPlaylist(playlist) {
                                        router.screen = .playlist(full.id)
                                    }
                                }
                            }"""
new_tap = """                            PlaylistCardView(playlist: playlist) {
                                Task { @MainActor in
                                    if let full = await store.openHotPlaylist(playlist) {
                                        router.screen = .playlist(full.id)
                                    }
                                }
                            }"""
assert old_tap in x
# 文案同步：点封面展开列表（不再“播放”）
x = x.replace("""            Text("网易云歌单 · 点封面播放并展开列表")""",
              """            Text("网易云 + 小Q源 · 点封面展开歌单列表")""")
io.open(h, "w", encoding="utf-8").write(x)
print("HomeView: copy updated")

# ============ 4) 卡片：曲目数未知时只显示来源 ============
c = os.path.join(root, "CarPlayer", "Components.swift")
k = io.open(c, encoding="utf-8").read()
old_sub = """            Text(playlist.isRemote
                 ? "\\(playlist.source.display) · \\(playlist.count) 首"
                 : "\\(playlist.count) 首")"""
new_sub = """            Text(playlist.isRemote
                 ? (playlist.count > 0
                    ? "\\(playlist.source.display) · \\(playlist.count) 首"
                    : "\\(playlist.source.display) 歌单")
                 : "\\(playlist.count) 首")"""
assert old_sub in k
k = k.replace(old_sub, new_sub)
io.open(c, "w", encoding="utf-8").write(k)
print("Components: card subtitle handles unknown count")
