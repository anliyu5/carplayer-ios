import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ---------- A) Models：小Q源排最前 ----------
m = os.path.join(root, "CarPlayer", "Models.swift")
t = io.open(m, encoding="utf-8").read()
t = t.replace("static let searchOrder: [SourceId] = [.kw, .wy, .tx, .mg, .kg]",
              "static let searchOrder: [SourceId] = [.tx, .kw, .wy, .mg, .kg]   // 小Q源排最前")
io.open(m, "w", encoding="utf-8").write(t)
print("Models: searchOrder tx-first")

# ---------- B) BuiltinSources：歌词 + 网易云歌单 ----------
b = os.path.join(root, "CarPlayer", "BuiltinSources.swift")
s = io.open(b, encoding="utf-8").read()

old_lyric = s[s.index("    func lyric(song: Song) async throws -> String? {"):]
old_lyric = old_lyric[:old_lyric.index("\n    }\n") + len("\n    }\n")]
new_lyric = '''    /// 歌词：按平台取（酷我 / 网易 / 酷狗 / QQ），失败再按同名歌去网易捞一次
    func lyric(song: Song) async throws -> String? {
        if let template = book.lyric[song.source.rawValue] {
            let data = try await get(fill(template, ["id": song.id]))
            if let text = extractLyric(from: data) { return text }
        }
        switch song.source {
        case .wy:
            if let text = try? await neteaseLyric(id: song.id) { return text }
        case .kw:
            if let text = try? await kuwoLyric(rid: song.extra["rid"] ?? song.id) { return text }
        case .kg:
            if let text = try? await kugouLyric(hash: song.id) { return text }
        case .tx:
            if let text = try? await qqLyric(mid: song.extra["mid"] ?? song.id) { return text }
        default:
            break
        }
        // 兜底：同名歌去网易找（很多 QQ/咪咕曲目在网易有同名歌词）
        if song.source != .wy,
           let list = try? await search(source: .wy, keyword: "\\(song.name) \\(song.displaySinger)"),
           let hit = list.first, let text = try? await neteaseLyric(id: hit.id) {
            return text
        }
        return nil
    }

    private func neteaseLyric(id: String) async throws -> String? {
        let data = try await get("https://interface3.music.163.com/api/song/lyric?id=\\(id)&lv=1&kv=0&tv=-1",
                                 referer: "https://music.163.com/")
        return extractLyric(from: data)
    }

    private func kuwoLyric(rid: String) async throws -> String? {
        let data = try await get("https://wapi.kuwo.cn/openapi/v1/www/lyric/getlyric?musicId=\\(rid)",
                                 referer: "https://www.kuwo.cn/")
        return extractLyric(from: data)
    }

    private func kugouLyric(hash: String) async throws -> String? {
        let millis = Int(Date().timeIntervalSince1970 * 1000)
        let data = try await get("https://m3ws.kugou.com/api/v1/krc/get_lyrics?clienttime=\\(millis)&hash=\\(hash)",
                                 referer: "https://www.kugou.com/")
        return extractLyric(from: data)
    }

    private func qqLyric(mid: String) async throws -> String? {
        let data = try await get("https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?songmid=\\(mid)&format=json&nobase64=1",
                                 referer: "https://y.qq.com/")
        return extractLyric(from: data)
    }

    /// 从任意结构里找 LRC 文本
    private func extractLyric(from data: Data) -> String? {
        if let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            if let lrc = dict["lrc"] as? [String: Any], let lyric = lrc["lyric"] as? String, !lyric.isEmpty {
                return lyric
            }
            for key in ["lyric", "lrc", "krc", "content", "text"] {
                if let value = dict[key] as? String, value.contains("[") { return value }
            }
            if let inner = dict["data"] as? [String: Any] {
                for key in ["lyric", "lrc", "content"] {
                    if let value = inner[key] as? String, value.contains("[") { return value }
                }
            }
        }
        if let text = String(data: data, encoding: .utf8), text.contains("[") { return text }
        return nil
    }

    // MARK: - 网易云热门歌单 / 歌单详情
    func hotPlaylists(limit: Int = 12) async throws -> [Playlist] {
        let data = try await get("https://music.163.com/api/personalized/playlist?limit=\\(limit)",
                                 referer: "https://music.163.com/")
        guard let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let list = dict["result"] as? [[String: Any]] else { return [] }
        return list.compactMap { item in
            guard let id = item["id"].map({ "\\($0)" }) else { return nil }
            let name = item["name"] as? String ?? "热门歌单"
            var cover = item["coverImgUrl"] as? String ?? item["picUrl"] as? String ?? ""
            if cover.isEmpty, let creator = item["creator"] as? [String: Any] {
                cover = creator["avatarUrl"] as? String ?? ""
            }
            let count = item["trackCount"] as? Int ?? 0
            return Playlist(id: "wy-\\(id)", name: name, songs: [],
                            picUrl: cover.isEmpty ? nil : cover, source: .wy,
                            isRemote: true, trackCount: count)
        }
    }

    /// 网易云歌单详情（返回歌曲）
    func wyPlaylistSongs(id: String) async throws -> [Song] {
        let data = try await get("https://music.163.com/api/v6/playlist/detail?id=\\(id)&n=1000",
                                 referer: "https://music.163.com/")
        guard let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let playlist = dict["playlist"] as? [String: Any],
              let tracks = playlist["tracks"] as? [[String: Any]] else { return [] }
        return tracks.compactMap { item in
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
    }
'''
s = s.replace(old_lyric, new_lyric)
io.open(b, "w", encoding="utf-8").write(s)
print("BuiltinSources: lyrics + hot playlists")
