import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ C) 下载页：管理模式（全选删除 / 单条删除） ============
p = os.path.join(root, "CarPlayer", "DownloadView.swift")
t = io.open(p, encoding="utf-8").read()

# 状态
t = t.replace("    @State private var showQuality = false",
              "    @State private var showQuality = false\n    @State private var isManaging = false")

# 头部右侧「管理 / 完成」
old_title = """                Text("下载")
                    .font(FType.h2())
                    .foregroundColor(Palette.text)
                Spacer(minLength: 0)
            }"""
new_title = """                Text("下载")
                    .font(FType.h2())
                    .foregroundColor(Palette.text)
                Spacer(minLength: 0)
                if !store.downloads.isEmpty {
                    Button {
                        isManaging.toggle()
                    } label: {
                        Text(isManaging ? "完成" : "管理")
                            .font(FType.chip())
                            .foregroundColor(Palette.accent)
                            .padding(.horizontal, 16)
                            .frame(height: 32)
                            .background(Capsule().fill(Palette.accentFill))
                            .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
                    }
                    .buttonStyle(.borderless)
                }
            }"""
assert old_title in t, "title anchor"
t = t.replace(old_title, new_title)

# 行：管理模式下点行=删除；右侧保留垃圾桶
old_rows = t[t.index("                    ForEach(Array(store.downloads.enumerated()), id: \\.element.id) { index, song in"):]
old_rows = old_rows[:old_rows.index("\n                    }\n") + len("\n                    }\n")]
new_rows = """                    ForEach(Array(store.downloads.enumerated()), id: \\.element.id) { index, song in
                        HStack(spacing: 0) {
                            SongRowView(song: song, index: index + 1, showQuality: false) {
                                if isManaging {
                                    delete(song)
                                } else {
                                    store.playAll(store.downloads, startAt: index)
                                    router.screen = .player
                                }
                            } onMore: {
                                delete(song)
                            }
                            if isManaging {
                                Button {
                                    delete(song)
                                } label: {
                                    Text("删除")
                                        .font(FType.chip())
                                        .foregroundColor(Palette.danger)
                                        .padding(.horizontal, 14)
                                        .frame(height: 34)
                                        .background(Capsule().fill(Palette.surface2))
                                }
                                .buttonStyle(.borderless)
                                .padding(.trailing, 8)
                            }
                        }
                        .contentShape(Rectangle())
                        .contextMenu {
                            Button(role: .destructive) { delete(song) } label: { Text("删除本地文件") }
                            Button { store.playAll(store.downloads, startAt: index); router.screen = .player } label: { Text("立即播放") }
                        }
                    }
"""
t = t.replace(old_rows, new_rows)

# 管理模式下底部加「全部删除」
old_q = t.replace("    private var qualityRow: some View {", "    private var qualityRow: some View {")
t = t.replace("""    private func delete(_ song: Song) {
        Downloader.shared.deleteLocalFile(song)
        store.deleteDownload(song)
    }""",
"""    private func delete(_ song: Song) {
        Downloader.shared.deleteLocalFile(song)
        store.deleteDownload(song)
    }

    private func deleteAll() {
        let all = store.downloads
        for song in all {
            Downloader.shared.deleteLocalFile(song)
        }
        store.downloads = []
        store.persistAll()
        store.show("已清空下载（\\(all.count) 首）")
        isManaging = false
    }""")
io.open(p, "w", encoding="utf-8").write(t)
print("DownloadView: manage mode")

# ============ D) 歌曲菜单：本地音乐可删除文件 ============
sa = os.path.join(root, "CarPlayer", "SongActions.swift")
s = io.open(sa, encoding="utf-8").read()
old_tail = """            if let playlistId {
                action("从歌单移除", icon: .delete) {
                    store.removeFromPlaylist(song, playlistId: playlistId)
                }
            }"""
new_tail = """            if let playlistId {
                action("从歌单移除", icon: .delete) {
                    store.removeFromPlaylist(song, playlistId: playlistId)
                }
            }
            if song.isLocal {
                action("删除本地文件", icon: .delete) {
                    Downloader.shared.deleteLocalFile(song)
                    store.deleteDownload(song)
                }
            }"""
assert old_tail in s, "song actions anchor"
s = s.replace(old_tail, new_tail)
io.open(sa, "w", encoding="utf-8").write(s)
print("SongActions: delete local file")

# ============ E) 设置页「下载管理」：列出已下载并能删 ============
st = os.path.join(root, "CarPlayer", "SettingsView.swift")
v = io.open(st, encoding="utf-8").read()
old_list = """            if downloader.jobs.isEmpty {
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
                }
                .padding(.top, 8)
            }"""
new_list = """            if store.downloads.isEmpty && downloader.jobs.isEmpty {
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
            }"""
assert old_list in v, "settings download list anchor"
v = v.replace(old_list, new_list)
io.open(st, "w", encoding="utf-8").write(v)
print("SettingsView: download management list")
