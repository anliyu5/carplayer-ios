import Foundation

// MARK: - 青听音源配置（真实 schema：lines[].id/name/enabled/searchApi/detailApi/levels）
//
// 官方 music.json：
//   /**
//    * @name 青听音源
//    * @version 1.1
//    */
//   { "lines": [ { "id": "kw", "name": "小窝源", "enabled": true,
//                  "searchApi": "fetchSearchMusic", "detailApi": "fetchMusicDetail",
//                  "levels": ["standard","exhigh","lossless","atmos","atmos_plus","master"] } ] }
//
// 关键点：lines 里**没有** url 字段，网关根地址由 music.json 自身网址推导：
//   https://13413.kstore.vip/QingMusic/music.json → https://13413.kstore.vip
struct QingConfig: Codable, Hashable {
    struct Line: Codable, Hashable, Identifiable {
        var id: String
        var name: String
        var enabled: Bool = true
        var searchApi: String?
        var detailApi: String?
        var levels: [String] = []
        var url: String?          // 兼容其它网关写法

        var sourceId: SourceId? { SourceId(qingLineId: id) }
        var qualities: [Quality] { levels.compactMap { Quality.fromLevel($0) } }
        var levelsText: String { levels.isEmpty ? "-" : levels.joined(separator: "/") }
    }

    var lines: [Line]
    var raw: String
    var meta: [String: String] = [:]
    var sourceURL: String?

    var title: String { meta["name"] ?? "青听音源" }
    var version: String { meta["version"] ?? "-" }
    var author: String { meta["author"] ?? "" }
    var enabledLines: [Line] { lines.filter { $0.enabled } }
    var supportedSources: [SourceId] { enabledLines.compactMap { $0.sourceId } }

    /// https://13413.kstore.vip/QingMusic/music.json → https://13413.kstore.vip
    var gatewayBase: String {
        guard let sourceURL, let url = URL(string: sourceURL),
              var comps = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return "" }
        comps.path = ""
        comps.query = nil
        comps.fragment = nil
        return comps.string ?? ""
    }

    // MARK: 解析
    /// 容错解析：去掉 BOM / JS 注释 / 前后杂物，必要时截取首个 { 到最后一个 }
    static func parse(json text: String, sourceURL: String? = nil) -> QingConfig? {
        var meta: [String: String] = [:]
        let raw = stripComments(text, meta: &meta)

        for candidate in [raw, sliceJSON(raw)] {
            if let config = decode(candidate, meta: meta, sourceURL: sourceURL) { return config }
        }
        QingDebug.lastError = "解析失败：长度 \(text.count)，含 lines=\(text.contains("lines"))，开头：\(String(text.prefix(80)).replacingOccurrences(of: "\n", with: " "))"
        return nil
    }

    /// 去掉 BOM、/* */ 块注释与 // 行注释，同时收集 @name/@version 等元信息
    private static func stripComments(_ text: String, meta: inout [String: String]) -> String {
        var body = text.replacingOccurrences(of: "\u{FEFF}", with: "")
        while let start = body.range(of: "/*"), let end = body.range(of: "*/", range: start.upperBound..<body.endIndex) {
            for raw in body[start.upperBound..<end.lowerBound].split(separator: "\n") {
                let line = raw.trimmingCharacters(in: CharacterSet(charactersIn: " \t\r*"))
                guard line.hasPrefix("@") else { continue }
                let parts = line.dropFirst().split(separator: " ", maxSplits: 1, omittingEmptySubsequences: true)
                if parts.count == 2 {
                    meta[String(parts[0]).lowercased()] = String(parts[1]).trimmingCharacters(in: .whitespaces)
                }
            }
            body.removeSubrange(start.lowerBound..<end.upperBound)
        }
        body = body.trimmingCharacters(in: .whitespacesAndNewlines)
        return body
    }

    /// 截取首个 { 到最后一个 }，防止前后有杂字符/说明文字
    private static func sliceJSON(_ text: String) -> String {
        guard let first = text.firstIndex(of: "{"), let last = text.lastIndex(of: "}"), first < last else { return text }
        return String(text[first...last])
    }

    private static func decode(_ text: String, meta: [String: String], sourceURL: String?) -> QingConfig? {
        guard let data = text.data(using: .utf8) else { return nil }
        let object = (try? JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed]))
            ?? (try? JSONSerialization.jsonObject(with: data))
        guard let root = object as? [String: Any] else { return nil }

        // lines 可能在根上，也可能包在 data 里
        let linesArr = (root["lines"] as? [[String: Any]])
            ?? ((root["data"] as? [String: Any])?["lines"] as? [[String: Any]])
            ?? []
        guard !linesArr.isEmpty else { return nil }

        var lines: [Line] = []
        for item in linesArr {
            guard let id = (item["id"] as? String) ?? (item["source"] as? String) ?? (item["key"] as? String) else { continue }
            lines.append(Line(id: id,
                              name: (item["name"] as? String) ?? id,
                              enabled: (item["enabled"] as? Bool) ?? true,
                              searchApi: (item["searchApi"] as? String) ?? (item["search_api"] as? String),
                              detailApi: (item["detailApi"] as? String) ?? (item["detail_api"] as? String),
                              levels: (item["levels"] as? [String]) ?? (item["qualitys"] as? [String]) ?? [],
                              url: (item["url"] as? String) ?? (item["api"] as? String)))
        }
        guard !lines.isEmpty else { return nil }
        var finalMeta = meta
        if finalMeta["name"] == nil { finalMeta["name"] = "青听音源" }
        QingDebug.lastError = nil
        return QingConfig(lines: lines, raw: text, meta: finalMeta, sourceURL: sourceURL)
    }

    /// 粘贴内容可能是 URL，也可能是整段 JSON（含 JS 注释头）
    static func parse(text: String) -> QingConfig? {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.hasPrefix("http"), !trimmed.contains("{") { return nil }   // 交给上层先下载
        return parse(json: trimmed)
    }

    /// 从配置网址下载并解析（https 失败自动退 http，禁用缓存）
    static func load(urlString: String) async -> QingConfig? {
        guard let url = URL(string: urlString) else { return nil }
        var candidates: [URL] = [url]
        if url.scheme == "https", var comps = URLComponents(url: url, resolvingAgainstBaseURL: false) {
            comps.scheme = "http"
            if let httpURL = comps.url { candidates.append(httpURL) }
        }
        var lastBody = ""
        for candidate in candidates {
            var request = URLRequest(url: candidate, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 15)
            request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
            request.setValue("application/json,text/plain,*/*", forHTTPHeaderField: "Accept")
            guard let (data, _) = try? await URLSession.shared.data(for: request),
                  let text = String(data: data, encoding: .utf8) else { continue }
            lastBody = text
            if let config = parse(json: text, sourceURL: urlString) { return config }
        }
        if lastBody.isEmpty {
            QingDebug.lastError = "下载失败：\(urlString)（网络或证书问题）"
        }
        return nil
    }
}

/// 最近的解析/下载错误（显示在设置页「诊断」里，便于远程排查）
enum QingDebug {
    static var lastError: String?
}

// MARK: - 容错 JSON 读取工具（网关返回结构随版本变化）
enum JSON {
    static func firstURL(in data: Data) -> String? {
        if let obj = try? JSONSerialization.jsonObject(with: data),
           let hit = walk(obj, match: { $0.hasPrefix("http://") || $0.hasPrefix("https://") }) {
            return hit
        }
        if let text = String(data: data, encoding: .utf8),
           let r = text.range(of: #"https?://[^"\\\s)]+"#, options: .regularExpression) {
            return String(text[r])
        }
        return nil
    }

    static func firstString(in data: Data, key: String) -> String? {
        guard let obj = try? JSONSerialization.jsonObject(with: data) else { return nil }
        if let dict = obj as? [String: Any], let value = dict[key] as? String, !value.isEmpty { return value }
        if let dict = obj as? [String: Any], let nested = dict["data"] as? [String: Any],
           let value = nested[key] as? String, !value.isEmpty { return value }
        return nil
    }

    private static func walk(_ node: Any, match: (String) -> Bool) -> String? {
        if let dict = node as? [String: Any] {
            for key in ["url", "playUrl", "play_url", "src", "link"] {
                if let value = dict[key] as? String, match(value) { return value }
            }
            for (_, value) in dict {
                if let hit = walk(value, match: match) { return hit }
            }
        } else if let array = node as? [Any] {
            for value in array {
                if let hit = walk(value, match: match) { return hit }
            }
        } else if let str = node as? String, match(str) {
            return str
        }
        return nil
    }
}

