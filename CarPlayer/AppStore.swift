import Foundation
import Combine

// 对应 Android com.carplayer.data.Store：全部状态落盘到 Application Support/CarPlayer
struct AppSettings: Codable, Equatable {
    var downloadQuality: Quality = .k320
    var playQuality: Quality = .k320
    var autoPlayOnLaunch: Bool = false
    var bootAutoStart: Bool = false
    var enabledSources: Set<SourceId> = [.kw, .wy, .tx, .mg, .kg]
    var defaultQualityLabel: String = "默认音质"
    var volume: Double = 0.85
    var lastSongId: String?
    var lastPosition: Double = 0
}

@MainActor
final class AppStore: ObservableObject {
    // MARK: - 持久化状态
    @Published var playlists: [Playlist] = []
    @Published var history: [HistoryEntry] = []
    @Published var favorites: [Song] = []
    @Published var downloads: [Song] = []
    @Published var searchHistory: [String] = []
    @Published var settings = AppSettings()
    @Published var scripts: [ScriptMeta] = []
    @Published var qing: QingConfig?

    // MARK: - 运行状态
    @Published var searchKeyword: String = ""
    @Published var searchResults: [Song] = []
    @Published var searchStatus: String = "输入关键词开始搜索"
    @Published var searching: Bool = false
    @Published var hotTx: [Song] = []
    @Published var hotWy: [Song] = []
    @Published var hotTxError: String?
    @Published var hotWyError: String?
    @Published var hotLoading: Bool = false
    @Published var crashLog: String = ""
    @Published var hotPlaylists: [Playlist] = []
    @Published var hotPlaylistLoading = false
    @Published var hotPlaylistError: String?
    @Published var toast: String?

    private let root: URL
    private let engine: LxRuntimeEngine
    private let net: BuiltinSources
    var player: PlayerEngine!

    init() {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("CarPlayer", isDirectory: true)
        try? FileManager.default.createDirectory(at: base, withIntermediateDirectories: true)
        root = base
        engine = LxRuntimeEngine()
        net = BuiltinSources()
        load()
        if playlists.isEmpty { seedDefaultPlaylists() }
        player = PlayerEngine(store: self)
    }

    // MARK: - 文件读写
    private func url(_ name: String) -> URL { root.appendingPathComponent(name + ".json") }

    private func load() {
        playlists = decode([Playlist].self, "playlists") ?? []
        history = decode([HistoryEntry].self, "history") ?? []
        favorites = decode([Song].self, "favorites") ?? []
        downloads = decode([Song].self, "downloads") ?? []
        searchHistory = decode([String].self, "searchHistory") ?? []
        settings = decode(AppSettings.self, "settings") ?? AppSettings()
        scripts = decode([ScriptMeta].self, "scripts") ?? []
        if let q: QingConfig = decode(QingConfig.self, "qing") { qing = q }
        crashLog = (try? String(contentsOf: url("crash"), encoding: .utf8)) ?? ""
    }

    private func decode<T: Decodable>(_ type: T.Type, _ name: String) -> T? {
        guard let data = try? Data(contentsOf: url(name)) else { return nil }
        return try? JSONDecoder().decode(T.self, from: data)
    }

    private func save<T: Encodable>(_ value: T, _ name: String) {
        guard let data = try? JSONEncoder().encode(value) else { return }
        try? data.write(to: url(name), options: .atomic)
    }

    func persistAll() {
        save(playlists, "playlists"); save(history, "history"); save(favorites, "favorites")
        save(downloads, "downloads"); save(searchHistory, "searchHistory")
        save(settings, "settings"); save(scripts, "scripts")
        if let qing { save(qing, "qing") }
    }

    private func seedDefaultPlaylists() {
        playlists = [
            Playlist(id: "favorite", name: "我的收藏", songs: [], picUrl: nil, source: .local, isFavorite: true),
            Playlist(id: "local", name: "本地音乐", songs: [], picUrl: nil, source: .local)
        ]
        save(playlists, "playlists")
    }

    // MARK: - 提示
    func show(_ text: String) {
        toast = text
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 1_800_000_000)
            if toast == text { toast = nil }
        }
    }

    // MARK: - 歌单
    var favoritePlaylist: Playlist {
        playlists.first(where: { $0.isFavorite }) ??
        Playlist(id: "favorite", name: "我的收藏", songs: [], isFavorite: true)
    }

    func isFavorite(_ song: Song) -> Bool {
        favoritePlaylist.songs.contains { $0.id == song.id && $0.source == song.source }
    }

    func toggleFavorite(_ song: Song) {
        var fav = favoritePlaylist
        if let idx = fav.songs.firstIndex(where: { $0.id == song.id && $0.source == song.source }) {
            fav.songs.remove(at: idx)
            show("已取消收藏")
        } else {
            fav.songs.insert(song, at: 0)
            show("已收藏")
        }
        replacePlaylist(fav)
    }

    func replacePlaylist(_ playlist: Playlist) {
        if let idx = playlists.firstIndex(where: { $0.id == playlist.id }) {
            playlists[idx] = playlist
        } else {
            playlists.append(playlist)
        }
        save(playlists, "playlists")
    }

    func createPlaylist(name: String) -> Playlist {
        let p = Playlist(id: UUID().uuidString, name: name, songs: [])
        playlists.append(p)
        save(playlists, "playlists")
        return p
    }

    func addToPlaylist(_ song: Song, playlistId: String) -> Bool {
        guard var p = playlists.first(where: { $0.id == playlistId }) else { return false }
        if p.songs.contains(where: { $0.id == song.id && $0.source == song.source }) {
            show("「\(p.name)」里已经有这首歌了")
            return false
        }
        p.songs.append(song)
        replacePlaylist(p)
        show("已加入「\(p.name)」")
        return true
    }

    func removeFromPlaylist(_ song: Song, playlistId: String) {
        guard var p = playlists.first(where: { $0.id == playlistId }) else { return }
        p.songs.removeAll { $0.id == song.id && $0.source == song.source }
        replacePlaylist(p)
        show("已移除")
    }

    func deletePlaylist(_ playlist: Playlist) {
        if playlist.isFavorite { show("收藏歌单不可删除"); return }
        playlists.removeAll { $0.id == playlist.id }
        save(playlists, "playlists")
        show("已删除")
    }

    // MARK: - 播放历史
    func addHistory(_ song: Song) {
        history.removeAll { $0.song.id == song.id && $0.song.source == song.source }
        history.insert(HistoryEntry(song: song, source: song.source.rawValue, time: Date()), at: 0)
        if history.count > 100 { history = Array(history.prefix(100)) }   // 最多保留最近 100 首
        save(history, "history")
    }

    func clearHistory() {
        history = []
        save(history, "history")
        show("已清空播放历史")
    }

    func addSearchHistory(_ keyword: String) {
        let k = keyword.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !k.isEmpty else { return }
        searchHistory.removeAll { $0 == k }
        searchHistory.insert(k, at: 0)
        if searchHistory.count > 30 { searchHistory = Array(searchHistory.prefix(30)) }
        save(searchHistory, "searchHistory")
    }

    func clearSearchHistory() {
        searchHistory = []
        save(searchHistory, "searchHistory")
        show("已清空搜索历史")
    }

    // MARK: - 搜索
    func search(_ keyword: String) {
        let k = keyword.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !k.isEmpty else {
            searchStatus = "请输入关键词"
            return
        }
        searchKeyword = k
        addSearchHistory(k)
        searching = true
        searchStatus = "搜索中…"
        searchResults = []

        let sources = searchSources
        if sources.isEmpty {
            searching = false
            searchStatus = "至少保留一个搜索来源"
            return
        }

        Task { @MainActor in
            var all: [Song] = []
            var errors: [String] = []
            for source in sources {
                do {
                    let songs = try await net.search(source: source, keyword: k)
                    all.append(contentsOf: songs)
                } catch {
                    errors.append("\(source.display)搜索失败")
                }
            }
            searching = false
            // 稳定排序：小Q源结果永远在最前，其余按来源优先级
            searchResults = all.enumerated()
                .sorted { lhs, rhs in
                    let lp = sourcePriority(lhs.element.source)
                    let rp = sourcePriority(rhs.element.source)
                    return lp == rp ? lhs.offset < rhs.offset : lp < rp
                }
                .map { $0.element }
            if all.isEmpty {
                searchStatus = errors.isEmpty ? "没有结果，换个关键词试试" : "搜索失败：\(errors.joined(separator: "，"))"
            } else {
                searchStatus = "共 \(all.count) 首 · \(sources.map { $0.display }.joined(separator: " / "))"
            }
        }
    }

    /// 来源优先级：小Q源(tx) 永远排最前，其余按内置顺序，未知来源垫底
    func sourcePriority(_ source: SourceId) -> Int {
        SourceId.searchOrder.firstIndex(of: source) ?? SourceId.searchOrder.count
    }

    /// 可用来源：导入青听配置后以配置里的线路为准，否则是内置五平台；统一按优先级排序
    var availableSources: [SourceId] {
        var list: [SourceId] = SourceId.searchOrder
        if let qing = self.qing, !qing.supportedSources.isEmpty {
            list = qing.supportedSources
        }
        return list.sorted { sourcePriority($0) < sourcePriority($1) }
    }

    /// 生效来源 = 可用来源 ∩ 用户在搜索页勾选的；勾选为空时退回全部可用
    var searchSources: [SourceId] {
        let available = availableSources
        let selected = settings.enabledSources
        let filtered = available.filter { selected.contains($0) }
        return filtered.isEmpty ? available : filtered
    }

    /// 搜索页点 chip：切换来源并立刻重搜
    func toggleSearchSource(_ source: SourceId) {
        var set = settings.enabledSources
        if set.contains(source) {
            if availableSources.contains(where: { set.contains($0) }) && set.count <= 1 {
                show("至少保留一个搜索来源")
                persistAll()
                return
            }
            set.remove(source)
        } else {
            set.insert(source)
        }
        settings.enabledSources = set
        persistAll()
        if !searchKeyword.isEmpty { search(searchKeyword) }
    }

    func isSourceEnabled(_ source: SourceId) -> Bool {
        settings.enabledSources.contains(source)
    }


    // MARK: - 首页热歌榜
    func loadHotCharts(force: Bool = false) {
        guard !hotLoading else { return }
        hotLoading = true
        hotTxError = nil
        hotWyError = nil
        Task { @MainActor in
            async let tx = net.hotChart(source: .tx)
            async let wy = net.hotChart(source: .wy)
            let (t, w) = await (tx, wy)
            hotLoading = false
            hotTx = t
            hotWy = w
            if t.isEmpty { hotTxError = "加载失败" }
            if w.isEmpty { hotWyError = "加载失败" }
        }
    }

    /// 首页「热门歌单」：网易云
    func loadHotPlaylists(force: Bool = false) {
        guard force || hotPlaylists.isEmpty, !hotPlaylistLoading else { return }
        hotPlaylistLoading = true
        hotPlaylistError = nil
        Task { @MainActor in
            let list = (try? await net.hotPlaylists(limit: 20)) ?? []
            hotPlaylistLoading = false
            if list.isEmpty {
                hotPlaylistError = "加载失败"
            } else {
                hotPlaylists = list
            }
        }
    }

    /// 点热门歌单：拉全量曲目 → 写入歌单 → 返回可展示的 Playlist（不自动播放）
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
        show("已加载「\(full.name)」· \(imported.songs.count) 首")
        return full
    }

    func shuffleHot() {
        hotTx.shuffle()
        hotWy.shuffle()
    }

    // MARK: - 音源脚本
    func importScript(text: String) async -> String {
        guard text.contains("lx.sources") || text.contains("lx.on") else {
            return "这不像是音源脚本（缺少 lx.sources）"
        }
        let meta = await engine.probe(script: text)
        guard let meta else { return "脚本注入失败：脚本环境加载失败" }
        scripts.removeAll { $0.id == meta.id }
        scripts.append(meta)
        save(scripts, "scripts")
        return "已导入「\(meta.name)」，支持 \(meta.sources.keys.joined(separator: "/"))"
    }

    func removeScript(_ meta: ScriptMeta) {
        scripts.removeAll { $0.id == meta.id }
        save(scripts, "scripts")
    }

    func importQing(json: String, sourceURL: String? = nil) async -> String {
        let text = json.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return "内容为空" }

        var config: QingConfig?
        if text.hasPrefix("http") {
            config = await QingConfig.load(urlString: text)
            if config == nil { return "下载失败，检查网址后重试" }
        } else {
            config = QingConfig.parse(json: text, sourceURL: sourceURL)
        }
        guard let config else {
            let detail = QingDebug.lastError.map { "\n诊断：\($0)" } ?? ""
            return "这份内容没能解析成青听音源配置（需要 lines 字段）。请确认粘贴的是 music.json 的网址，或完整的 JSON 内容。\(detail)"
        }
        qing = config
        save(config, "qing")
        var set = settings.enabledSources
        for source in config.supportedSources { set.insert(source) }
        settings.enabledSources = set
        save(settings, "settings")
        let names = config.lines.map { $0.name }.joined(separator: " / ")
        return "已导入「\(config.title) \(config.version)」· \(config.lines.count) 条线路：\(names)"
    }

    /// 切换青听配置里某条线路的启用状态
    func toggleQingLine(_ lineId: String) {
        guard var config = qing,
              let index = config.lines.firstIndex(where: { $0.id == lineId }) else { return }
        config.lines[index].enabled.toggle()
        qing = config
        save(config, "qing")
    }

    func clearQing() {
        qing = nil
        try? FileManager.default.removeItem(at: url("qing"))
        show("已清除")
    }

    // MARK: - 下载记录
    func registerDownload(_ song: Song) {
        downloads.removeAll { $0.name == song.name && $0.displaySinger == song.displaySinger }
        downloads.insert(song, at: 0)
        save(downloads, "downloads")
    }

    func deleteDownload(_ song: Song) {
        if let path = song.localPath {
            try? FileManager.default.removeItem(atPath: path)
        }
        downloads.removeAll { $0.id == song.id }
        save(downloads, "downloads")
        show("已删除：\(song.name)")
    }

    /// 把磁盘上已有的文件并进列表（重启后仍可见）
    func refreshLocalDownloads() {
        let scanned = Downloader.shared.scanLocalSongs()
        var merged = downloads
        for song in scanned where !merged.contains(where: { $0.localPath == song.localPath }) {
            merged.append(song)
        }
        merged.removeAll { song in
            guard let path = song.localPath else { return false }
            return !FileManager.default.fileExists(atPath: path)
        }
        if merged.count != downloads.count { downloads = merged; save(downloads, "downloads") }
    }

    // MARK: - 播放封装
    func play(song: Song, queue: [Song]? = nil) {
        player.play(song: song, queue: queue ?? [song])
    }

    func playAll(_ songs: [Song], startAt index: Int = 0) {
        guard !songs.isEmpty else { show("歌单是空的"); return }
        player.play(song: songs[min(index, songs.count - 1)], queue: songs)
    }

    /// 取播放地址：青听网关（覆盖 QQ/咪咕/汽水/B站）→ 平台直连 → 自定义脚本 → 跨源兜底
    func resolveURL(for song: Song, quality: Quality) async throws -> URL {
        if song.source == .local, let path = song.localPath {
            return URL(fileURLWithPath: path)
        }

        // 1) 青听网关：和 Android 版同一条路，签名由 QingGateway 负责
        if let qing = self.qing {
            let line = qing.enabledLines.first { $0.sourceId == song.source }
            let level = line?.levels.first { Quality.fromLevel($0) == quality }
                ?? qualityLevel(for: song, quality: quality, line: line)
            if let url = try? await QingGateway.resolveURL(source: song.source.rawValue,
                                                          rid: gatewayRid(for: song),
                                                          level: level) {
                return url
            }
        }

        // 2) 平台直连：酷我 / 网易 / 酷狗
        if [.kw, .wy, .kg].contains(song.source),
           let url = try? await net.resolveURL(song: song, quality: quality) {
            return url
        }

        // 3) 自定义 lx 脚本
        for meta in scripts where meta.enabled && meta.sources.keys.contains(song.source.rawValue) {
            if let url = try? await engine.musicURL(meta: meta, song: song, quality: quality) {
                return url
            }
        }

        // 4) 最后兜底：同名歌换平台（正常不会走到）
        if let alt = await crossMatch(song: song),
           let url = try? await net.resolveURL(song: alt, quality: quality) {
            show("已改用\(alt.source.display)音源播放")
            return url
        }

        throw SourceError.noResolver("\(song.source.display)没有可用播放地址（网关与直连都失败）")
    }

    /// 网关用的歌曲 ID：QQ 用 songmid、酷我用 rid、酷狗用 hash
    private func gatewayRid(for song: Song) -> String {
        switch song.source {
        case .tx: return song.extra["mid"] ?? song.id
        case .kw: return song.extra["rid"] ?? song.id
        case .kg: return song.extra["hash"] ?? song.id
        default: return song.id
        }
    }

    /// 网关音质名：优先用配置里该线路支持的等级
    private func qualityLevel(for song: Song, quality: Quality, line: QingConfig.Line?) -> String {
        let name = Quality.levelName(for: quality)
        guard let levels = line?.levels, !levels.isEmpty else { return name }
        if levels.contains(name) { return name }
        if let mapped = levels.first(where: { Quality.fromLevel($0) == quality }) { return mapped }
        return levels.contains("exhigh") ? "exhigh" : (levels.first ?? name)
    }

    /// 跨平台找同名歌（用于 QQ/咪咕/汽水/B站 这类客户端拿不到地址的平台）
    private func crossMatch(song: Song) async -> Song? {
        let keyword = "\(song.name) \(song.displaySinger)"
        for source in [SourceId.kw, .wy, .kg] where source != song.source {
            guard let list = try? await net.search(source: source, keyword: keyword), !list.isEmpty else { continue }
            let normalized = song.name.replacingOccurrences(of: " ", with: "").lowercased()
            if let hit = list.first(where: {
                $0.name.replacingOccurrences(of: " ", with: "").lowercased() == normalized
            }) {
                return hit
            }
            if let first = list.first { return first }
        }
        return nil
    }

    func resolveLyric(for song: Song) async -> Lyric? {
        for meta in scripts where meta.enabled {
            if let lrc = try? await engine.lyric(meta: meta, song: song) {
                return Lyric.parse(lrc)
            }
        }
        if let lrc = try? await net.lyric(song: song) {
            return Lyric.parse(lrc)
        }
        return nil
    }
}

