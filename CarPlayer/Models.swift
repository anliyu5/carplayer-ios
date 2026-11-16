import Foundation

// 与 Android 侧 com.carplayer.data.Song / Playlist / HistoryEntry 字段一一对应
enum SourceId: String, Codable, CaseIterable, Identifiable {
    case kw, kg, tx, wy, mg, qs, bili, local
    var id: String { rawValue }

    /// 音源中文名，取自 aria/字符串表
    var display: String {
        switch self {
        case .kw: return "酷我"
        case .kg: return "酷狗"
        case .tx: return "QQ"
        case .wy: return "网易"
        case .mg: return "咪咕"
        case .qs: return "汽水"
        case .bili: return "哔哩哔哩"
        case .local: return "本地"
        }
    }

    /// SourceEngine 的展示顺序：kw 搜索结果最全 → wy → tx → mg → kg
    static let searchOrder: [SourceId] = [.tx, .kw, .wy, .mg, .kg]   // 小Q源排最前

    /// 青听 music.json 的 line id（小写别名）→ SourceId
    init?(qingLineId: String) {
        switch qingLineId.lowercased() {
        case "kw", "kuwo": self = .kw
        case "kg", "kugou": self = .kg
        case "tx", "qq": self = .tx
        case "wy", "netease": self = .wy
        case "mg", "migu": self = .mg
        case "qs", "qishui": self = .qs
        case "bili", "bilibili": self = .bili
        case "local": self = .local
        default: return nil
        }
    }
}

enum Quality: String, Codable, CaseIterable, Identifiable {
    case k128, k320, flac, flac24bit, hires, atmos, master, atmos_plus, spatial
    var id: String { rawValue }

    var display: String {
        switch self {
        case .k128: return "标准 128K"
        case .k320: return "较高 320K"
        case .flac: return "无损 FLAC"
        case .flac24bit: return "超清母带FLAC"
        case .hires: return "高清环绕"
        case .atmos: return "全景声"
        case .master: return "母带"
        case .atmos_plus: return "全景声 Plus"
        case .spatial: return "沉浸环绕"
        }
    }

    /// 列表右侧音质角标（songQuality）
    var badge: String {
        switch self {
        case .k128: return "128K"
        case .k320: return "320K"
        case .flac: return "FLAC"
        case .flac24bit: return "24bit"
        case .hires: return "Hi-Res"
        case .atmos: return "全景声"
        case .master: return "母带"
        case .atmos_plus: return "全景声+"
        case .spatial: return "空间"
        }
    }

    /// lx 脚本用的音质 key
    var lxKey: String {
        switch self {
        case .k128: return "128k"
        case .k320: return "320k"
        case .flac: return "flac"
        case .flac24bit: return "flac24bit"
        case .hires: return "hires"
        case .atmos: return "atmos"
        case .master: return "master"
        case .atmos_plus: return "atmos_plus"
        case .spatial: return "spatial"
        }
    }

    static func fromLxKey(_ key: String) -> Quality? {
        Quality.allCases.first { $0.lxKey == key }
    }

    /// 青听 music.json 的 levels 名称
    static func fromLevel(_ level: String) -> Quality? {
        switch level.lowercased() {
        case "standard", "128k": return .k128
        case "exhigh", "320k", "higher": return .k320
        case "lossless", "flac", "bili192": return .flac
        case "hires": return .hires
        case "atmos": return .atmos
        case "atmos_plus", "clear": return .atmos_plus
        case "master", "jymaster": return .master
        case "sky", "sur", "jyeffect", "spatial": return .spatial
        default: return nil
        }
    }

    static func levelName(for quality: Quality) -> String {
        switch quality {
        case .k128: return "standard"
        case .k320: return "exhigh"
        case .flac, .flac24bit: return "lossless"
        case .hires: return "hires"
        case .atmos: return "atmos"
        case .atmos_plus: return "atmos_plus"
        case .master: return "master"
        case .spatial: return "sky"
        }
    }

    /// 下载音质档位（设置页「下载音质」）
    static let downloadOptions: [Quality] = [.k320, .flac, .flac24bit, .master]
}

struct Song: Identifiable, Codable, Hashable {
    var id: String                    // 平台原始 ID
    var source: SourceId
    var name: String
    var singer: String
    var albumName: String?
    var picUrl: String?
    var interval: Double              // 秒
    var qualitys: [Quality]
    var localPath: String?
    /// 平台附加字段（songmid / hash / copyrightId / rid …），各音源解析时自行取用
    var extra: [String: String] = [:]

    var displaySinger: String { singer.isEmpty ? "未知歌手" : singer }
    var displayAlbum: String { (albumName?.isEmpty == false) ? albumName! : "未知专辑" }
    var bestQuality: Quality? { qualitys.max(by: { Quality.allCases.firstIndex(of: $0)! < Quality.allCases.firstIndex(of: $1)! }) }
    var isLocal: Bool { source == .local }
}

struct Playlist: Identifiable, Codable, Hashable {
    var id: String
    var name: String
    var songs: [Song]
    var picUrl: String?
    var source: SourceId = .local
    var isFavorite: Bool = false
    var isRemote: Bool = false          // 远程导入歌单（网易云/QQ）
    var trackCount: Int = 0             // 远程歌单的曲目总数（未展开时显示用）

    var count: Int { songs.isEmpty ? trackCount : songs.count }
    var subtitle: String {
        let owner = source == .local ? "我的歌单" : "\(source.display)歌单"
        return "\(owner) · \(count) 首"
    }
}

struct HistoryEntry: Identifiable, Codable, Hashable {
    var id: String { song.id + "-" + source + "-" + String(time.timeIntervalSince1970) }
    var song: Song
    var source: String
    var time: Date

    enum CodingKeys: String, CodingKey { case song, source, time }
}

struct SearchRow: Identifiable, Codable, Hashable {
    var id: String { song.source.rawValue + ":" + song.id }
    var song: Song
    var index: Int
}

enum PlayMode: String, Codable, CaseIterable {
    case order, repeatOne, shuffle
    var display: String {
        switch self {
        case .order: return "顺序播放"
        case .repeatOne: return "单曲循环"
        case .shuffle: return "随机播放"
        }
    }
    var icon: Icon {
        switch self {
        case .order: return .repeatAll
        case .repeatOne: return .repeatOne
        case .shuffle: return .shuffle
        }
    }
    var next: PlayMode {
        switch self {
        case .order: return .repeatOne
        case .repeatOne: return .shuffle
        case .shuffle: return .order
        }
    }
}

/// 导入后的音源脚本元数据（对应 ScriptMeta / SourceCap）
struct ScriptMeta: Codable, Hashable, Identifiable {
    var id: String            // sha1
    var name: String
    var version: String
    var author: String
    var description: String
    var homepage: String
    var sources: [String: [String]]   // source -> qualitys
    var enabled: Bool = true
    var script: String
    var initedAt: Date = Date()
}

/// 歌单导入用的平台
enum PlaylistImportPlatform: String {
    case wy, tx
    var display: String { self == .wy ? "网易云歌单" : "QQ 歌单" }

    /// 从链接/分享文本里解析歌单 ID（兼容路径式、query 式、短链、纯数字）
    static func detect(_ text: String) -> (PlaylistImportPlatform, String)? {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return nil }

        let lower = t.lowercased()
        // 1) QQ 音乐
        if lower.contains("qq.com") {
            if let id = firstID(in: t, pattern: #"playlist/(\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: t, pattern: #"[?&](?:id|disstid|songlistid)=(\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: t, pattern: #"(?:disstid|songlistid)=(\d{4,})"#) { return (.tx, id) }
        }
        // 2) 网易云（含 y.music.163.com、music.163.com/…、163cn.tv 短链）
        if lower.contains("163.com") || lower.contains("163cn.tv") {
            if let id = firstID(in: t, pattern: #"/playlist/(\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: t, pattern: #"[?&]id=(\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: t, pattern: #"playlist[^\s]*?id=(\d{4,})"#) { return (.wy, id) }
        }
        // 3) 纯数字：先按网易试，失败由上层退回 QQ
        if t.count >= 4, t.allSatisfy({ $0.isNumber }) { return (.wy, t) }
        return nil
    }

    /// 短链识别：先按原文匹配，不行就跟随 302 跳转，再按跳转后的网址 / 落地页识别
    static func resolve(_ text: String) async -> (PlaylistImportPlatform, String)? {
        if let hit = detect(text) { return hit }
        guard let urlString = firstURL(in: text), let url = URL(string: urlString) else { return nil }
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        guard let (data, response) = try? await URLSession.shared.data(for: request) else { return nil }
        let final = response.url?.absoluteString ?? ""
        if let hit = detect(final) { return hit }

        // 落地页里抠：网易 playlist?id=… / QQ playlist/<id>
        let html = String(data: data, encoding: .utf8) ?? ""
        if final.contains("qq.com") || urlString.contains("qq.com") {
            if let id = firstID(in: final, pattern: #"playlist/(\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: html, pattern: #"playlist/(\d{4,})"#) { return (.tx, id) }
            if let id = firstID(in: final, pattern: #"[?&]id=(\d{4,})"#) { return (.tx, id) }
        } else {
            if let id = firstID(in: final, pattern: #"[?&]id=(\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: html, pattern: #"playlist[^"'\s]*?[?&]id=(\d{4,})"#) { return (.wy, id) }
            if let id = firstID(in: html, pattern: #"[?&]id=(\d{6,})"#) { return (.wy, id) }
        }
        return nil
    }

    private static func firstURL(in text: String) -> String? {
        guard let range = text.range(of: #"https?://[^\s"'<>]+"#, options: .regularExpression) else { return nil }
        return String(text[range])
    }

    private static func firstID(in text: String, pattern: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let ns = text as NSString
        guard let match = regex.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)),
              match.numberOfRanges >= 2 else { return nil }
        let range = match.range(at: 1)
        guard range.location != NSNotFound else { return nil }
        return ns.substring(with: range)
    }
}
