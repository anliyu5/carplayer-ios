import io, os, re
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "AppStore.swift")
t = io.open(p, encoding="utf-8").read()

# --- 1) 搜索来源：优先用青听配置里的线路 ---
old_sources = '''        let sources = SourceId.searchOrder.filter { settings.enabledSources.contains($0) }
        if sources.isEmpty {
            searching = false
            searchStatus = "至少保留一个搜索来源"
            return
        }'''
new_sources = '''        let sources = searchSources
        if sources.isEmpty {
            searching = false
            searchStatus = "至少保留一个搜索来源"
            return
        }'''
assert old_sources in t
t = t.replace(old_sources, new_sources)

# --- 2) 追加 searchSources 计算属性 ---
anchor = '''    private func engineSearch(_ keyword: String) async -> [Song]? {'''
add = '''    /// 当前生效的搜索来源：导入青听配置后以配置里的 lines 为准，否则用设置页勾选的平台
    var searchSources: [SourceId] {
        if let qing {
            let list = qing.supportedSources
            if !list.isEmpty {
                let ordered = SourceId.searchOrder.filter { list.contains($0) }
                let extra = list.filter { !SourceId.searchOrder.contains($0) }
                return ordered + extra
            }
        }
        return SourceId.searchOrder.filter { settings.enabledSources.contains($0) }
    }

    private func engineSearch(_ keyword: String) async -> [Song]? {'''
assert anchor in t
t = t.replace(anchor, add)

# --- 3) 搜索结果里的青听补充改为：直接用内置适配器搜（网关只负责取播放地址） ---
old_engine_call = '''            // 自定义脚本音源（lx 脚本 / 青听网关）补充
            if let scriptSongs = await engineSearch(k) { all.append(contentsOf: scriptSongs) }
'''
new_engine_call = ''
assert old_engine_call in t
t = t.replace(old_engine_call, new_engine_call)

# --- 4) importQing：用真实 schema 解析（注释头 + lines，URL 先下载） ---
start = t.index('    func importQing(json: String) async -> String {')
end = t.index('    func clearQing() {')
new_import = '''    func importQing(json: String) async -> String {
        let text = json.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return "内容为空" }

        var config: QingConfig?
        if text.hasPrefix("http") {
            config = await QingConfig.load(urlString: text)
            if config == nil { return "下载失败，检查网址后重试" }
        } else {
            config = QingConfig.parse(json: text)
        }
        guard let config else {
            return "这份内容没能解析成青听音源配置（需要 lines 字段）。请确认粘贴的是 music.json 的网址，或完整的 JSON 内容。"
        }
        qing = config
        save(config, "qing")
        let names = config.lines.map { $0.name }.joined(separator: " / ")
        return "已导入「\\(config.title) \\(config.version)」· \\(config.lines.count) 条线路：\\(names)"
    }

    /// 切换青听配置里某条线路的启用状态
    func toggleQingLine(_ lineId: String) {
        guard var config = qing,
              let index = config.lines.firstIndex(where: { $0.id == lineId }) else { return }
        config.lines[index].enabled.toggle()
        qing = config
        save(config, "qing")
    }

'''
t = t[:start] + new_import + t[end:]

io.open(p, "w", encoding="utf-8").write(t)
print("AppStore patched:", len(t), "chars")
for k in ["var searchSources", "QingConfig.load(urlString", "toggleQingLine"]:
    print("  ", k, "->", k in t)
