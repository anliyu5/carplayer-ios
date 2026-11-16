import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ---------- 1) QingGateway：TTL 8 小时、JSON 保序、错误码判断 ----------
g = os.path.join(root, "CarPlayer", "QingGateway.swift")
t = io.open(g, encoding="utf-8").read()
t = t.replace("private static let ticketTTL: TimeInterval = 600",
              "private static let ticketTTL: TimeInterval = 8 * 3600   // Android: TICKET_TTL = 28_800_000 ms")
t = t.replace('''        // org.json 风格的紧凑 JSON（键顺序固定，保证签名串与请求体一致）
        var body = "{"
        body += json.keys.sorted().map { "\\"\\($0)\\":\\"\\(json[$0] ?? "")\\"" }.joined(separator: ",")
        body += "}"
        let request = makeRequest(path: path, body: body, bearer: bearer)''',
'''        // 与 org.json 一致：保持调用方给的键顺序，保证签名串与请求体完全一致
        let body = "{" + json.map { "\\"\\($0.key)\\":\\"\\($0.value)\\"" }.joined(separator: ",") + "}"
        let request = makeRequest(path: path, body: body, bearer: bearer)''')
# payload 用有序数组，避免字典顺序不定
t = t.replace('''    private static func post(path: String, json: [String: String], bearer: String?) async -> (Int, [String: Any])? {''',
'''    private static func post(path: String, json: [(key: String, value: String)], bearer: String?) async -> (Int, [String: Any])? {''')
t = t.replace('''        let payload = ["deviceId": deviceId, "appVersion": appVersion, "platform": "android"]''',
'''        let payload: [(key: String, value: String)] = [("deviceId", deviceId), ("appVersion", appVersion), ("platform", "android")]''')
t = t.replace('''        let payload = ["source": source, "rid": rid, "level": level]''',
'''        let payload: [(key: String, value: String)] = [("source", source), ("rid", rid), ("level", level)]''')
t = t.replace('''                if attempt == 0, reason.contains("SIGN") || reason.contains("UPGRADE") || message.contains("授权") {''',
'''                let codeText = (obj["code"] as? String) ?? ""
                if attempt == 0, codeText.contains("SIGN") || codeText.contains("UPGRADE")
                    || reason.contains("SIGN") || reason.contains("UPGRADE") || message.contains("授权") {''')
io.open(g, "w", encoding="utf-8").write(t)
print("QingGateway aligned with Android")

# ---------- 2) BuiltinSources：搜索按 Android 的接口/Referer ----------
b = os.path.join(root, "CarPlayer", "BuiltinSources.swift")
s = io.open(b, encoding="utf-8").read()

s = s.replace('"wet": ""', '"wet": ""')  # noop
s = s.replace('''        "wy": "https://music.163.com/api/search/get?s={keyword}&type=1&limit=30&offset=0",''',
              '''        "wy": "https://interface.music.163.com/api/search/get?type=1&s={keyword}&limit=30&offset=0",''')
s = s.replace('''        "mg": "https://m.music.migu.cn/migu/remoting/scr_search_tag?keyword={keyword}&type=2&rows=20&pgc=1",''',
              '''        "mg": "https://app.c.nf.migu.cn/MIGUM2.0/v1.0/content/search_all.do?ua=Android_migu&version=5.0.1&text={keyword}&pageNo=1&pageSize=30&searchSwitch=%7B%22song%22%3A1%7D",''')

# 带 Referer 的 get
s = s.replace('''    private func get(_ urlString: String) async throws -> Data {
        guard let url = URL(string: urlString) else { throw SourceError.badURL }
        let (data, _) = try await session.data(from: url)
        return data
    }''',
'''    private func get(_ urlString: String, referer: String? = nil) async throws -> Data {
        guard let url = URL(string: urlString) else { throw SourceError.badURL }
        var request = URLRequest(url: url)
        if let referer { request.setValue(referer, forHTTPHeaderField: "Referer") }
        let (data, _) = try await session.data(for: request)
        return data
    }''')

# 每个平台带自己的 Referer（Android 的做法）
s = s.replace('''    func search(source: SourceId, keyword: String) async throws -> [Song] {
        guard let template = book.search[source.rawValue] else { throw SourceError.unsupported }
        let data = try await get(fill(template, ["keyword": keyword]))
        return parseSearch(source: source, data: data)
    }''',
'''    func search(source: SourceId, keyword: String) async throws -> [Song] {
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
    }''')

# 咪咕解析：按 songResultData.result[] 结构
s = s.replace('''        case .mg:
            guard let dict = obj as? [String: Any], let list = dict["musics"] as? [[String: Any]] else { return [] }
            return list.map { item in
                Song(id: item["copyrightId"] as? String ?? item["id"] as? String ?? "",
                     source: .mg,
                     name: item["songName"] as? String ?? item["name"] as? String ?? "",
                     singer: item["singerName"] as? String ?? "",
                     albumName: item["albumName"] as? String,
                     picUrl: item["cover"] as? String,
                     interval: Double(item["length"] as? String ?? "0") ?? 0,
                     qualitys: [.k128, .k320, .flac])
            }''',
'''        case .mg:
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
            }''')
io.open(b, "w", encoding="utf-8").write(s)
print("BuiltinSources search aligned with Android")
