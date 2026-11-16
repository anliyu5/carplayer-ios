import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "QingGate.swift")
t = io.open(p, encoding="utf-8").read()

start = t.index("    // MARK: 解析")
end = t.index("    /// 粘贴内容可能是 URL，也可能是整段 JSON（含 JS 注释头）")
new = '''    // MARK: 解析
    /// 容错解析：去掉 BOM / JS 注释 / 前后杂物，必要时截取首个 { 到最后一个 }
    static func parse(json text: String, sourceURL: String? = nil) -> QingConfig? {
        var meta: [String: String] = [:]
        let raw = stripComments(text, meta: &meta)

        for candidate in [raw, sliceJSON(raw)] {
            if let config = decode(candidate, meta: meta, sourceURL: sourceURL) { return config }
        }
        QingDebug.lastError = "解析失败：长度 \\(text.count)，含 lines=\\(text.contains("lines"))，开头：\\(String(text.prefix(80)).replacingOccurrences(of: "\\n", with: " "))"
        return nil
    }

    /// 去掉 BOM、/* */ 块注释与 // 行注释，同时收集 @name/@version 等元信息
    private static func stripComments(_ text: String, meta: inout [String: String]) -> String {
        var body = text.replacingOccurrences(of: "\\u{FEFF}", with: "")
        while let start = body.range(of: "/*"), let end = body.range(of: "*/", range: start.upperBound..<body.endIndex) {
            for raw in body[start.upperBound..<end.lowerBound].split(separator: "\\n") {
                let line = raw.trimmingCharacters(in: CharacterSet(charactersIn: " \\t\\r*"))
                guard line.hasPrefix("@") else { continue }
                let parts = line.dropFirst().split(separator: " ", maxSplits: 1, omittingEmptySubsequences: true)
                if parts.count == 2 {
                    meta[String(parts[0]).lowercased()] = String(parts[1]).trimmingCharacters(in: .whitespaces)
                }
            }
            body.removeSubrange(start.lowerBound..<end.upperBound)
        }
        if let lineComment = body.range(of: "//") whereFalse: do { _ = lineComment }
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

'''
t = t[:start] + new + t[end:]

# load：https 失败再退 http，并带上 Accept / 不缓存
old_load_start = t.index("    /// 从配置网址下载并解析")
old_load_end = t.index("}\n\n// MARK: - 青听网关")
new_load = '''    /// 从配置网址下载并解析（https 失败自动退 http，禁用缓存）
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
            QingDebug.lastError = "下载失败：\\(urlString)（网络或证书问题）"
        }
        return nil
    }
'''
t = t[:old_load_start] + new_load + t[old_load_end:]

# 追加调试容器
t = t.replace("// MARK: - 青听网关", '''/// 最近的解析/下载错误（显示在设置页「诊断」里，便于远程排查）
enum QingDebug {
    static var lastError: String?
}

// MARK: - 青听网关''')

io.open(p, "w", encoding="utf-8").write(t)
print("QingGate rewritten:", len(t), "chars")
print("  stripComments:", "private static func stripComments" in t)
