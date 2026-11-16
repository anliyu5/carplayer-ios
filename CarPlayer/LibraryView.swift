import SwiftUI

/// 曲库 / 歌单页：对齐 view_library（res/o7.xml）
struct LibraryView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                historyEntry
                remoteSection
                playlistList
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
        }
        .task {
            if store.downloads.isEmpty {
                store.downloads = Downloader.shared.scanLocalSongs()
            }
        }
    }

    // 播放历史入口卡片
    private var historyEntry: some View {
        HStack(spacing: 12) {
            VectorIcon(icon: .history, size: 26, color: Palette.accent)
                .frame(width: 30, height: 30)
            VStack(alignment: .leading, spacing: 3) {
                Text("播放历史")
                    .font(FType.rowTitle().bold())
                    .foregroundColor(Palette.text)
                Text(store.history.isEmpty ? "还没有播放记录" : "共 \(store.history.count) 首 · 长按可清空")
                    .font(FType.subSm())
                    .foregroundColor(Palette.textSub)
            }
            Spacer(minLength: 0)
            VectorIcon(icon: .chevron, size: 18, color: Palette.textSub)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .surfaceCard()
        .padding(.top, 2)
        .contentShape(Rectangle())
        .onTapGesture { router.screen = .history }
    }

    // 远程导入歌单（item_playlist_card 横滑）
    @ViewBuilder
    private var remoteSection: some View {
        let remote = store.playlists.filter { $0.isRemote }
        if !remote.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                SectionTitle(text: "导入的歌单", font: FType.sectionSm())
                    .padding(.top, 18)
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 0) {
                        ForEach(remote) { playlist in
                            ZStack(alignment: .topTrailing) {
                                PlaylistCardView(playlist: playlist) {
                                    router.screen = .playlist(playlist.id)
                                }
                                Button {
                                    store.deletePlaylist(playlist)
                                } label: {
                                    VectorIcon(icon: .close, size: 13, color: Palette.text)
                                        .frame(width: 26, height: 26)
                                        .background(Circle().fill(Color.black.opacity(0.55)))
                                }
                                .buttonStyle(.borderless)
                                .padding(.top, 6)
                                .padding(.trailing, 20)
                                .accessibilityLabel("删除歌单")
                            }
                        }
                    }
                }
            }
        }
    }

    // 本地歌单列表（item_playlist_row）
    private var playlistList: some View {
        VStack(spacing: 0) {
            HStack {
                SectionTitle(text: "我的歌单", font: FType.sectionSm())
                Button {
                    createPlaylist()
                } label: {
                    VectorIcon(icon: .plus, size: 20, color: Palette.textSub)
                        .frame(width: 36, height: 36)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("新增")
            }
            .padding(.top, 18)

            ForEach(store.playlists.filter { !$0.isRemote }) { playlist in
                PlaylistRowView(playlist: playlist) {
                    router.screen = .playlist(playlist.id)
                } onMore: {
                    moreMenu(playlist)
                }
            }

            if store.downloads.isEmpty {
                Text("还没有歌单，先去歌单页导入一个")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 20)
            }
        }
    }

    private func createPlaylist() {
        let playlist = store.createPlaylist(name: "新建歌单 \(store.playlists.count)")
        router.screen = .playlist(playlist.id)
    }

    private func moreMenu(_ playlist: Playlist) {
        guard !playlist.isFavorite else {
            store.show("收藏歌单不可删除")
            return
        }
        store.deletePlaylist(playlist)
        store.show("已删除「\(playlist.name)」")
    }
}
