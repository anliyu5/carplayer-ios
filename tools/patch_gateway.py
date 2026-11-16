import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ---- 1) AppStore：播放地址改为 青听网关 → 平台直连 → 脚本 → 跨源 ----
p = os.path.join(root, "CarPlayer", "AppStore.swift")
t = io.open(p, encoding="utf-8").read()
start = t.index("    /// 取播放地址：平台直连（快）→ 青听网关 → 自定义脚本 → 跨源兜底")
end = t.index("    /// 跨平台找同名歌")
new = '''    /// 取播放地址：青听网关（覆盖 QQ/咪咕/汽水/B站）→ 平台直连 → 自定义脚本 → 跨源兜底
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
            show("已改用\\(alt.source.display)音源播放")
            return url
        }

        throw SourceError.noResolver("\\(song.source.display)没有可用播放地址（网关与直连都失败）")
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

'''
t = t[:start] + new + t[end:]

# 歌词：网关没有歌词接口，走脚本/直连
t = t.replace('''        if let qing = self.qing, let lrc = try? await QingGate.lyric(song: song, config: qing) {
            return Lyric.parse(lrc)
        }
''', "")
io.open(p, "w", encoding="utf-8").write(t)
print("AppStore wired to QingGateway:", len(t), "chars")

# ---- 2) QingGate.swift：删掉旧的 ticket/resolve/lyric 实现，只留配置与 JSON 工具 ----
q = os.path.join(root, "CarPlayer", "QingGate.swift")
s = io.open(q, encoding="utf-8").read()
cut = s.index("// MARK: - 青听网关")
end_marker = "// MARK: - 容错 JSON 读取工具（网关返回结构随版本变化）"
keep_json = s[s.index(end_marker):]
s = s[:cut] + keep_json
# 去掉 withTimeout（已不再使用）
io.open(q, "w", encoding="utf-8").write(s)
print("QingGate trimmed to config + JSON helpers:", len(s), "chars")
