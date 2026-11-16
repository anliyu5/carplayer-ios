import SwiftUI

/// 播放页（按用户给的 3 张截图 1:1 还原：顶部「正在播放 · 单击切换封面 / 歌词」、大封面、居中歌词、圆点进度条、五键控制）
struct PlayerView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var player: PlayerEngine
    @EnvironmentObject private var router: Router

    @State private var dragging: Double?
    @State private var showQueue = false
    @State private var showQuality = false
    @State private var showLyric = false

    private var song: Song? { player.current }

    var body: some View {
        VStack(spacing: 0) {
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
        }
        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            Color.clear
                .frame(width: 72, height: 60)
                .contentShape(Rectangle())
                .onTapGesture { closePlayer() }
        }
        .gesture(
            DragGesture(minimumDistance: 30)
                .onEnded { value in
                    if value.translation.height > 80 || value.translation.width > 100 { closePlayer() }
                }
        )
        .sheet(isPresented: $showQueue) {
            QueueSheet()
                .presentationDetents([.medium, .large])
        }
        .sheet(isPresented: $showQuality) {
            QualityPickerSheet(title: "音质",
                               options: song?.qualitys ?? [.k320],
                               selected: store.settings.playQuality) { quality in
                store.settings.playQuality = quality
                store.persistAll()
                store.show("音质已设为 \(quality.display)")
            }
            .presentationDetents([.height(CGFloat(120 + (song?.qualitys.count ?? 1) * 50))])
        }
    }

    private func closePlayer() { router.screen = .main }

    // MARK: - 顶栏
    private var topBar: some View {
        ZStack {
            Text("正在播放 · 单击切换封面 / 歌词")
                .font(.system(size: 15))
                .foregroundColor(Palette.text.opacity(0.9))
            HStack {
                Button(action: closePlayer) {
                    VectorIcon(icon: .back, size: 22, color: Palette.text)
                        .frame(width: 56, height: 56)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.borderless)
                Spacer()
                Button {
                    if let song {
                        Downloader.shared.download(song: song, quality: store.settings.downloadQuality, store: store)
                    }
                } label: {
                    VectorIcon(icon: .download, size: 22, color: Palette.text)
                        .frame(width: 56, height: 56)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.borderless)
            }
        }
        .frame(height: 56)
        .padding(.horizontal, 6)
        .background(Palette.bg)
        .zIndex(2)
    }

    // MARK: - 封面 / 歌词
    private func coverOrLyric(_ song: Song, side: CGFloat) -> some View {
        Group {
            if showLyric {
                lyricPanel
            } else {
                cover(song, side: side)
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: side)
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) { showLyric.toggle() }
        }
        .padding(.top, 12)
    }

    private func cover(_ song: Song, side: CGFloat) -> some View {
        CoverBanner(url: song.picUrl, radius: 20)
            .frame(width: side, height: side)
            .shadow(color: .black.opacity(0.45), radius: 24, y: 10)
            .frame(maxWidth: .infinity)
    }

    private var lyricPanel: some View {
        Group {
            if let lyric = player.lyric, !lyric.lines.isEmpty {
                ScrollViewReader { proxy in
                    ScrollView(showsIndicators: false) {
                        LazyVStack(spacing: 18) {
                            ForEach(Array(lyric.lines.enumerated()), id: \.offset) { index, line in
                                Text(line.text.isEmpty ? "♪" : line.text)
                                    .font(.system(size: index == player.lyricIndex ? 19 : 17,
                                                  weight: index == player.lyricIndex ? .semibold : .regular))
                                    .foregroundColor(index == player.lyricIndex ? Palette.accent : Palette.textSub)
                                    .multilineTextAlignment(.center)
                                    .frame(maxWidth: .infinity)
                                    .id(index)
                            }
                        }
                        .padding(.vertical, 120)
                    }
                    .onAppear { proxy.scrollTo(max(player.lyricIndex, 0), anchor: .center) }
                    .onChange(of: player.lyricIndex) { index in
                        withAnimation(.easeInOut(duration: 0.3)) {
                            proxy.scrollTo(max(index, 0), anchor: .center)
                        }
                    }
                }
            } else if player.isResolving {
                VStack(spacing: 10) {
                    ProgressView().tint(Palette.accent)
                    Text("正在加载歌词…").font(FType.sub()).foregroundColor(Palette.textSub)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                VStack(spacing: 8) {
                    Text("暂无歌词").font(FType.chip()).foregroundColor(Palette.textSub)
                    Text("轻点回到封面").font(FType.subSm()).foregroundColor(Palette.textSub.opacity(0.7))
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private func titleBlock(_ song: Song) -> some View {
        VStack(spacing: 6) {
            Text(song.name)
                .font(.system(size: 23, weight: .bold))
                .foregroundColor(Palette.text)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            Text("\(song.displaySinger) · \(song.displayAlbum)")
                .font(.system(size: 14))
                .foregroundColor(Palette.textSub)
                .lineLimit(1)
        }
        .padding(.top, 0)
    }

    // MARK: - 进度条（圆点拖柄）
    private var progressBlock: some View {
        VStack(spacing: 8) {
            GeometryReader { geo in
                let total = max(player.duration, 0.001)
                let value = dragging ?? player.progress
                let ratio = min(max(value / total, 0), 1)
                let width = geo.size.width
                ZStack(alignment: .leading) {
                    Capsule().fill(Palette.trackBg).frame(height: 6)
                    Capsule().fill(Palette.accent).frame(width: max(ratio * width, 6), height: 6)
                    Circle()
                        .fill(Palette.accent)
                        .frame(width: 18, height: 18)
                        .overlay(Circle().fill(Color.white.opacity(0.65)).frame(width: 6, height: 6))
                        .offset(x: max(min(ratio * width - 9, width - 18), 0))
                }
                .frame(height: 18)
                .contentShape(Rectangle())
                .gesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { g in
                            dragging = min(max(g.location.x / width, 0), 1) * total
                        }
                        .onEnded { _ in
                            if let target = dragging { player.seek(target) }
                            dragging = nil
                        }
                )
            }
            .frame(height: 18)

            HStack {
                Text(Fmt.duration(dragging ?? player.progress))
                    .font(.system(size: 13))
                    .foregroundColor(Palette.textSub)
                Spacer()
                Text(Fmt.duration(player.duration))
                    .font(.system(size: 13))
                    .foregroundColor(Palette.textSub)
            }
        }
        .padding(.bottom, 26)
    }

    // MARK: - 控制区（模式 / 上一首 / 播放暂停 / 下一首 / 收藏）
    private func controls(_ song: Song) -> some View {
        HStack(spacing: 0) {
            Button { player.cycleMode() } label: {
                VectorIcon(icon: player.mode.icon, size: 22, color: Palette.textSub)
                    .frame(width: 48, height: 48)
            }
            .buttonStyle(.borderless)

            Spacer(minLength: 0)

            Button { player.prev() } label: {
                VectorIcon(icon: .prev, size: 26, color: Palette.text)
                    .frame(width: 56, height: 56)
            }
            .buttonStyle(.borderless)

            Button { player.toggle() } label: {
                ZStack {
                    Circle()
                        .fill(player.isPlaying ? Palette.accent : Palette.accent.opacity(0.85))
                    VectorIcon(icon: player.isPlaying ? .pause : .play,
                               size: 30,
                               color: Color(hex: 0x14161B))
                        .offset(x: player.isPlaying ? 0 : 2)
                }
                .frame(width: 78, height: 78)
                .shadow(color: Palette.accent.opacity(0.35), radius: 16, y: 6)
            }
            .buttonStyle(.borderless)
            .padding(.horizontal, 30)

            Button { player.next() } label: {
                VectorIcon(icon: .next, size: 26, color: Palette.text)
                    .frame(width: 56, height: 56)
            }
            .buttonStyle(.borderless)

            Spacer(minLength: 0)

            Button { store.toggleFavorite(song) } label: {
                VectorIcon(icon: .heart, size: 22,
                           color: store.isFavorite(song) ? Palette.accent : Palette.textSub)
                    .frame(width: 48, height: 48)
            }
            .buttonStyle(.borderless)
        }
        .padding(.horizontal, 4)
    }
}

/// 播放列表抽屉
struct QueueSheet: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var player: PlayerEngine
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("播放列表 · \(player.queue.count) 首")
                    .font(FType.sectionSm())
                    .foregroundColor(Palette.text)
                Spacer()
                Button("收起") { dismiss() }
                    .font(FType.chip())
                    .foregroundColor(Palette.textSub)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 14)

            ScrollView(showsIndicators: false) {
                LazyVStack(spacing: 0) {
                    ForEach(Array(player.queue.enumerated()), id: \.element.id) { index, song in
                        let isCurrent = player.current?.id == song.id
                        SongRowView(song: song, index: index + 1, showQuality: false) {
                            store.playAll(player.queue, startAt: index)
                        } onMore: {
                            store.show("已加入队列")
                        }
                        .background(isCurrent ? Palette.surface : Color.clear)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.bottom, 20)
            }
        }
        .background(Palette.sheet.ignoresSafeArea())
    }
}
