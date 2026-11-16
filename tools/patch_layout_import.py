import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ 1) 播放页：去掉底部黑边，内容按可用高度分布 ============
p = os.path.join(root, "CarPlayer", "PlayerView.swift")
t = io.open(p, encoding="utf-8").read()

old_body = """        VStack(spacing: 0) {
            topBar
            if let song {
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 0) {
                        coverOrLyric(song)
                        titleBlock(song)
                        progressBlock
                        controls(song)
                    }
                    .padding(.horizontal, 24)
                    .padding(.bottom, 24)
                }
            } else {
                VStack {
                    Spacer()
                    Text("当前没有正在播放的歌曲")
                        .font(FType.rowTitle())
                        .foregroundColor(Palette.textSub)
                    Spacer()
                }
            }
        }"""
new_body = """        VStack(spacing: 0) {
            topBar
            if let song {
                GeometryReader { geo in
                    let coverSide = min(geo.size.width - 48, geo.size.height * 0.40, 340)
                    VStack(spacing: 0) {
                        Spacer(minLength: 6)
                        coverOrLyric(song, side: coverSide)
                        Spacer(minLength: 14)
                        titleBlock(song)
                        Spacer(minLength: 12)
                        progressBlock
                        Spacer(minLength: 10)
                        controls(song)
                        Spacer(minLength: 8)
                    }
                    .padding(.horizontal, 24)
                    .frame(width: geo.size.width, height: geo.size.height)
                }
            } else {
                VStack {
                    Spacer()
                    Text("当前没有正在播放的歌曲")
                        .font(FType.rowTitle())
                        .foregroundColor(Palette.textSub)
                    Spacer()
                }
            }
        }"""
assert old_body in t, "player body anchor missing"
t = t.replace(old_body, new_body)

# coverOrLyric 接收尺寸
t = t.replace("""    private func coverOrLyric(_ song: Song) -> some View {""",
              """    private func coverOrLyric(_ song: Song, side: CGFloat) -> some View {""")
t = t.replace("""            if showLyric {
                lyricPanel
            } else {
                cover(song)
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: 320)""",
"""            if showLyric {
                lyricPanel
            } else {
                cover(song, side: side)
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: side)""")

t = t.replace("""    private func cover(_ song: Song) -> some View {
        ZStack {
            CoverBanner(url: song.picUrl, radius: 20)
                .frame(width: 300, height: 300)
                .shadow(color: .black.opacity(0.45), radius: 24, y: 10)
        }
        .frame(maxWidth: .infinity)
    }""",
"""    private func cover(_ song: Song, side: CGFloat) -> some View {
        CoverBanner(url: song.picUrl, radius: 20)
            .frame(width: side, height: side)
            .shadow(color: .black.opacity(0.45), radius: 24, y: 10)
            .frame(maxWidth: .infinity)
    }""")

# 歌词面板内边距按高度自适应
t = t.replace(".padding(.vertical, 140)", ".padding(.vertical, 120)")

# 标题块/进度/控制的外边距收紧，进一步吃掉底部空白
t = t.replace("""        .padding(.top, 26)
        .padding(.bottom, 26)""", """        .padding(.top, 0)""")
io.open(p, "w", encoding="utf-8").write(t)
print("PlayerView: layout fills height")

# ============ 2) 导入音源：按钮固定底部 + 永远有反馈 ============
s = os.path.join(root, "CarPlayer", "SettingsView.swift")
v = io.open(s, encoding="utf-8").read()

# 2.1 sheet 改成 large，内容可滚动，按钮不压在键盘下
v = v.replace(".sheet(isPresented: $showScriptSheet) { scriptImportSheet.presentationDetents([.height(420)]) }",
              ".sheet(isPresented: $showScriptSheet) { scriptImportSheet.presentationDetents([.large]) }")

# 2.2 重写 scriptImportSheet：ScrollView + safeAreaInset 底部按钮
start = v.index("    private var scriptImportSheet: some View {")
end = v.index("    private var playlistImportSheet: some View {")
new_sheet = '''    private var scriptImportSheet: some View {
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
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
            .padding(.top, 8)
            .background(Palette.sheet)
        }
    }

'''
v = v[:start] + new_sheet + v[end:]

# 2.3 importScript：立即反馈 + 明确失败原因
old_import = v[v.index("    private func importScript() {"):]
old_import = old_import[:old_import.index("\n    }\n") + len("\n    }\n")]
new_import = '''    private func importScript() {
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
                showScriptSheet = false
                return
            }
            // 2) 文本：含 lines → 青听配置；否则按 .js 脚本
            if text.contains("\\"lines\\"") || text.contains("/**") || text.contains("lines\\":") {
                let message = await store.importQing(json: text)
                store.show(message)
            } else {
                let message = await store.importScript(text: text)
                store.show(message)
            }
            showScriptSheet = false
        }
    }
'''
v = v.replace(old_import, new_import)
io.open(s, "w", encoding="utf-8").write(v)
print("SettingsView: import sheet fixed")

# ============ 3) AppStore.importQing 支持 sourceURL，便于推导网关 ============
a = os.path.join(root, "CarPlayer", "AppStore.swift")
w = io.open(a, encoding="utf-8").read()
w = w.replace("    func importQing(json: String) async -> String {",
              "    func importQing(json: String, sourceURL: String? = nil) async -> String {")
w = w.replace("            config = QingConfig.parse(json: text)",
              "            config = QingConfig.parse(json: text, sourceURL: sourceURL)")
io.open(a, "w", encoding="utf-8").write(w)
print("AppStore: importQing(sourceURL:)")
