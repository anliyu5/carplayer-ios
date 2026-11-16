import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ A) 搜索页返回加固 ============
p = os.path.join(root, "CarPlayer", "SearchView.swift")
t = io.open(p, encoding="utf-8").read()
old = """            Button {
                router.screen = .main
            } label: {
                VectorIcon(icon: .close, size: 20, color: Palette.text)
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("关闭搜索")"""
new = """            Button {
                router.screen = .main
            } label: {
                VectorIcon(icon: .close, size: 20, color: Palette.text)
                    .frame(width: 64, height: 56)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("关闭搜索")"""
assert old in t, "search back anchor"
t = t.replace(old, new)
t = t.replace("""        .padding(.horizontal, 20)
        .background(Palette.bg.ignoresSafeArea())""",
"""        .padding(.horizontal, 20)
        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            Color.clear
                .frame(width: 76, height: 56)
                .contentShape(Rectangle())
                .onTapGesture { router.screen = .main }
        }""")
io.open(p, "w", encoding="utf-8").write(t)
print("SearchView: back hardened")

# ============ B) 网易云歌单：用 trackIds 拉全量（不再只有 10 首） ============
s = os.path.join(root, "CarPlayer", "SettingsView.swift")
v = io.open(s, encoding="utf-8").read()

old_wy = """            guard let (data, _) = try? await URLSession.shared.data(for: request),
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
            return ImportedPlaylist(name: name, cover: cover, songs: songs)"""

new_wy = """            guard let (data, _) = try? await URLSession.shared.data(for: request),
                  let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let playlist = dict["playlist"] as? [String: Any] else { return nil }

            let name = playlist["name"] as? String ?? "网易云歌单 \\(id)"
            let cover = playlist["coverImgUrl"] as? String
            let partial = playlist["tracks"] as? [[String: Any]] ?? []
            let trackIds = (playlist["trackIds"] as? [[String: Any]])?.compactMap { $0["id"].map { "\\($0)" } } ?? []

            var songs = partial.compactMap(Self.wySong(from:))
            // v6 详情只给前 10 首；用 trackIds + 批量详情补齐全部
            if trackIds.count > songs.count {
                var details: [String: Song] = [:]
                for song in songs { details[song.id] = song }
                var missing = trackIds.filter { details[$0] == nil }
                var guardCount = 0
                while !missing.isEmpty && guardCount < 20 {
                    guardCount += 1
                    let chunk = Array(missing.prefix(100))
                    missing.removeFirst(min(100, missing.count))
                    for song in await Self.wySongDetails(ids: chunk) {
                        details[song.id] = song
                    }
                }
                let ordered = trackIds.compactMap { details[$0] }
                if ordered.count > songs.count { songs = ordered }
            }
            return ImportedPlaylist(name: name, cover: cover, songs: songs)"""
assert old_wy in v, "wy importer anchor"
v = v.replace(old_wy, new_wy)

# 追加两个静态工具
anchor = """    static func fetch(platform: PlaylistImportPlatform, id: String) async throws -> ImportedPlaylist? {"""
helpers = """    /// 网易云单曲（兼容 al/ar 与 album/artists 两种字段）
    static func wySong(from item: [String: Any]) -> Song? {
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

    /// 批量取歌曲详情：/api/v3/song/detail?c=[{"id":…},…]
    static func wySongDetails(ids: [String]) async -> [Song] {
        guard !ids.isEmpty else { return [] }
        let json = "[" + ids.map { "{\\"id\\":\\($0)}" }.joined(separator: ",") + "]"
        guard var comps = URLComponents(string: "https://music.163.com/api/v3/song/detail") else { return [] }
        comps.queryItems = [URLQueryItem(name: "c", value: json)]
        guard let url = comps.url else { return [] }
        var request = URLRequest(url: url, timeoutInterval: 20)
        request.setValue("https://music.163.com/", forHTTPHeaderField: "Referer")
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        guard let (data, _) = try? await URLSession.shared.data(for: request),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let list = dict["songs"] as? [[String: Any]] else { return [] }
        return list.compactMap(wySong(from:))
    }

""" + anchor
assert anchor in v
v = v.replace(anchor, helpers)
io.open(s, "w", encoding="utf-8").write(v)
print("SettingsView: netease full track import")

# ============ C) 歌单删除 ============
# C1 资料库：远程歌单卡片右上角删除
lib = os.path.join(root, "CarPlayer", "LibraryView.swift")
l = io.open(lib, encoding="utf-8").read()
old_card = """                        ForEach(remote) { playlist in
                            PlaylistCardView(playlist: playlist) {
                                router.screen = .playlist(playlist.id)
                            }
                        }"""
new_card = """                        ForEach(remote) { playlist in
                            ZStack(alignment: .topTrailing) {
                                PlaylistCardView(playlist: playlist) {
                                    router.screen = .playlist(playlist.id)
                                }
                                Button {
                                    store.deletePlaylist(playlist)
                                } label: {
                                    VectorIcon(icon: .close, size: 13, color: Palette.text)
                                        .frame(width: 26, height: 26)
                                        .background(Circle().fill(Color.black.opacity(0.55)))
                                }
                                .buttonStyle(.borderless)
                                .padding(.top, 6)
                                .padding(.trailing, 20)
                                .accessibilityLabel("删除歌单")
                            }
                        }"""
assert old_card in l, "remote card anchor"
l = l.replace(old_card, new_card)

# C2 本地歌单行：⋮ 删除改为带确认的二次点击（直接删太危险）
l = l.replace("""    private func moreMenu(_ playlist: Playlist) {
        if playlist.isFavorite {
            store.show("收藏歌单不可删除")
        } else {
            store.deletePlaylist(playlist)
        }
    }""",
"""    private func moreMenu(_ playlist: Playlist) {
        guard !playlist.isFavorite else {
            store.show("收藏歌单不可删除")
            return
        }
        store.deletePlaylist(playlist)
        store.show("已删除「\\(playlist.name)」")
    }""")
io.open(lib, "w", encoding="utf-8").write(l)
print("LibraryView: remote playlist delete")

# C3 歌单详情页：右上角删除
pl = os.path.join(root, "CarPlayer", "PlaylistView.swift")
q = io.open(pl, encoding="utf-8").read()
old_header = """            NavHeader(title: playlist?.name ?? "歌单", trailing: AnyView(Spacer())) {
                router.screen = .main
            }"""
new_header = """            HStack(spacing: 6) {
                Button {
                    router.screen = .main
                } label: {
                    VectorIcon(icon: .back, size: 24, color: Palette.text)
                        .frame(width: 64, height: 56)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.borderless)
                Text(playlist?.name ?? "歌单")
                    .font(FType.h2())
                    .foregroundColor(Palette.text)
                    .lineLimit(1)
                Spacer(minLength: 0)
                if let playlist, !playlist.isFavorite {
                    Button {
                        store.deletePlaylist(playlist)
                        router.screen = .main
                    } label: {
                        VectorIcon(icon: .delete, size: 20, color: Palette.danger)
                            .frame(width: 56, height: 56)
                            .contentShape(Rectangle())
                    }
                    .buttonStyle(.borderless)
                    .accessibilityLabel("删除歌单")
                }
            }
            .frame(height: 64)
            .padding(.leading, 8)
            .padding(.trailing, 12)"""
assert old_header in q, "playlist header anchor"
q = q.replace(old_header, new_header)
io.open(pl, "w", encoding="utf-8").write(q)
print("PlaylistView: delete button in header")
