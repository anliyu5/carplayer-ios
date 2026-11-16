import SwiftUI
import UIKit
import UniformTypeIdentifiers
/// 设置页：对齐 activity_settings（res/q3.xml）
enum SettingsSheet: String, Identifiable {
    case quality, script, playlistImport, help, crash
    var id: String { rawValue }
}

struct SettingsView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router
    @ObservedObject private var downloader = Downloader.shared

    @State private var activeSheet: SettingsSheet?
    @State private var showSourceSection = false
    @State private var showMoreSection = false
    @State private var scriptText = ""
    @State private var playlistText = ""
    @State private var busy = false
    @State private var sheetStatus: String?
    @State private var showFileImporter = false
    @State private var importingScriptFile = false

    private var scriptedSources: [ScriptMeta] { store.scripts }

    var body: some View {
        VStack(spacing: 0) {
            header
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    downloadSection
                    sourceSectionToggle
                    if showSourceSection { sourceSection }
                    importPlaylistRow
                    moreToggle
                    if showMoreSection { moreSection }
                    versionRow
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 28)
            }
        }
        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            // 兜底返回区：任何情况下都能退出去
            Color.clear
                .frame(width: 76, height: 64)
                .contentShape(Rectangle())
                .onTapGesture { closeSettings() }
        }
        .sheet(item: $activeSheet) { kind in
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
        .fileImporter(isPresented: $showFileImporter,
                      allowedContentTypes: [.json, .plainText, .data],
                      allowsMultipleSelection: false) { result in
            guard case .success(let urls) = result, let url = urls.first else { return }
            let scoped = url.startAccessingSecurityScopedResource()
            defer { if scoped { url.stopAccessingSecurityScopedResource() } }
            guard let text = try? String(contentsOf: url, encoding: .utf8) else {
                store.show("读取文件失败，换个文件试试")
                return
            }
            scriptText = text
            importingScriptFile = true
        }
    }

    private func closeSettings() {
        router.screen = .main
    }

    // MARK: - header
    private var header: some View {
        HStack(spacing: 6) {
            Button {
                closeSettings()
            } label: {
                VectorIcon(icon: .back, size: 24, color: Palette.text)
                    .frame(width: 64, height: 56)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("返回")
            Text("设置")
                .font(FType.h2())
                .foregroundColor(Palette.text)
            Spacer(minLength: 0)
            Button {
                activeSheet = .script
            } label: {
                Text("导入音源")
                    .font(FType.body())
                    .foregroundColor(Palette.accent)
                    .padding(.horizontal, 18)
                    .frame(height: 40)
                    .background(Capsule().fill(Palette.accentFill))
                    .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
            }
            .buttonStyle(.plain)
        }
        .frame(height: 64)
        .padding(.leading, 8)
        .padding(.trailing, 16)
    }

    // MARK: - 下载管理
    private var downloadSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text("下载管理")
                    .font(FType.sectionSm())
                    .foregroundColor(Palette.text)
                Spacer()
                Text("保存在 文件 → CarPlayer/Music")
                    .font(FType.subSm())
                    .foregroundColor(Palette.textSub)
            }
            settingRow(title: "下载音质", value: store.settings.downloadQuality.display) {
                activeSheet = .quality
            }
            settingRow(title: "启动时自动播放", value: store.settings.autoPlayOnLaunch ? "已开启" : "已关闭") {
                store.settings.autoPlayOnLaunch.toggle()
                store.persistAll()
            }
            settingRow(title: "开机自动启动", value: store.settings.bootAutoStart ? "已开启" : "已关闭") {
                store.settings.bootAutoStart.toggle()
                store.persistAll()
            }
            if store.settings.bootAutoStart {
                Text("开机后会自动打开 Music。（iOS 无第三方自启动权限，实际由「车机 CarPlay 自动启动上次播放」实现）")
                    .font(FType.subSm())
                    .foregroundColor(Palette.textSub)
                    .padding(.top, 6)
                    .padding(.horizontal, 4)
            }

            if store.downloads.isEmpty && downloader.jobs.isEmpty {
                Text("还没有下载过音乐")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .surfaceCard()
                    .padding(.top, 8)
            } else {
                VStack(spacing: 0) {
                    ForEach(downloader.jobs) { job in
                        HStack {
                            Text(job.song.name).font(FType.chip()).foregroundColor(Palette.text).lineLimit(1)
                            Spacer()
                            Text(job.state.rawValue)
                                .font(FType.tiny())
                                .foregroundColor(job.state == .failed ? Palette.danger : Palette.textSub)
                        }
                        .padding(.vertical, 6)
                    }
                    ForEach(store.downloads) { song in
                        HStack {
                            Text(song.name)
                                .font(FType.chip())
                                .foregroundColor(Palette.text)
                                .lineLimit(1)
                            Spacer()
                            Text("已下载")
                                .font(FType.tiny())
                                .foregroundColor(Palette.accent)
                            Button {
                                Downloader.shared.deleteLocalFile(song)
                                store.deleteDownload(song)
                            } label: {
                                VectorIcon(icon: .delete, size: 16, color: Palette.danger)
                                    .frame(width: 36, height: 36)
                                    .contentShape(Rectangle())
                            }
                            .buttonStyle(.borderless)
                        }
                        .padding(.vertical, 2)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .surfaceCard()
                .padding(.top, 8)
            }

            Button {
                router.screen = .downloads
            } label: {
                Text("查看下载列表")
                    .font(FType.chip())
                    .foregroundColor(Palette.textSub)
                    .frame(maxWidth: .infinity)
                    .frame(height: 40)
                    .background(Capsule().fill(Palette.surface2))
            }
            .buttonStyle(.plain)
            .padding(.top, 8)
        }
    }

    private func settingRow(title: String, value: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Text(title).font(FType.body()).foregroundColor(Palette.text)
                Spacer()
                Text(value).font(FType.chip()).foregroundColor(Palette.textSub)
            }
            .padding(.horizontal, 16)
            .frame(height: 52)
            .surfaceCard()
            .padding(.top, 8)
        }
        .buttonStyle(.plain)
    }

    // MARK: - 音源
    private var sourceSectionToggle: some View {
        Button {
            withAnimation(.easeOut(duration: 0.18)) { showSourceSection.toggle() }
        } label: {
            HStack(spacing: 10) {
                Text("音源").font(FType.rowTitle().bold()).foregroundColor(Palette.text)
                Text(sourceSummary)
                    .font(FType.subSm())
                    .foregroundColor(Palette.textSub)
                    .lineLimit(1)
                    .frame(maxWidth: .infinity, alignment: .leading)
                VectorIcon(icon: showSourceSection ? .chevron : .next, size: 20, color: Palette.textSub.opacity(0.6))
            }
            .padding(.horizontal, 16)
            .frame(height: 56)
            .surfaceCard()
            .padding(.top, 22)
        }
        .buttonStyle(.plain)
    }

    private var sourceSummary: String {
        if let qing = store.qing { return "青听 · \(qing.title) · \(qing.lines.count) 条线路" }
        if !scriptedSources.isEmpty { return scriptedSources.map { $0.name }.joined(separator: " / ") }
        return "未配置"
    }

    private var sourceSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            if let qing = store.qing {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(alignment: .top, spacing: 12) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("\(qing.title) \(qing.version)")
                                .font(FType.body())
                                .foregroundColor(Palette.text)
                            Text("\(qing.lines.count) 条线路 · 网关 \(qing.gatewayBase)")
                                .font(FType.subSm())
                                .foregroundColor(Palette.textSub)
                                .lineLimit(1)
                        }
                        Spacer(minLength: 0)
                        Button {
                            store.clearQing()
                        } label: {
                            Text("清除")
                                .font(FType.subSm())
                                .foregroundColor(Palette.danger)
                                .padding(.horizontal, 12)
                                .frame(height: 30)
                                .background(Capsule().fill(Palette.surface2))
                        }
                        .buttonStyle(.plain)
                    }

                    ForEach(qing.lines) { line in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(line.enabled ? Palette.accent : Palette.textSub.opacity(0.4))
                                .frame(width: 6, height: 6)
                            Text(line.name)
                                .font(FType.sub())
                                .foregroundColor(line.enabled ? Palette.text : Palette.textSub)
                            Text(line.id)
                                .font(FType.tiny())
                                .foregroundColor(Palette.textSub)
                            Spacer(minLength: 6)
                            Text(line.levelsText)
                                .font(FType.tiny())
                                .foregroundColor(Palette.textSub)
                                .lineLimit(1)
                            Toggle("", isOn: Binding(
                                get: { line.enabled },
                                set: { _ in store.toggleQingLine(line.id) }))
                            .labelsHidden()
                            .tint(Palette.accent)
                        }
                        .padding(.horizontal, 10)
                        .frame(height: 38)
                        .background(RoundedRectangle(cornerRadius: 10, style: .continuous).fill(Palette.surface2))
                    }
                }
                .padding(14)
                .surfaceCard()
            }

            ForEach(scriptedSources) { meta in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(meta.name).font(FType.body()).foregroundColor(Palette.text)
                        Spacer()
                        Text(meta.enabled ? "已启用" : "已停用")
                            .font(FType.tiny())
                            .foregroundColor(meta.enabled ? Palette.accent : Palette.textSub)
                    }
                    Text("支持 \(meta.sources.keys.sorted().joined(separator: " / "))  ·  v\(meta.version)")
                        .font(FType.subSm())
                        .foregroundColor(Palette.textSub)
                    HStack(spacing: 8) {
                        Button {
                            if let index = store.scripts.firstIndex(where: { $0.id == meta.id }) {
                                store.scripts[index].enabled.toggle()
                                store.persistAll()
                            }
                        } label: {
                            Text(meta.enabled ? "停用" : "启用")
                                .font(FType.tiny())
                                .foregroundColor(Palette.textSub)
                                .padding(.horizontal, 10)
                                .frame(height: 26)
                                .background(Capsule().fill(Palette.surface2))
                        }
                        .buttonStyle(.plain)
                        Button {
                            store.removeScript(meta)
                        } label: {
                            Text("删除音源")
                                .font(FType.tiny())
                                .foregroundColor(Palette.danger)
                                .padding(.horizontal, 10)
                                .frame(height: 26)
                                .background(Capsule().fill(Palette.surface2))
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(.top, 2)
                }
                .padding(14)
                .surfaceCard()
            }

            if scriptedSources.isEmpty && store.qing == nil {
                Text("还没有音源。点右上角「导入音源」，把青听的 music.json 网址或 .js 脚本导进来即可。")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .lineSpacing(3)
                    .padding(14)
                    .surfaceCard()
            }

            Text("点右上角「导入音源」：可粘贴 .js 脚本、青听 music.json 的网址或整段 JSON，也能从文件里选。")
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .padding(.horizontal, 4)
                .padding(.top, 6)

        }
        .padding(.top, 8)
    }

    // MARK: - 导入歌单
    private var importPlaylistRow: some View {
        Button {
            activeSheet = .playlistImport
        } label: {
            HStack {
                Text("导入歌单").font(FType.rowTitle()).foregroundColor(Palette.text)
                Spacer()
                Text("QQ / 网易云链接").font(FType.subSm()).foregroundColor(Palette.textSub)
                VectorIcon(icon: .plus, size: 18, color: Palette.textSub.opacity(0.6))
                    .padding(.leading, 8)
            }
            .padding(.horizontal, 16)
            .frame(height: 56)
            .surfaceCard()
            .padding(.top, 10)
        }
        .buttonStyle(.plain)
    }

    // MARK: - 更多设置
    private var moreToggle: some View {
        Button {
            withAnimation(.easeOut(duration: 0.18)) { showMoreSection.toggle() }
        } label: {
            HStack {
                Text("更多设置").font(FType.rowTitle()).foregroundColor(Palette.text)
                Spacer()
                Text("搜索范围 · 诊断").font(FType.subSm()).foregroundColor(Palette.textSub)
                VectorIcon(icon: showMoreSection ? .chevron : .next, size: 20, color: Palette.textSub.opacity(0.6))
                    .padding(.leading, 8)
            }
            .padding(.horizontal, 16)
            .frame(height: 56)
            .surfaceCard()
            .padding(.top, 10)
        }
        .buttonStyle(.plain)
    }

    private var moreSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("搜索范围")
                .font(FType.body().bold())
                .foregroundColor(Palette.text)
                .padding(.top, 16)
            Text("只影响搜索和歌单导入，与播放无关。")
                .font(FType.subSm())
                .foregroundColor(Palette.textSub)
                .padding(.top, 4)
            VStack(spacing: 8) {
                ForEach(SourceId.searchOrder) { source in
                    HStack {
                        Text(source.display).font(FType.body()).foregroundColor(Palette.text)
                        Spacer()
                        Toggle("", isOn: Binding(
                            get: { store.settings.enabledSources.contains(source) },
                            set: { on in
                                var set = store.settings.enabledSources
                                if on { set.insert(source) } else {
                                    if set.count <= 1 { store.show("至少保留一个搜索来源"); return }
                                    set.remove(source)
                                }
                                store.settings.enabledSources = set
                                store.persistAll()
                            }))
                        .labelsHidden()
                        .tint(Palette.accent)
                    }
                    .padding(.horizontal, 16)
                    .frame(height: 46)
                    .surfaceCard()
                }
            }
            .padding(.top, 8)

            Text("诊断")
                .font(FType.body().bold())
                .foregroundColor(Palette.text)
                .padding(.top, 16)
            Text(diagnosisText)
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .lineSpacing(2)
                .padding(14)
                .frame(maxWidth: .infinity, alignment: .leading)
                .surfaceCard()
                .padding(.top, 8)

            Button {
                activeSheet = .crash
            } label: {
                Text("查看上次崩溃日志")
                    .font(FType.body())
                    .foregroundColor(Palette.text)
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .surfaceCard()
                    .padding(.top, 8)
            }
            .buttonStyle(.plain)
        }
    }

    private var diagnosisText: String {
        var parts: [String] = []
        if let error = QingDebug.lastError { parts.append("音源：" + error) }
        if !store.crashLog.isEmpty { parts.append(String(store.crashLog.prefix(200))) }
        if parts.isEmpty { parts.append("没有崩溃记录") }
        return parts.joined(separator: "\n")
    }

    private var versionRow: some View {
        Text("Music iOS 1.9.14 (build 27) · 适配自 Android com.carplayer.music")
            .font(FType.subSm())
            .foregroundColor(Palette.textSub)
            .frame(maxWidth: .infinity)
            .padding(.top, 22)
    }

    // MARK: - 弹窗
    private var scriptImportSheet: some View {
        sheetContainer(title: "导入音源") {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    Text("三选一：① 青听 music.json 的网址　② .js 音源脚本的全部内容　③ 上面两者的网址。导入时会自动识别类型。")
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                    TextEditor(text: $scriptText)
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundColor(Palette.text)
                        .scrollContentBackground(.hidden)
                        .frame(height: 220)
                        .padding(8)
                        .background(RoundedRectangle(cornerRadius: Radius.surface, style: .continuous).fill(Palette.surface))
                        .overlay(RoundedRectangle(cornerRadius: Radius.surface, style: .continuous).stroke(Palette.stroke, lineWidth: 1))
                        .scrollDismissesKeyboard(.interactively)
                    HStack(spacing: 10) {
                        Button {
                            if let text = UIPasteboard.general.string {
                                scriptText = text
                                store.show("已粘贴 \(text.count) 个字符")
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

                        Button {
                            showFileImporter = true
                        } label: {
                            Text("从文件")
                                .font(FType.chip())
                                .foregroundColor(Palette.text)
                                .frame(maxWidth: .infinity).frame(height: 44)
                                .surfaceCard()
                        }
                        .buttonStyle(.borderless)
                    }
                }
            }
            .frame(maxHeight: .infinity)
        }
        .safeAreaInset(edge: .bottom) {
            VStack(spacing: 8) {
                if let sheetStatus {
                    Text(sheetStatus)
                        .font(FType.subSm())
                        .foregroundColor(sheetStatus.hasPrefix("已导入") ? Palette.accent : Palette.danger)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: .infinity)
                }
                Button(action: importScript) {
                Text(busy ? "正在导入…" : "导入")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Palette.accent)
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Capsule().fill(Palette.accentFill))
                    .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
            }
                .buttonStyle(.borderless)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

    private var playlistImportSheet: some View {
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
                            store.show("已粘贴 \(text.count) 个字符")
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
            VStack(spacing: 8) {
                if let sheetStatus {
                    Text(sheetStatus)
                        .font(FType.subSm())
                        .foregroundColor(sheetStatus.hasPrefix("已导入") ? Palette.accent : Palette.danger)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: .infinity)
                }
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
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

    private var helpSheet: some View {
        sheetContainer(title: "音源脚本从哪来") {
            ScrollView {
                Text("""
                本应用用的是 LX 自定义源脚本（.js 单文件）。

                1. 从你之前给青听用的那份音源脚本里拿（青听能用的这里都能用）；
                2. 或者找分享的 LX / 洛雪自定义源 .js 文件；
                3. 拿到后用「导入音源」选中即可，导入时会立刻校验能不能跑通。

                脚本支持哪些平台、哪些音质，导入后会在列表里直接写出来。
                """)
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .lineSpacing(4)
            }
            Spacer(minLength: 0)
        }
    }

    private var crashSheet: some View {
        sheetContainer(title: "上次崩溃日志") {
            ScrollView {
                Text(store.crashLog.isEmpty ? "没有崩溃记录" : store.crashLog)
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(Palette.textSub)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            Button {
                UIPasteboard.general.string = store.crashLog
                store.show("已复制，发给我即可定位")
            } label: {
                Text("复制")
                    .font(FType.chip())
                    .foregroundColor(Palette.accent)
                    .frame(maxWidth: .infinity).frame(height: 44)
                    .background(Capsule().fill(Palette.accentFill))
            }
            .buttonStyle(.plain)
            .padding(.top, 10)
        }
    }

    private func sheetContainer<Content: View>(title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(title)
                .font(FType.sectionSm())
                .foregroundColor(Palette.text)
                .padding(.bottom, 14)
            content()
            Spacer(minLength: 0)
        }
        .padding(20)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Palette.sheet.ignoresSafeArea())
    }

    // MARK: - 行为
    private func importScript() {
        let text = scriptText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            store.show("请先粘贴音乐源配置网址或脚本内容")
            return
        }
        busy = true
        store.show("正在导入…")
        Task { @MainActor in
            defer { busy = false }
            // 1) 网址：先下载，再按内容判断是 music.json 还是 .js
            if text.hasPrefix("http") {
                guard let url = URL(string: text) else {
                    store.show("请输入 http/https 网址")
                    return
                }
                var request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 20)
                request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
                guard let (data, _) = try? await URLSession.shared.data(for: request),
                      let body = String(data: data, encoding: .utf8), !body.isEmpty else {
                    store.show("下载失败，检查网址后重试")
                    return
                }
                if body.contains("lx.sources") || body.contains("lx.on") {
                    let message = await store.importScript(text: body)
                    store.show(message)
                } else {
                    let message = await store.importQing(json: body, sourceURL: text)
                    store.show(message)
                }
                activeSheet = nil
                return
            }
            // 2) 文本：含 lines → 青听配置；否则按 .js 脚本
            if text.contains("\"lines\"") || text.contains("/**") || text.contains("lines\":") {
                let message = await store.importQing(json: text)
                store.show(message)
            } else {
                let message = await store.importScript(text: text)
                store.show(message)
            }
            activeSheet = nil
        }
    }

    private func importPlaylist() {
        let text = playlistText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            sheetStatus = "请粘贴歌单链接或 ID"
            store.show("请粘贴歌单链接或 ID")
            return
        }
        busy = true
        sheetStatus = "正在识别歌单链接…"
        store.show("正在识别歌单链接…")
        Task { @MainActor in
            defer { busy = false }
            guard let (platform, id) = await PlaylistImportPlatform.resolve(text) else {
                sheetStatus = "没识别到歌单 ID：支持 163cn.tv 短链、music.163.com/playlist?id=…、y.qq.com/…/playlist/…"
                store.show("未识别到歌单 ID")
                return
            }
            sheetStatus = "正在导入歌单…"
            store.show("正在导入歌单…")
            var result = try? await PlaylistImporter.fetch(platform: platform, id: id)
            // 纯数字时平台可能猜错：另一个平台再试一次
            if result == nil {
                let other: PlaylistImportPlatform = platform == .wy ? .tx : .wy
                result = try? await PlaylistImporter.fetch(platform: other, id: id)
            }
            guard let imported = result, !imported.songs.isEmpty else {
                sheetStatus = "歌单取不到歌曲：可能不存在、为空、或需要登录"
                store.show("歌单不存在、为空或需要登录")
                return
            }
            let playlist = Playlist(id: "\(platform.rawValue)-\(id)",
                                    name: imported.name,
                                    songs: imported.songs,
                                    picUrl: imported.cover,
                                    source: platform == .wy ? .wy : .tx,
                                    isRemote: true,
                                    trackCount: imported.songs.count)
            store.replacePlaylist(playlist)
            sheetStatus = "已导入「\(imported.name)」· \(imported.songs.count) 首"
            store.show("已导入「\(imported.name)」· \(imported.songs.count) 首")
            activeSheet = nil
        }
    }
}

/// 歌单导入（网易云 / QQ 公开歌单）
struct ImportedPlaylist {
    var name: String
    var cover: String?
    var songs: [Song]
}

enum PlaylistImporter {
    /// 网易云单曲（兼容 al/ar 与 album/artists 两种字段）
    static func wySong(from item: [String: Any]) -> Song? {
        guard let sid = item["id"].map({ "\($0)" }) else { return nil }
        let artists = (item["ar"] as? [[String: Any]])?.compactMap { $0["name"] as? String }
            ?? (item["artists"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
        let album = (item["al"] as? [String: Any]) ?? (item["album"] as? [String: Any])
        return Song(id: sid, source: .wy,
                    name: item["name"] as? String ?? "",
                    singer: artists.joined(separator: "/"),
                    albumName: album?["name"] as? String,
                    picUrl: album?["picUrl"] as? String,
                    interval: Double(item["dt"] as? Int ?? item["duration"] as? Int ?? 0) / 1000,
                    qualitys: [.k128, .k320, .flac, .hires])
    }

    /// 批量取歌曲详情：/api/v3/song/detail?c=[{"id":…},…]
    static func wySongDetails(ids: [String]) async -> [Song] {
        guard !ids.isEmpty else { return [] }
        let json = "[" + ids.map { "{\"id\":\($0)}" }.joined(separator: ",") + "]"
        guard var comps = URLComponents(string: "https://music.163.com/api/v3/song/detail") else { return [] }
        comps.queryItems = [URLQueryItem(name: "c", value: json)]
        guard let url = comps.url else { return [] }
        var request = URLRequest(url: url, timeoutInterval: 20)
        request.setValue("https://music.163.com/", forHTTPHeaderField: "Referer")
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        guard let (data, _) = try? await URLSession.shared.data(for: request),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let list = dict["songs"] as? [[String: Any]] else { return [] }
        return list.compactMap { wySong(from: $0) }
    }

    static func fetch(platform: PlaylistImportPlatform, id: String) async throws -> ImportedPlaylist? {
        switch platform {
        case .wy:
            let url = URL(string: "https://music.163.com/api/v6/playlist/detail?id=\(id)&n=1000&s=0")!
            var request = URLRequest(url: url, timeoutInterval: 20)
            request.setValue("https://music.163.com/", forHTTPHeaderField: "Referer")
            request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
            guard let (data, _) = try? await URLSession.shared.data(for: request),
                  let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let playlist = dict["playlist"] as? [String: Any] else { return nil }

            let name = playlist["name"] as? String ?? "网易云歌单 \(id)"
            let cover = playlist["coverImgUrl"] as? String
            let partial = playlist["tracks"] as? [[String: Any]] ?? []
            let trackIds = (playlist["trackIds"] as? [[String: Any]])?.compactMap { $0["id"].map { "\($0)" } } ?? []

            var songs = partial.compactMap { Self.wySong(from: $0) }
            // v6 详情只给前 10 首；用 trackIds + 批量详情补齐全部
            if trackIds.count > songs.count {
                var details: [String: Song] = [:]
                for song in songs { details[song.id] = song }
                var missing = trackIds.filter { details[$0] == nil }
                var guardCount = 0
                while !missing.isEmpty && guardCount < 20 {
                    guardCount += 1
                    let chunk = Array(missing.prefix(100))
                    missing.removeFirst(min(100, missing.count))
                    for song in await Self.wySongDetails(ids: chunk) {
                        details[song.id] = song
                    }
                }
                let ordered = trackIds.compactMap { details[$0] }
                if ordered.count > songs.count { songs = ordered }
            }
            return ImportedPlaylist(name: name, cover: cover, songs: songs)

        case .tx:
            // 就是 Android 用的同一个接口：fcg_ucc_getcdinfo_byids_cp.fcg
            let raw = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?type=1&json=1&utf8=1&onlysong=0&disstid=\(id)&format=json&g_tk=5381"
            guard let url = URL(string: raw) else { return nil }
            var request = URLRequest(url: url, timeoutInterval: 20)
            request.setValue("https://y.qq.com/", forHTTPHeaderField: "Referer")
            request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
            guard let (data, _) = try? await URLSession.shared.data(for: request),
                  let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let cdlist = dict["cdlist"] as? [[String: Any]],
                  let cd = cdlist.first,
                  let list = cd["songlist"] as? [[String: Any]] else { return nil }
            let songs: [Song] = list.compactMap { item in
                let mid = item["songmid"] as? String ?? item["mid"] as? String ?? ""
                guard !mid.isEmpty else { return nil }
                let singers = (item["singer"] as? [[String: Any]])?.compactMap { $0["name"] as? String } ?? []
                let albumMid = item["albummid"] as? String
                return Song(id: mid, source: .tx,
                            name: item["songname"] as? String ?? item["name"] as? String ?? "",
                            singer: singers.joined(separator: "/"),
                            albumName: item["albumname"] as? String,
                            picUrl: albumMid.flatMap { "https://y.qq.com/music/photo_new/T002R300x300M000\($0).jpg" },
                            interval: Double(item["interval"] as? Int ?? 0),
                            qualitys: [.k128, .k320, .flac],
                            extra: ["mid": mid])
            }
            let name = cd["dissname"] as? String ?? "QQ 歌单 \(id)"
            let cover = cd["logo"] as? String
            return ImportedPlaylist(name: name, cover: cover, songs: songs)
        }
    }
}

