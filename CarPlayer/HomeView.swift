import SwiftUI

/// 首页：对齐 view_home（res/EL.xml）
struct HomeView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                searchBar
                hotPlaylistSection
                hotHeader
                hotColumns
                Spacer(minLength: 8)
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 8)
        }
        .task { store.loadHotPlaylists() }
    }

    /// 热门歌单（网易云）：点一下开始播放并展开列表
    private var hotPlaylistSection: some View {
        VStack(spacing: 0) {
            HStack {
                Text("热门歌单")
                    .font(FType.section())
                    .foregroundColor(Palette.text)
                Spacer()
                Button {
                    store.loadHotPlaylists(force: true)
                } label: {
                    Text("换一批")
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                        .padding(.horizontal, 16)
                        .frame(height: 36)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.plain)
            }
            .padding(.top, 22)

            Text("网易云 + 小Q源 · 点封面展开歌单列表")
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 6)

            if store.hotPlaylists.isEmpty {
                Text(store.hotPlaylistError ?? (store.hotPlaylistLoading ? "加载中…" : ""))
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 20)
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 0) {
                        ForEach(store.hotPlaylists) { playlist in
                            PlaylistCardView(playlist: playlist) {
                                Task { @MainActor in
                                    if let full = await store.openHotPlaylist(playlist) {
                                        router.screen = .playlist(full.id)
                                    }
                                }
                            }
                        }
                    }
                    .padding(.top, 8)
                }
            }
        }
    }

    // 搜索条（56dp，bg_search 圆角胶囊 + 1dp 描边）
    private var searchBar: some View {
        HStack(spacing: 12) {
            VectorIcon(icon: .search, size: 20, color: Palette.textSub.opacity(0.6))
            Text("搜索歌曲、歌手")
                .font(FType.rowTitle())
                .foregroundColor(Palette.textSub)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 18)
        .frame(height: 56)
        .background(Capsule().fill(Palette.surface))
        .overlay(Capsule().stroke(Palette.stroke, lineWidth: 1))
        .contentShape(Rectangle())
        .onTapGesture { router.screen = .search }
    }

    // 热歌榜标题 + 换一批
    private var hotHeader: some View {
        HStack(spacing: 0) {
            Text("热歌榜")
                .font(FType.section())
                .foregroundColor(Palette.text)
                .frame(maxWidth: .infinity, alignment: .leading)
            Button {
                store.shuffleHot()
            } label: {
                Text("换一批")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .padding(.horizontal, 16)
                    .frame(height: 36)
                    .background(Capsule().fill(Palette.surface2))
            }
            .buttonStyle(.plain)
        }
        .padding(.top, 20)
    }

    // 两列：小Q热歌 / 小云热歌
    private var hotColumns: some View {
        HStack(alignment: .top, spacing: 0) {
            column(title: "小Q热歌", songs: store.hotTx, empty: store.hotTxError, source: .tx)
            Rectangle()
                .fill(Color.white.opacity(0.13))
                .frame(width: 1)
                .padding(.horizontal, 12)
            column(title: "小云热歌", songs: store.hotWy, empty: store.hotWyError, source: .wy)
        }
        .padding(.top, 10)
    }

    private func column(title: String, songs: [Song], empty: String?, source: SourceId) -> some View {
        VStack(spacing: 0) {
            Text(title)
                .font(FType.hotTitle())
                .foregroundColor(Palette.accent)
                .frame(maxWidth: .infinity, alignment: .leading)
            if songs.isEmpty {
                Text(empty ?? (store.hotLoading ? "加载中…" : "加载失败"))
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 30)
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(songs.prefix(10).enumerated()), id: \.offset) { index, song in
                        HotColumnRowView(index: index + 1, song: song) {
                            store.playAll(songs, startAt: index)
                            router.screen = .player
                        }
                        .padding(.top, index == 0 ? 6 : 0)
                    }
                }
            }
        }
        .frame(maxWidth: .infinity)
    }
}
