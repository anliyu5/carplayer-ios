import SwiftUI

/// 歌曲「⋮」菜单：条目与 Android 侧一致（下一首播放 / 加入歌单 / 收藏 / 下载）
struct SongActionSheet: View {
    let song: Song
    var playlistId: String?          // 在歌单内时显示「从歌单移除」

    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var player: PlayerEngine
    @Environment(\.dismiss) private var dismiss
    @State private var showPlaylistPicker = false

    var body: some View {
        VStack(spacing: 0) {
            Capsule()
                .fill(Palette.divider)
                .frame(width: 36, height: 4)
                .padding(.top, 10)
                .padding(.bottom, 14)

            HStack(spacing: 12) {
                CoverImage(url: song.picUrl, size: 44, radius: Radius.cover)
                VStack(alignment: .leading, spacing: 3) {
                    Text(song.name)
                        .font(FType.rowTitle())
                        .foregroundColor(Palette.text)
                        .lineLimit(1)
                    Text(song.displaySinger)
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                        .lineLimit(1)
                }
                Spacer(minLength: 0)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 10)

            action("下一首播放", icon: .next) {
                var queue = player.queue
                if let at = queue.firstIndex(where: { $0.id == player.current?.id }) {
                    queue.insert(song, at: min(at + 1, queue.count))
                } else {
                    queue.append(song)
                }
                if let current = player.current {
                    player.play(song: current, queue: queue)
                }
                store.show("已加入队列")
            }
            action("加入歌单", icon: .plus, dismissAfter: false) { showPlaylistPicker = true }
            action(store.isFavorite(song) ? "取消收藏" : "收藏", icon: .heart) {
                store.toggleFavorite(song)
            }
            action("下载", icon: .download) {
                Downloader.shared.download(song: song, quality: store.settings.downloadQuality, store: store)
                store.show("开始下载 \(song.name)")
            }
            if let playlistId {
                action("从歌单移除", icon: .delete) {
                    store.removeFromPlaylist(song, playlistId: playlistId)
                }
            }
            if song.isLocal {
                action("删除本地文件", icon: .delete) {
                    Downloader.shared.deleteLocalFile(song)
                    store.deleteDownload(song)
                }
            }
            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Palette.sheet.ignoresSafeArea())
        .sheet(isPresented: $showPlaylistPicker) {
            PlaylistPickerSheet(song: song)
                .presentationDetents([.medium])
        }
    }

    private func action(_ title: String, icon: Icon, dismissAfter: Bool = true, perform: @escaping () -> Void) -> some View {
        Button {
            perform()
            if dismissAfter { dismiss() }
        } label: {
            HStack(spacing: 14) {
                VectorIcon(icon: icon, size: 20, color: Palette.textSub)
                Text(title)
                    .font(FType.rowTitle())
                    .foregroundColor(Palette.text)
                Spacer(minLength: 0)
            }
            .padding(.horizontal, 20)
            .frame(height: 52)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

/// 加入哪个歌单？
struct PlaylistPickerSheet: View {
    let song: Song
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var player: PlayerEngine
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("加入哪个歌单？")
                    .font(FType.sectionSm())
                    .foregroundColor(Palette.text)
                Spacer()
                Button("取消") { dismiss() }
                    .font(FType.chip())
                    .foregroundColor(Palette.textSub)
            }
            .padding(.horizontal, 20)
            .padding(.top, 18)
            .padding(.bottom, 10)

            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    ForEach(store.playlists.filter { !$0.isRemote }) { playlist in
                        Button {
                            _ = store.addToPlaylist(song, playlistId: playlist.id)
                            dismiss()
                        } label: {
                            HStack(spacing: 12) {
                                CoverImage(url: playlist.picUrl, size: 40, radius: Radius.cover)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(playlist.name)
                                        .font(FType.rowTitle())
                                        .foregroundColor(Palette.text)
                                        .lineLimit(1)
                                    Text("\(playlist.count) 首")
                                        .font(FType.subSm())
                                        .foregroundColor(Palette.textSub)
                                }
                                Spacer(minLength: 0)
                            }
                            .padding(.horizontal, 20)
                            .frame(height: 60)
                            .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            Spacer(minLength: 0)
        }
        .background(Palette.sheet.ignoresSafeArea())
    }
}
