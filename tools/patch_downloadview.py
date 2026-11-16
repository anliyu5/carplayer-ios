import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
p = os.path.join(root, "CarPlayer", "DownloadView.swift")
t = io.open(p, encoding="utf-8").read()

# 1) 返回键加固
old_back = """            HStack(spacing: 6) {
                Button {
                    router.screen = .main
                } label: {
                    VectorIcon(icon: .back, size: 24, color: Palette.text)
                        .frame(width: 52, height: 52)
                }
                .buttonStyle(.plain)"""
new_back = """            HStack(spacing: 6) {
                Button {
                    router.screen = .main
                } label: {
                    VectorIcon(icon: .back, size: 24, color: Palette.text)
                        .frame(width: 64, height: 56)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.borderless)
                .accessibilityLabel("返回")"""
assert old_back in t, "back anchor"
t = t.replace(old_back, new_back)

# 2) 顶层兜底返回区 + 自动刷新本地列表
old_bg = """        .background(Palette.bg.ignoresSafeArea())
        .sheet(item: $menuSong) { song in"""
if old_bg not in t:
    old_bg = """        .background(Palette.bg.ignoresSafeArea())
        .confirmationDialog"""
t = t.replace("""        .background(Palette.bg.ignoresSafeArea())
""", """        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            Color.clear
                .frame(width: 76, height: 60)
                .contentShape(Rectangle())
                .onTapGesture { router.screen = .main }
        }
        .task { store.refreshLocalDownloads() }
""", 1)

# 3) 已下载列表：每行加删除按钮
old_rows = """                    ForEach(Array(store.downloads.enumerated()), id: \\.element.id) { index, song in
                        SongRowView(song: song, index: index + 1, showQuality: false) {
                            store.playAll(store.downloads, startAt: index)
                            router.screen = .player
                        } onMore: {
                            store.show("本地音乐不可删除")
                        }
                    }"""
new_rows = """                    ForEach(Array(store.downloads.enumerated()), id: \\.element.id) { index, song in
                        HStack(spacing: 0) {
                            SongRowView(song: song, index: index + 1, showQuality: false) {
                                store.playAll(store.downloads, startAt: index)
                                router.screen = .player
                            } onMore: {
                                delete(song)
                            }
                            Button {
                                delete(song)
                            } label: {
                                VectorIcon(icon: .delete, size: 20, color: Palette.danger)
                                    .frame(width: 44, height: 44)
                                    .contentShape(Rectangle())
                            }
                            .buttonStyle(.borderless)
                            .accessibilityLabel("删除本地文件")
                        }
                    }"""
assert old_rows in t, "rows anchor"
t = t.replace(old_rows, new_rows)

# 4) 删除方法
t = t.replace("""    private var qualityRow: some View {""",
"""    private func delete(_ song: Song) {
        Downloader.shared.deleteLocalFile(song)
        store.deleteDownload(song)
    }

    private var qualityRow: some View {""")

# 5) 进行中的任务也能移除
t = t.replace("""                                Text(job.state.rawValue)
                                    .font(FType.tiny())
                                    .foregroundColor(job.state == .failed ? Palette.danger : Palette.textSub)""",
"""                                Text(job.state.rawValue)
                                    .font(FType.tiny())
                                    .foregroundColor(job.state == .failed ? Palette.danger : Palette.textSub)
                                if job.state == .failed {
                                    Button {
                                        downloader.remove(job)
                                    } label: {
                                        VectorIcon(icon: .close, size: 16, color: Palette.textSub)
                                            .frame(width: 36, height: 36)
                                    }
                                    .buttonStyle(.borderless)
                                }""")
io.open(p, "w", encoding="utf-8").write(t)
print("DownloadView: back + delete + refresh")
