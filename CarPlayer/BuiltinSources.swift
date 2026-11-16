import Foundation

/// 内置搜索适配层（对应 Android com.carplayer.source.SourceEngine）
///
/// 说明：与 Android 版保持一致 —— 内置的只是「搜索 + 榜单」骨架，
/// 真正的播放地址解析走「自定义 lx 脚本」或「青听网关」，两者都在设置页导入。
/// 如果你在自己的部署里已经有一整套直连接口，把 EndpointBook 里的模板换成你的即可，
/// 解析代码不用动。
struct EndpointBook: Codable {
    var search: [String: String] = [
        "kw": "http://search.kuwo.cn/r.s?all={keyword}&ft=music&itemset=web_2013&client=kt&pn=0&rn=30&rformat=json&encoding=utf8",
        "wy": "https://interface.music.163.com/api/search/get?type=1&s={keyword}&limit=30&offset=0",
        "tx": "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={keyword}&format=json&n=30&p=1&cr=1&new_json=1",
        "mg": "https://app.c.nf.migu.cn/MIGUM2.0/v1.0/content/search_all.do?ua=Android_migu&version=5.0.1&text={keyword}&pageNo=1&pageSize=30&searchSwitch=%7B%22song%22%3A1%7D",
        "kg": "https://mobilecdn.kugou.com/api/v3/search/song?keyword={keyword}&page=1&pagesize=30&showtype=1"
    ]
    var chart: [String: String] = [
        "tx": "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?topid={TOPID}&format=json&page=detail&type=top&song_num=20",
        "kw": "https://www.kuwo.cn/api/pc/bang/bang?bangId={TOPID}",
        "wy": "https://music.163.com/api/playlist/detail?id=3778678"
    ]
    /// 直连解析（可选）：{id} / {quality} 占位
    var resolve: [String: String] = [:]
    var lyric: [String: String] = [:]

    static func load() -> EndpointBook {
        guard let data = UserDefaults.standard.data(forKey: "endpoint.book"),
              let book = try? JSONDecoder().decode(EndpointBook.self, from: data) else { return EndpointBook() }
        return book
    }

    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: "endpoint.book")
        }
    }
}

final class BuiltinSources {
    private let session: URLSession
    private let book = EndpointBook.load()

    init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 12
        config.httpAdditionalHeaders = [
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
            "Referer": "https://music.163.com/"
        ]
        session = URLSession(configuration: config)
    }

    private func get(_ urlString: String, referer: String? = nil) async throws -> Data {
        guard let url = URL(string: urlString) else { throw SourceError.badURL }
        var request = URLRequest(url: url)
        if let referer { request.setValue(referer, forHTTPHeaderField: "Referer") }
        let (data, _) = try await session.data(for: request)
        return data
    }

    private func fill(_ template: String, _ map: [String: String]) -> String {
        var out = template
        for (k, v) in map {
            out = out.replacingOccurrences(of: "{\(k)}", with: v.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? v)
        }
        return out
    }

    // MARK: - 搜索
    func search(source: SourceId, keyword: String) async throws -> [Song] {
        guard let template = book.search[source.rawValue] else { throw SourceError.unsupported }
        let referer: String?
        switch source {
        case .tx: referer = "https://y.qq.com/"
        case .wy: referer = "https://music.163.com/"
        case .mg: referer = "https://app.c.nf.migu.cn/"
        case .kw: referer = "https://www.kuwo.cn/"
        case .kg: referer = "https://www.kugou.com/"
        default: referer = nil
        }
        let data = try await get(fill(template, ["keyword": keyword]), referer: referer)
        return parseSearch(source: source, data: data)
    }

    private func parseSearch(source: SourceId, data: Data) -> [Song] {
        guard let obj = try? JSONSerialization.jsonObject(with: data) else { return [] }
        switch source {
        case .kw:
            if let dict = obj as? [String: Any], let abs = extractKw(dict) { return abs }
            if let text = String(data: data, encoding: .utf8) { return KwTextParser.parse(text) }
            return []
        case .wy:
            guard let dict = obj as? [String: Any],
                  let result = dict["result"] as? [String: Any],
                  let songs = result["songs"] as? [[String: Any]] else { return [] }
            return songs.map { item in
                let artists = (item["artists"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                let album = item["album"] as? [String: Any]
                return Song(id: String(item["id"] as? Int ?? 0),
                            source: .wy,
                            name: item["name"] as? String ?? "",
                            singer: artists.joined(separator: "/"),
                            albumName: album?["name"] as? String,
                            picUrl: album?["picUrl"] as? String,
                            interval: Double(item["duration"] as? Int ?? 0) / 1000,
                            qualitys: [.k128, .k320, .flac])
            }
        case .tx:
            guard let dict = obj as? [String: Any],
                  let dataDict = dict["data"] as? [String: Any],
                  let songDict = dataDict["song"] as? [String: Any],
                  let list = songDict["list"] as? [[String: Any]] else { return [] }
            return list.map { item in
                let singers = (item["singer"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                let album = item["album"] as? [String: Any]
                let mid = item["mid"] as? String ?? item["songmid"] as? String ?? ""
                let id = mid.isEmpty ? String(item["songid"] as? Int ?? 0) : mid
                return Song(id: id,
                            source: .tx,
                            name: item["title"] as? String ?? item["songname"] as? String ?? "",
                            singer: singers.joined(separator: "/"),
                            albumName: album?["name"] as? String ?? (album?["title"] as? String),
                            picUrl: album?["pmid"].flatMap { "https://y.gtimg.cn/music/photo_new/T002R300x300M000\($0).jpg" },
                            interval: Double(item["interval"] as? Int ?? 0),
                            qualitys: [.k128, .k320, .flac],
                            extra: ["mid": mid])
            }
        case .mg:
            guard let dict = obj as? [String: Any],
                  let songData = dict["songResultData"] as? [String: Any],
                  let list = songData["result"] as? [[String: Any]] else { return [] }
            return list.compactMap { item in
                var id = item["id"] as? String ?? ""
                if id.isEmpty { id = item["songId"] as? String ?? "" }
                guard !id.isEmpty else { return nil }
                let singers = (item["singers"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                let album = (item["albums"] as? [[String: Any]])?.first?["name"] as? String
                let pic = (item["imgItems"] as? [[String: Any]])?.first?["img"] as? String
                let name = item["name"] as? String ?? item["songName"] as? String ?? ""
                return Song(id: id, source: .mg, name: name,
                            singer: singers.joined(separator: "/"),
                            albumName: album, picUrl: pic,
                            interval: Double(item["duration"] as? Int ?? 0),
                            qualitys: [.k128])
            }
        case .kg:
            guard let dict = obj as? [String: Any],
                  let dataDict = dict["data"] as? [String: Any],
                  let info = dataDict["info"] as? [[String: Any]] else { return [] }
            return info.map { item in
                Song(id: item["hash"] as? String ?? "",
                     source: .kg,
                     name: item["songname"] as? String ?? "",
                     singer: item["singername"] as? String ?? "",
                     albumName: item["album_name"] as? String,
                     picUrl: nil,
                     interval: Double(item["duration"] as? Int ?? 0),
                     qualitys: [.k128, .k320, .flac],
                     extra: ["album_id": String(item["album_id"] as? Int ?? 0)])
            }
        default:
            return []
        }
    }

    private func extractKw(_ dict: [String: Any]) -> [Song]? {
        guard let list = dict["abslist"] as? [[String: Any]] else { return nil }
        return list.map { item in
            Song(id: String(item["MUSICRID"] as? String ?? "").replacingOccurrences(of: "MUSIC_", with: ""),
                 source: .kw,
                 name: item["SONGNAME"] as? String ?? "",
                 singer: item["ARTIST"] as? String ?? "",
                 albumName: item["ALBUM"] as? String,
                 picUrl: nil,
                 interval: Double(item["DURATION"] as? String ?? "0") ?? 0,
                 qualitys: [.k128, .k320, .flac],
                 extra: ["rid": String(item["MUSICRID"] as? String ?? "").replacingOccurrences(of: "MUSIC_", with: "")])
        }
    }

    // MARK: - 榜单（首页「小Q热歌 / 小云热歌」）
    func hotChart(source: SourceId) async -> [Song] {
        guard let template = book.chart[source.rawValue] else { return [] }
        do {
            let data = try await get(fill(template, ["TOPID": source == .tx ? "26" : "3778678"]))
            switch source {
            case .tx:
                guard let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let list = dict["songlist"] as? [[String: Any]] else { return [] }
                return list.prefix(20).enumerated().compactMap { idx, item in
                    guard let song = item["data"] as? [String: Any] else { return nil }
                    let singers = (song["singer"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                    let mid = song["songmid"] as? String ?? ""
                    let albumMid = song["albummid"] as? String
                    return Song(id: mid.isEmpty ? "\(idx)" : mid, source: .tx,
                                name: song["songname"] as? String ?? song["title"] as? String ?? "",
                                singer: singers.joined(separator: "/"),
                                albumName: song["albumname"] as? String,
                                picUrl: albumMid.map { "https://y.gtimg.cn/music/photo_new/T002R300x300M000\($0).jpg" },
                                interval: Double(song["interval"] as? Int ?? 0),
                                qualitys: [.k128, .k320, .flac],
                                extra: ["mid": mid])
                }
            case .wy:
                guard let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let result = dict["result"] as? [String: Any],
                      let tracks = result["tracks"] as? [[String: Any]] else { return [] }
                return tracks.prefix(20).map { item in
                    let artists = (item["artists"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                    let album = item["album"] as? [String: Any]
                    return Song(id: String(item["id"] as? Int ?? 0), source: .wy,
                                name: item["name"] as? String ?? "",
                                singer: artists.joined(separator: "/"),
                                albumName: album?["name"] as? String,
                                picUrl: album?["picUrl"] as? String,
                                interval: Double(item["duration"] as? Int ?? 0) / 1000,
                                qualitys: [.k128, .k320, .flac])
                }
            default:
                return []
            }
        } catch {
            return []
        }
    }

    // MARK: - 播放地址
    /// 顺序：自定义模板 → 平台直连（酷我 / 网易 / 酷狗）
    func resolveURL(song: Song, quality: Quality) async throws -> URL {
        if let template = book.resolve[song.source.rawValue] {
            let urlString = fill(template, ["id": song.id, "quality": quality.lxKey])
            if let url = URL(string: urlString) { return url }
        }
        switch song.source {
        case .kw: return try await resolveKuwo(song: song)
        case .wy: return try await resolveNetease(song: song)
        case .kg: return try await resolveKugou(song: song)
        default:
            throw SourceError.noResolver("音源没有返回播放地址（\(song.source.display)）。请导入支持该平台的音源脚本")
        }
    }

    /// 酷我：antiserver 直接回一个 http 音频地址
    private func resolveKuwo(song: Song) async throws -> URL {
        let rid = song.extra["rid"] ?? song.id
        let urlString = "http://antiserver.kuwo.cn/anti.s?type=convert_url&format=mp3&response=url&rid=MUSIC_\(rid)"
        guard let url = URL(string: urlString) else { throw SourceError.badURL }
        var request = URLRequest(url: url)
        request.timeoutInterval = 12
        guard let (data, _) = try? await session.data(for: request),
              let text = String(data: data, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines),
              text.hasPrefix("http"), let target = URL(string: text) else {
            throw SourceError.noResolver("酷我没有返回播放地址（该曲可能需要版权/无损音质）")
        }
        return target
    }

    /// 网易：outer 接口 302 到 CDN；不可播时会跳 /404，这里先探一次
    private func resolveNetease(song: Song) async throws -> URL {
        guard let url = URL(string: "https://music.163.com/song/media/outer/url?id=\(song.id).mp3") else {
            throw SourceError.badURL
        }
        var request = URLRequest(url: url)
        request.timeoutInterval = 12
        request.setValue("https://music.163.com/", forHTTPHeaderField: "Referer")
        let finalURL: URL = await withCheckedContinuation { cont in
            let task = session.dataTask(with: request) { _, response, _ in
                if let http = response as? HTTPURLResponse,
                   let location = http.allHeaderFields["Location"] as? String,
                   let target = URL(string: location) {
                    cont.resume(returning: target)
                } else {
                    cont.resume(returning: url)
                }
            }
            task.resume()
        }
        if finalURL.path.contains("/404") {
            throw SourceError.noResolver("网易云没有返回播放地址（该曲需要会员或已下架）")
        }
        return finalURL
    }

    /// 酷狗：trackercdn v2，key = md5(hash + "kgcloudv2")
    private func resolveKugou(song: Song) async throws -> URL {
        let hash = song.id
        guard !hash.isEmpty else { throw SourceError.noResolver("歌曲 ID 为空，换一首试试") }
        let key = md5(hash + "kgcloudv2")
        let urlString = "https://trackercdn.kugou.com/i/v2/?key=\(key)&hash=\(hash)&appid=1005&pid=2&cmd=25&behavior=play"
        guard let url = URL(string: urlString) else { throw SourceError.badURL }
        guard let (data, _) = try? await session.data(for: URLRequest(url: url)) else {
            throw SourceError.noResolver("酷狗请求失败")
        }
        guard let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw SourceError.noResolver("酷狗返回数据异常")
        }
        let candidate = (dict["url"] as? [String])?.first
            ?? (dict["data"] as? [String: Any])?["url"] as? String
        if let candidate, let target = URL(string: candidate) { return target }
        throw SourceError.noResolver("酷狗没有返回播放地址（" + ((dict["error"] as? String) ?? "可能被限流") + "）")
    }

    /// 歌词：按平台取（酷我 / 网易 / 酷狗 / QQ），失败再按同名歌去网易捞一次
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
           let list = try? await search(source: .wy, keyword: "\(song.name) \(song.displaySinger)"),
           let hit = list.first, let text = try? await neteaseLyric(id: hit.id) {
            return text
        }
        return nil
    }

    private func neteaseLyric(id: String) async throws -> String? {
        let data = try await get("https://interface3.music.163.com/api/song/lyric?id=\(id)&lv=1&kv=0&tv=-1",
                                 referer: "https://music.163.com/")
        return extractLyric(from: data)
    }

    private func kuwoLyric(rid: String) async throws -> String? {
        let data = try await get("https://wapi.kuwo.cn/openapi/v1/www/lyric/getlyric?musicId=\(rid)",
                                 referer: "https://www.kuwo.cn/")
        return extractLyric(from: data)
    }

    private func kugouLyric(hash: String) async throws -> String? {
        let millis = Int(Date().timeIntervalSince1970 * 1000)
        let data = try await get("https://m3ws.kugou.com/api/v1/krc/get_lyrics?clienttime=\(millis)&hash=\(hash)",
                                 referer: "https://www.kugou.com/")
        return extractLyric(from: data)
    }

    private func qqLyric(mid: String) async throws -> String? {
        let data = try await get("https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?songmid=\(mid)&format=json&nobase64=1",
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

    // MARK: - 热门歌单（网易云 + QQ 混排）
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
        let data = try? await get("https://music.163.com/api/personalized/playlist?limit=\(limit)",
                                  referer: "https://music.163.com/")
        guard let data,
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let list = dict["result"] as? [[String: Any]] else { return [] }
        return list.compactMap { item in
            guard let id = item["id"].map({ "\($0)" }) else { return nil }
            var cover = item["coverImgUrl"] as? String ?? item["picUrl"] as? String ?? ""
            if cover.isEmpty, let creator = item["creator"] as? [String: Any] {
                cover = creator["avatarUrl"] as? String ?? ""
            }
            return Playlist(id: "wy-\(id)",
                            name: item["name"] as? String ?? "热门歌单",
                            songs: [],
                            picUrl: cover.isEmpty ? nil : cover,
                            source: .wy,
                            isRemote: true,
                            trackCount: item["trackCount"] as? Int ?? 0)
        }
    }

    /// QQ 歌单广场（Android 用的是同一套 fcg 接口）
    /// 注意：广场里有部分歌单取不到曲目，这里先并发校验，只保留真能拿到歌的
    private func qqHotPlaylists(limit: Int) async -> [Playlist] {
        let candidates = 30
        let raw = "https://c.y.qq.com/splcloud/fcgi-bin/fcg_get_diss_by_tag.fcg?picmid=1&rnd=0.5&g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&categoryId=10000000&sortId=5&sin=0&ein=\(max(candidates - 1, 0))"
        guard let data = try? await get(raw, referer: "https://y.qq.com/"),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let dataDict = dict["data"] as? [String: Any],
              let list = dataDict["list"] as? [[String: Any]] else { return [] }

        struct Candidate {
            let id: String
            let name: String
            let cover: String
        }
        let items: [Candidate] = list.compactMap { item in
            guard let dissid = item["dissid"].map({ "\($0)" }) else { return nil }
            var cover = item["imgurl"] as? String ?? ""
            if cover.hasPrefix("http://") { cover = "https://" + cover.dropFirst("http://".count) }
            return Candidate(id: dissid, name: item["dissname"] as? String ?? "QQ 歌单", cover: cover)
        }
        guard !items.isEmpty else { return [] }

        // 分批并发校验（每批 8 个），凑够 limit 就停
        var result: [Playlist] = []
        var index = 0
        while index < items.count && result.count < limit {
            let batch = Array(items[index..<min(index + 8, items.count)])
            index += batch.count
            let checked = await withTaskGroup(of: Playlist?.self) { group -> [Playlist?] in
                for item in batch {
                    group.addTask {
                        guard let count = await Self.qqSongCount(dissid: item.id), count > 0 else { return nil }
                        return Playlist(id: "tx-\(item.id)",
                                        name: item.name,
                                        songs: [],
                                        picUrl: item.cover.isEmpty ? nil : item.cover,
                                        source: .tx,
                                        isRemote: true,
                                        trackCount: count)
                    }
                }
                var out: [Playlist?] = []
                for await value in group { out.append(value) }
                return out
            }
            result.append(contentsOf: checked.compactMap { $0 })
        }
        return Array(result.prefix(limit))
    }

    /// 校验 QQ 歌单可读 + 拿到真实曲目数（拿不到返回 nil）
    static func qqSongCount(dissid: String) async -> Int? {
        let raw = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?type=1&json=1&utf8=1&onlysong=0&disstid=\(dissid)&format=json&g_tk=5381"
        guard let url = URL(string: raw) else { return nil }
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.setValue("https://y.qq.com/", forHTTPHeaderField: "Referer")
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        guard let (data, _) = try? await URLSession.shared.data(for: request),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let cdlist = dict["cdlist"] as? [[String: Any]],
              let cd = cdlist.first,
              let list = cd["songlist"] as? [[String: Any]],
              !list.isEmpty else { return nil }
        return list.count
    }

}

enum SourceError: LocalizedError {
    case badURL, unsupported, noResolver(String), parse

    var errorDescription: String? {
        switch self {
        case .badURL: return "请求地址为空"
        case .unsupported: return "该平台暂不支持"
        case .noResolver(let msg): return msg
        case .parse: return "解析失败"
        }
    }
}

/// 酷我老接口返回的是「单引号伪 JSON」，Android 侧同样要文本兜底解析
enum KwTextParser {
    static func parse(_ text: String) -> [Song] {
        var songs: [Song] = []
        let blocks = text.components(separatedBy: "MUSICRID:'MUSIC_")
        for block in blocks.dropFirst() {
            func field(_ key: String) -> String? {
                let pattern = "\(key):'([^']*)'"
                guard let r = block.range(of: pattern, options: .regularExpression) else { return nil }
                let matched = String(block[r])
                return matched.components(separatedBy: "'").dropFirst().first
            }
            let id = block.components(separatedBy: "'").first ?? ""
            let name = field("SONGNAME") ?? ""
            let artist = field("ARTIST") ?? ""
            let album = field("ALBUM") ?? ""
            let duration = Double(field("DURATION") ?? "0") ?? 0
            if !name.isEmpty {
                songs.append(Song(id: id, source: .kw, name: name, singer: artist,
                                  albumName: album, picUrl: nil, interval: duration,
                                  qualitys: [.k128, .k320, .flac], extra: ["rid": id]))
            }
        }
        return songs
    }
}

