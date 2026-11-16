import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "Models.swift")
t = io.open(p, encoding="utf-8").read()

# 1) SourceId 增加 bili
t = t.replace('''enum SourceId: String, Codable, CaseIterable, Identifiable {
    case kw, kg, tx, wy, mg, qs, local''',
'''enum SourceId: String, Codable, CaseIterable, Identifiable {
    case kw, kg, tx, wy, mg, qs, bili, local''')

t = t.replace('''        case .qs: return "汽水"
        case .local: return "本地"''',
'''        case .qs: return "汽水"
        case .bili: return "哔哩哔哩"
        case .local: return "本地"''')

# 2) 青听配置里的 line id → SourceId
t = t.replace('''    /// SourceEngine 的展示顺序：kw 搜索结果最全 → wy → tx → mg → kg → 聚合
    static let searchOrder: [SourceId] = [.kw, .wy, .tx, .mg, .kg]''',
'''    /// SourceEngine 的展示顺序：kw 搜索结果最全 → wy → tx → mg → kg
    static let searchOrder: [SourceId] = [.kw, .wy, .tx, .mg, .kg]

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
    }''')

# 3) Quality：网关等级名互转
t = t.replace('''    static func fromLxKey(_ key: String) -> Quality? {
        Quality.allCases.first { $0.lxKey == key }
    }''',
'''    static func fromLxKey(_ key: String) -> Quality? {
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
    }''')

io.open(p, "w", encoding="utf-8").write(t)
print("Models.swift patched:", len(t), "chars")
print("  bili:", "case .bili: return" in t, "| qingLineId:", "init?(qingLineId" in t, "| fromLevel:", "static func fromLevel" in t)
