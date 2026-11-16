import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ---------- C) Playlist 增加 trackCount ----------
m = os.path.join(root, "CarPlayer", "Models.swift")
t = io.open(m, encoding="utf-8").read()
t = t.replace('''    var isRemote: Bool = false          // 远程导入歌单（网易云/QQ），不可删除以外行为一致''',
'''    var isRemote: Bool = false          // 远程导入歌单（网易云/QQ）
    var trackCount: Int = 0             // 远程歌单的曲目总数（未展开时显示用）''')
t = t.replace('''    var count: Int { songs.count }''',
'''    var count: Int { songs.isEmpty ? trackCount : songs.count }''')
io.open(m, "w", encoding="utf-8").write(t)
print("Models: Playlist.trackCount")

# ---------- D) AppStore ----------
a = os.path.join(root, "CarPlayer", "AppStore.swift")
s = io.open(a, encoding="utf-8").read()

# 搜索来源：qing lines ∩ 用户勾选
old = s[s.index("    /// 当前生效的搜索来源"):]
old = old[:old.index("\n    }\n") + len("\n    }\n")]
new = '''    /// 可用来源：导入青听配置后以配置里的线路为准，否则是内置五平台
    var availableSources: [SourceId] {
        if let qing = self.qing {
            let list = qing.supportedSources
            if !list.isEmpty { return list }
        }
        return SourceId.searchOrder
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
'''
s = s.replace(old, new)

# 导入青听配置后把这些平台并入 enabledSources
s = s.replace('''        qing = config
        save(config, "qing")
        let names = config.lines.map { $0.name }.joined(separator: " / ")''',
'''        qing = config
        save(config, "qing")
        var set = settings.enabledSources
        for source in config.supportedSources { set.insert(source) }
        settings.enabledSources = set
        save(settings, "settings")
        let names = config.lines.map { $0.name }.joined(separator: " / ")''')

# 热门歌单
s = s.replace('''    @Published var crashLog: String = ""''',
'''    @Published var crashLog: String = ""
    @Published var hotPlaylists: [Playlist] = []
    @Published var hotPlaylistLoading = false
    @Published var hotPlaylistError: String?''')

s = s.replace('''    func shuffleHot() {''',
'''    /// 首页「热门歌单」：网易云
    func loadHotPlaylists(force: Bool = false) {
        guard force || hotPlaylists.isEmpty, !hotPlaylistLoading else { return }
        hotPlaylistLoading = true
        hotPlaylistError = nil
        Task { @MainActor in
            let list = (try? await net.hotPlaylists(limit: 12)) ?? []
            hotPlaylistLoading = false
            if list.isEmpty {
                hotPlaylistError = "加载失败"
            } else {
                hotPlaylists = list
            }
        }
    }

    /// 点热门歌单：拉曲目 → 立即播放 → 返回可展示的 Playlist
    func openHotPlaylist(_ playlist: Playlist) async -> Playlist? {
        let rawId = playlist.id.hasPrefix("wy-") ? String(playlist.id.dropFirst(3)) : playlist.id
        let songs = (try? await net.wyPlaylistSongs(id: rawId)) ?? []
        guard !songs.isEmpty else {
            show("这个歌单没取到歌，换一个试试")
            return nil
        }
        var full = playlist
        full.songs = songs
        full.trackCount = songs.count
        replacePlaylist(full)
        playAll(songs)
        return full
    }

    func shuffleHot() {''')

# 歌词：走内置多平台
old_lyric = s[s.index("    func resolveLyric(for song: Song) async -> Lyric? {"):]
old_lyric = old_lyric[:old_lyric.index("\n    }\n") + len("\n    }\n")]
new_lyric = '''    func resolveLyric(for song: Song) async -> Lyric? {
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
'''
s = s.replace(old_lyric, new_lyric)
io.open(a, "w", encoding="utf-8").write(s)
print("AppStore: sources + hot playlists + lyric")
