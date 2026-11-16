import io
import os
import re

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ 1) AppStore：来源按优先级排序（小Q源永远第一） ============
a = os.path.join(root, "CarPlayer", "AppStore.swift")
s = io.open(a, encoding="utf-8").read()

old_sources = """    /// 可用来源：导入青听配置后以配置里的线路为准，否则是内置五平台
    var availableSources: [SourceId] {
        if let qing = self.qing {
            let list = qing.supportedSources
            if !list.isEmpty { return list }
        }
        return SourceId.searchOrder
    }"""
new_sources = """    /// 来源优先级：小Q源(tx) 永远排最前，其余按内置顺序，未知来源垫底
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
    }"""
assert old_sources in s, "sources anchor missing"
s = s.replace(old_sources, new_sources)

# 结果按来源优先级稳定排序
old_assign = """            searching = false
            searchResults = all"""
new_assign = """            searching = false
            // 稳定排序：小Q源结果永远在最前，其余按来源优先级
            searchResults = all.enumerated()
                .sorted { lhs, rhs in
                    let lp = sourcePriority(lhs.element.source)
                    let rp = sourcePriority(rhs.element.source)
                    return lp == rp ? lhs.offset < rhs.offset : lp < rp
                }
                .map { $0.element }"""
assert old_assign in s, "results anchor missing"
s = s.replace(old_assign, new_assign)
io.open(a, "w", encoding="utf-8").write(s)
print("AppStore: tx-first ordering")

# ============ 2) SettingsView：单一 sheet 容器 + 返回键加固 + 导入歌单弹窗重做 ============
p = os.path.join(root, "CarPlayer", "SettingsView.swift")
t = io.open(p, encoding="utf-8").read()

# 2.1 状态：加入 activeSheet
t = t.replace("""    @State private var showQuality = false
    @State private var showSourceSection = false""",
"""    @State private var activeSheet: SettingsSheet?
    @State private var showSourceSection = false""")

# 2.2 删除旧的布尔状态
for name in ["showScriptSheet", "showPlaylistImport", "showHelp", "showCrash"]:
    t = t.replace(f"    @State private var {name} = false\n", "")

# 2.3 定义 sheet 枚举（放在 struct 内部开头）
t = t.replace("""struct SettingsView: View {""",
"""enum SettingsSheet: String, Identifiable {
    case quality, script, playlistImport, help, crash
    var id: String { rawValue }
}

struct SettingsView: View {""")

# 2.4 把 5 个 .sheet 换成 1 个 item 驱动的
start = t.index("        .sheet(isPresented: $showQuality) {")
end = t.index("        .fileImporter(isPresented: $showFileImporter,")
new_sheets = """        .sheet(item: $activeSheet) { kind in
            Group {
                switch kind {
                case .quality:
                    QualityPickerSheet(title: "下载音质",
                                       options: Quality.downloadOptions,
                                       selected: store.settings.downloadQuality) { quality in
                        store.settings.downloadQuality = quality
                        store.persistAll()
                    }
                    .presentationDetents([.height(CGFloat(120 + Quality.downloadOptions.count * 50))])
                case .script:
                    scriptImportSheet.presentationDetents([.large])
                case .playlistImport:
                    playlistImportSheet.presentationDetents([.large])
                case .help:
                    helpSheet.presentationDetents([.large])
                case .crash:
                    crashSheet.presentationDetents([.medium])
                }
            }
        }
"""
t = t[:start] + new_sheets + t[end:]

# 2.5 各处按钮改用 activeSheet
t = t.replace("showScriptSheet = true", "activeSheet = .script")
t = t.replace("showPlaylistImport = true", "activeSheet = .playlistImport")
t = t.replace("showHelp = true", "activeSheet = .help")
t = t.replace("showCrash = true", "activeSheet = .crash")
t = t.replace("showQuality = true", "activeSheet = .quality")
t = t.replace("showScriptSheet = false", "activeSheet = nil")
t = t.replace("showPlaylistImport = false", "activeSheet = nil")

# 2.6 返回键加固：borderless + contentShape + 顶层兜底
t = t.replace("""            Button {
                router.screen = .main
            } label: {
                VectorIcon(icon: .back, size: 24, color: Palette.text).frame(width: 52, height: 52)
            }
            .buttonStyle(.plain)""",
"""            Button {
                closeSettings()
            } label: {
                VectorIcon(icon: .back, size: 24, color: Palette.text)
                    .frame(width: 64, height: 56)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("返回")""")

t = t.replace("""        .background(Palette.bg.ignoresSafeArea())
        .sheet(item: $activeSheet) { kind in""",
"""        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            // 兜底返回区：任何情况下都能退出去
            Color.clear
                .frame(width: 76, height: 64)
                .contentShape(Rectangle())
                .onTapGesture { closeSettings() }
        }
        .sheet(item: $activeSheet) { kind in""")

# 2.7 closeSettings 方法
t = t.replace("    // MARK: - header", """    private func closeSettings() {
        router.screen = .main
    }

    // MARK: - header""")

# 2.8 重做导入歌单弹窗：large + 底部固定按钮 + 全程反馈
start = t.index("    private var playlistImportSheet: some View {")
end = t.index("    private var helpSheet: some View {")
new_sheet = '''    private var playlistImportSheet: some View {
        sheetContainer(title: "粘贴歌单链接或 ID") {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    Text("支持网易云、QQ 音乐；公开歌单无需登录。")
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                    TextEditor(text: $playlistText)
                        .font(.system(size: 14))
                        .foregroundColor(Palette.text)
                        .scrollContentBackground(.hidden)
                        .frame(height: 160)
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: Radius.surface, style: .continuous).fill(Palette.surface))
                        .overlay(RoundedRectangle(cornerRadius: Radius.surface, style: .continuous).stroke(Palette.stroke, lineWidth: 1))
                        .scrollDismissesKeyboard(.interactively)
                    Button {
                        if let text = UIPasteboard.general.string {
                            playlistText = text
                            store.show("已粘贴 \\(text.count) 个字符")
                        } else {
                            store.show("剪贴板是空的")
                        }
                    } label: {
                        Text("从剪贴板粘贴")
                            .font(FType.chip())
                            .foregroundColor(Palette.text)
                            .frame(maxWidth: .infinity).frame(height: 44)
                            .surfaceCard()
                    }
                    .buttonStyle(.borderless)
                }
            }
            .frame(maxHeight: .infinity)
        }
        .safeAreaInset(edge: .bottom) {
            Button(action: importPlaylist) {
                Text(busy ? "正在导入…" : "导入歌单")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Palette.accent)
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Capsule().fill(Palette.accentFill))
                    .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
            }
            .buttonStyle(.borderless)
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

'''
t = t[:start] + new_sheet + t[end:]
io.open(p, "w", encoding="utf-8").write(t)
print("SettingsView: single sheet + back hardening + playlist sheet")

# ============ 3) importPlaylist：立即反馈 + 失败原因 ============
t = io.open(p, encoding="utf-8").read()
start = t.index("    private func importPlaylist() {")
end = t.index("\n    }\n", start) + len("\n    }\n")
new_import = '''    private func importPlaylist() {
        let text = playlistText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            store.show("请粘贴歌单链接或 ID")
            return
        }
        guard let (platform, id) = PlaylistImportPlatform.detect(text) else {
            store.show("未识别到歌单 ID（网易云 / QQ 公开歌单链接）")
            return
        }
        busy = true
        store.show("正在导入歌单…")
        Task { @MainActor in
            defer { busy = false }
            let songs = (try? await PlaylistImporter.fetch(platform: platform, id: id)) ?? []
            guard !songs.isEmpty else {
                store.show("歌单不存在、为空或需要登录")
                return
            }
            let playlist = Playlist(id: "\\(platform.rawValue)-\\(id)",
                                    name: "\\(platform.display) \\(id)",
                                    songs: songs,
                                    picUrl: songs.first?.picUrl,
                                    source: platform == .wy ? .wy : .tx,
                                    isRemote: true,
                                    trackCount: songs.count)
            store.replacePlaylist(playlist)
            store.show("已导入「\\(playlist.name)」· \\(songs.count) 首")
            activeSheet = nil
        }
    }
'''
t = t[:start] + new_import + t[end:]
io.open(p, "w", encoding="utf-8").write(t)
print("SettingsView: importPlaylist feedback")
