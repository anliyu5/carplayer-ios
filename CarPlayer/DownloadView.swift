import SwiftUI

/// 下载页：对齐 view_download（res/Mq.xml）
struct DownloadView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router
    @ObservedObject private var downloader = Downloader.shared
    @State private var showQuality = false
    @State private var isManaging = false

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 6) {
                Button {
                    router.screen = .main
                } label: {
                    VectorIcon(icon: .back, size: 24, color: Palette.text)
                        .frame(width: 64, height: 56)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.borderless)
                .accessibilityLabel("返回")
                Text("下载")
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
            }
            .frame(height: 64)
            .padding(.leading, 8)
            .padding(.trailing, 16)

            qualityRow
                .padding(.horizontal, 20)
                .padding(.top, 8)

            content

            if isManaging && !store.downloads.isEmpty {
                Button {
                    deleteAll()
                } label: {
                    Text("删除全部已下载（\(store.downloads.count) 首）")
                        .font(FType.chip())
                        .foregroundColor(Palette.danger)
                        .frame(maxWidth: .infinity)
                        .frame(height: 46)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.borderless)
                .padding(.horizontal, 20)
                .padding(.bottom, 12)
                .padding(.top, 6)
            }
        }
        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            Color.clear
                .frame(width: 76, height: 60)
                .contentShape(Rectangle())
                .onTapGesture { router.screen = .main }
        }
        .task { store.refreshLocalDownloads() }
        .sheet(isPresented: $showQuality) {
            QualityPickerSheet(title: "下载音质",
                               options: Quality.downloadOptions,
                               selected: store.settings.downloadQuality) { quality in
                store.settings.downloadQuality = quality
                store.persistAll()
            }
            .presentationDetents([.height(CGFloat(120 + Quality.downloadOptions.count * 50))])
        }
    }

    private func delete(_ song: Song) {
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
        store.show("已清空下载（\(all.count) 首）")
        isManaging = false
    }

    private var qualityRow: some View {
        HStack(spacing: 0) {
            VectorIcon(icon: .download, size: 22, color: Palette.textSub)
            Text("下载音质")
                .font(FType.rowTitle())
                .foregroundColor(Palette.text)
                .padding(.leading, 14)
            Spacer()
            Text(store.settings.downloadQuality.display)
                .font(FType.chip().bold())
                .foregroundColor(Palette.accent)
            VectorIcon(icon: .next, size: 22, color: Palette.textSub.opacity(0.6))
                .padding(.leading, 6)
        }
        .padding(.horizontal, 18)
        .frame(height: 58)
        .background(RoundedRectangle(cornerRadius: Radius.card, style: .continuous).fill(Palette.card))
        .contentShape(Rectangle())
        .onTapGesture { showQuality = true }
    }

    @ViewBuilder
    private var content: some View {
        if downloader.jobs.isEmpty && store.downloads.isEmpty {
            VStack(spacing: 0) {
                Spacer()
                VectorIcon(icon: .download, size: 46, color: Palette.text.sub(0.35))
                Text("还没有下载的歌曲")
                    .font(FType.rowTitle())
                    .foregroundColor(Palette.text)
                    .padding(.top, 14)
                Text("搜索到歌曲后点列表右侧「⋮」→「下载」，文件会存到 文件 → CarPlayer/Music，这里也能直接播放。")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .multilineTextAlignment(.center)
                    .lineSpacing(3)
                    .padding(.top, 8)
                Spacer()
            }
            .padding(.horizontal, 40)
        } else {
            ScrollView(showsIndicators: false) {
                LazyVStack(spacing: 0) {
                    if !downloader.jobs.isEmpty {
                        ForEach(downloader.jobs) { job in
                            HStack(spacing: 12) {
                                VectorIcon(icon: .note, size: 20, color: Palette.textSub)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("\(job.song.name)")
                                        .font(FType.chip())
                                        .foregroundColor(Palette.text)
                                        .lineLimit(1)
                                    ProgressView(value: job.progress)
                                        .tint(Palette.accent)
                                }
                                Text(job.state.rawValue)
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
                                }
                            }
                            .padding(.vertical, 8)
                        }
                    }
                    ForEach(Array(store.downloads.enumerated()), id: \.element.id) { index, song in
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
                }
                .padding(.horizontal, 20)
                .padding(.top, 4)
                .padding(.bottom, 16)
            }
        }
    }
}

extension Color {
    func `sub`(_ alpha: Double) -> Color { self.opacity(alpha) }
}
