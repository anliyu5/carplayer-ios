import SwiftUI

/// 歌单详情：对齐 activity_playlist（res/vc.xml）
struct PlaylistView: View {
    let playlistId: String
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router
    @State private var filter: String = ""
    @State private var filterVisible = false
    @State private var menuSong: Song?

    private var playlist: Playlist? {
        store.playlists.first(where: { $0.id == playlistId })
    }

    private var songs: [Song] {
        guard let playlist else { return [] }
        guard !filter.isEmpty else { return playlist.songs }
        return playlist.songs.filter {
            $0.name.localizedCaseInsensitiveContains(filter) || $0.displaySinger.localizedCaseInsensitiveContains(filter)
        }
    }

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
                Text(playlist?.name ?? "歌单")
                    .font(FType.h2())
                    .foregroundColor(Palette.text)
                    .lineLimit(1)
                Spacer(minLength: 0)
                if let playlist, !playlist.isFavorite {
                    Button {
                        store.deletePlaylist(playlist)
                        router.screen = .main
                    } label: {
                        VectorIcon(icon: .delete, size: 20, color: Palette.danger)
                            .frame(width: 56, height: 56)
                            .contentShape(Rectangle())
                    }
                    .buttonStyle(.borderless)
                    .accessibilityLabel("删除歌单")
                }
            }
            .frame(height: 64)
            .padding(.leading, 8)
            .padding(.trailing, 12)
            infoRow
            if filterVisible {
                filterField
            }
            list
        }
        .background(Palette.bg.ignoresSafeArea())
        .sheet(item: $menuSong) { song in
            SongActionSheet(song: song, playlistId: playlistId)
                .presentationDetents([.height(400)])
        }
    }

    private var infoRow: some View {
        HStack(alignment: .center, spacing: 16) {
            CoverImage(url: playlist?.picUrl, size: 96, radius: Radius.cover)
            VStack(alignment: .leading, spacing: 0) {
                Text(subtitle)
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                HStack(spacing: 10) {
                    Button {
                        store.playAll(songs)
                        router.screen = .player
                    } label: {
                        Text("播放全部")
                            .font(FType.body())
                            .foregroundColor(Palette.accent)
                            .padding(.horizontal, 20)
                            .frame(height: 44)
                            .background(Capsule().fill(Palette.accentFill))
                            .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
                    }
                    .buttonStyle(.plain)

                    Button {
                        Downloader.shared.downloadAll(songs, quality: store.settings.downloadQuality, store: store)
                    } label: {
                        Text("全部下载")
                            .font(FType.body())
                            .foregroundColor(Palette.text)
                            .padding(.horizontal, 18)
                            .frame(height: 44)
                            .background(Capsule().fill(Palette.surface2))
                    }
                    .buttonStyle(.plain)
                }
                .padding(.top, 12)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 24)
        .padding(.bottom, 8)
    }

    private var subtitle: String {
        guard let playlist else { return "" }
        let owner = playlist.isFavorite ? "我的收藏" : (playlist.isRemote ? "\(playlist.source.display)歌单" : "我的歌单")
        return "\(owner) · \(playlist.count) 首"
    }

    private var filterField: some View {
        TextField("", text: $filter, prompt: Text("搜索本地音乐").foregroundColor(Palette.textSub))
            .font(FType.body())
            .foregroundColor(Palette.text)
            .padding(.horizontal, 16)
            .frame(height: 42)
            .background(Capsule().fill(Palette.surface))
            .overlay(Capsule().stroke(Palette.stroke, lineWidth: 1))
            .padding(.horizontal, 20)
            .padding(.top, 8)
    }

    @ViewBuilder
    private var list: some View {
        if songs.isEmpty {
            VStack {
                Spacer()
                Text(playlist?.songs.isEmpty == true ? "歌单是空的" : "没有找到本地音乐")
                    .font(FType.chip())
                    .foregroundColor(Palette.textSub)
                Spacer()
            }
        } else {
            ScrollView(showsIndicators: false) {
                LazyVStack(spacing: 0) {
                    ForEach(Array(songs.enumerated()), id: \.element.id) { index, song in
                        SongRowView(song: song, index: index + 1) {
                            store.playAll(songs, startAt: index)
                            router.screen = .player
                        } onMore: {
                            menuSong = song
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

/// 播放历史：对齐 activity_history（res/XY.xml）
struct HistoryView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router
    @State private var menuSong: Song?

    private struct Group: Identifiable {
        let id: String
        let entries: [HistoryEntry]
    }

    private var groups: [Group] {
        var order: [String] = []
        var map: [String: [HistoryEntry]] = [:]
        for entry in store.history {
            let key = Fmt.dayGroup(entry.time)
            if map[key] == nil { order.append(key) }
            map[key, default: []].append(entry)
        }
        return order.map { Group(id: $0, entries: map[$0] ?? []) }
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 6) {
                Button {
                    router.screen = .main
                } label: {
                    VectorIcon(icon: .back, size: 24, color: Palette.text)
                        .frame(width: 52, height: 52)
                }
                .buttonStyle(.plain)
                Text("播放历史")
                    .font(FType.h2())
                    .foregroundColor(Palette.text)
                Spacer(minLength: 0)
                Button {
                    store.clearHistory()
                } label: {
                    Text("清空")
                        .font(FType.chip())
                        .foregroundColor(Palette.textSub)
                        .padding(.horizontal, 16)
                        .frame(height: 36)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.plain)
            }
            .frame(height: 64)
            .padding(.leading, 8)
            .padding(.trailing, 16)

            HStack {
                Text("最多保留最近 100 首")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                Spacer()
                Button {
                    store.playAll(store.history.map { $0.song })
                    router.screen = .player
                } label: {
                    Text("播放全部")
                        .font(FType.chip())
                        .foregroundColor(Palette.accent)
                        .padding(.horizontal, 18)
                        .frame(height: 40)
                        .background(Capsule().fill(Palette.accentFill))
                        .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 6)

            if store.history.isEmpty {
                VStack {
                    Spacer()
                    Text("还没有播放记录\n听过一首歌之后就会出现在这里")
                        .font(FType.chip())
                        .foregroundColor(Palette.textSub)
                        .multilineTextAlignment(.center)
                        .lineSpacing(6)
                    Spacer()
                }
            } else {
                ScrollView(showsIndicators: false) {
                    LazyVStack(spacing: 0, pinnedViews: []) {
                        ForEach(groups) { group in
                            Text(group.id)
                                .font(FType.sub().bold())
                                .foregroundColor(Palette.accent)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 8)
                                .padding(.top, 14)
                                .padding(.bottom, 6)
                            ForEach(group.entries) { entry in
                                HistoryRowView(entry: entry) {
                                    let queue = store.history.map { $0.song }
                                    if let index = queue.firstIndex(where: { $0.id == entry.song.id }) {
                                        store.playAll(queue, startAt: index)
                                    }
                                    router.screen = .player
                                } onMore: {
                                    menuSong = entry.song
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.bottom, 16)
                }
            }
        }
        .background(Palette.bg.ignoresSafeArea())
        .sheet(item: $menuSong) { song in
            SongActionSheet(song: song)
                .presentationDetents([.height(360)])
        }
    }
}
