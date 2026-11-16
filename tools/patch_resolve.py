import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "AppStore.swift")
t = io.open(p, encoding="utf-8").read()

start = t.index("    /// 取播放地址：脚本音源 → 青听网关 → 内置直连")
end = t.index("    func resolveLyric(for song: Song) async -> Lyric? {")
new = '''    /// 取播放地址：平台直连（快）→ 青听网关 → 自定义脚本 → 跨源兜底
    func resolveURL(for song: Song, quality: Quality) async throws -> URL {
        if song.source == .local, let path = song.localPath {
            return URL(fileURLWithPath: path)
        }

        // 1) 平台直连：酷我 / 网易 / 酷狗，几秒内出结果
        if [.kw, .wy, .kg].contains(song.source),
           let url = try? await net.resolveURL(song: song, quality: quality) {
            return url
        }

        // 2) 青听网关（只在拿到 ticket 时试，内部超时很短）
        if let qing = self.qing,
           let url = try? await QingGate.resolveURL(song: song, quality: quality, config: qing) {
            return url
        }

        // 3) 自定义 lx 脚本
        for meta in scripts where meta.enabled && meta.sources.keys.contains(song.source.rawValue) {
            if let url = try? await engine.musicURL(meta: meta, song: song, quality: quality) {
                return url
            }
        }

        // 4) 跨源兜底：QQ / 咪咕 / 汽水 / B站 没法在客户端出链，就换同名的酷我 / 网易曲目播
        if let alt = await crossMatch(song: song),
           let url = try? await net.resolveURL(song: alt, quality: quality) {
            show("已改用\\(alt.source.display)音源播放")
            return url
        }

        throw SourceError.noResolver("\\(song.source.display)没有可用播放地址，且没有找到可替代的同名歌曲")
    }

    /// 跨平台找同名歌（用于 QQ/咪咕/汽水/B站 这类客户端拿不到地址的平台）
    private func crossMatch(song: Song) async -> Song? {
        let keyword = "\\(song.name) \\(song.displaySinger)"
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

'''
t = t[:start] + new + t[end:]
io.open(p, "w", encoding="utf-8").write(t)
print("AppStore resolveURL rewritten:", len(t), "chars")
print("  crossMatch:", "private func crossMatch" in t)
