import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "BuiltinSources.swift")
t = io.open(p, encoding="utf-8").read()

# 1) 榜单模板：tx 换成实测可用的 v8 接口
t = t.replace(
 '"tx": "https://u.y.qq.com/cgi-bin/musicu.fcg?format=json&g_tk=5381&topid={TOPID}&num=20",',
 '"tx": "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?topid={TOPID}&format=json&page=detail&type=top&song_num=20",\n        "kw": "https://www.kuwo.cn/api/pc/bang/bang?bangId={TOPID}"')

# 2) tx 榜单解析：改为 songlist[].data
old_tx = '''            case .tx:
                guard let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let detail = (dict["detail"] as? [String: Any]),
                      let dataDict = detail["data"] as? [String: Any],
                      let songs = dataDict["songInfoList"] as? [[String: Any]] else { return [] }
                return songs.prefix(20).enumerated().map { idx, item in
                    let singers = (item["singer"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                    let mid = item["mid"] as? String ?? ""
                    return Song(id: mid.isEmpty ? String(idx) : mid, source: .tx,
                                name: item["title"] as? String ?? item["name"] as? String ?? "",
                                singer: singers.joined(separator: "/"),
                                albumName: (item["album"] as? [String: Any])?["name"] as? String,
                                picUrl: nil, interval: Double(item["interval"] as? Int ?? 0),
                                qualitys: [.k128, .k320, .flac], extra: ["mid": mid])
                }'''
new_tx = '''            case .tx:
                guard let dict = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let list = dict["songlist"] as? [[String: Any]] else { return [] }
                return list.prefix(20).enumerated().compactMap { idx, item in
                    guard let song = item["data"] as? [String: Any] else { return nil }
                    let singers = (song["singer"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                    let mid = song["songmid"] as? String ?? ""
                    let albumMid = song["albummid"] as? String
                    return Song(id: mid.isEmpty ? "\\(idx)" : mid, source: .tx,
                                name: song["songname"] as? String ?? song["title"] as? String ?? "",
                                singer: singers.joined(separator: "/"),
                                albumName: song["albumname"] as? String,
                                picUrl: albumMid.map { "https://y.gtimg.cn/music/photo_new/T002R300x300M000\\($0).jpg" },
                                interval: Double(song["interval"] as? Int ?? 0),
                                qualitys: [.k128, .k320, .flac],
                                extra: ["mid": mid])
                }'''
assert old_tx in t
t = t.replace(old_tx, new_tx)

# 3) 播放地址：平台直连兜底
old_resolve = '''    // MARK: - 直连解析（EndpointBook.resolve 未配置时抛错，交由脚本/网关处理）
    func resolveURL(song: Song, quality: Quality) async throws -> URL {
        guard let template = book.resolve[song.source.rawValue] else {
            throw SourceError.noResolver("音源未返回播放地址（\\(song.source.display)）。请在设置里导入音源脚本或青听配置")
        }
        let urlString = fill(template, ["id": song.id, "quality": quality.lxKey])
        guard let url = URL(string: urlString) else { throw SourceError.badURL }
        return url
    }'''
new_resolve = '''    // MARK: - 播放地址
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
            throw SourceError.noResolver("音源没有返回播放地址（\\(song.source.display)）。请导入支持该平台的音源脚本")
        }
    }

    /// 酷我：antiserver 直接回一个 http 音频地址
    private func resolveKuwo(song: Song) async throws -> URL {
        let rid = song.extra["rid"] ?? song.id
        let urlString = "http://antiserver.kuwo.cn/anti.s?type=convert_url&format=mp3&response=url&rid=MUSIC_\\(rid)"
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
        guard let url = URL(string: "https://music.163.com/song/media/outer/url?id=\\(song.id).mp3") else {
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
        let urlString = "https://trackercdn.kugou.com/i/v2/?key=\\(key)&hash=\\(hash)&appid=1005&pid=2&cmd=25&behavior=play"
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
    }'''
assert old_resolve in t
t = t.replace(old_resolve, new_resolve)

io.open(p, "w", encoding="utf-8").write(t)
print("BuiltinSources patched:", len(t), "chars")
for k in ["resolveKuwo", "resolveNetease", "resolveKugou", "songlist"]:
    print("  ", k, "->", k in t)
