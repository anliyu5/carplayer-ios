import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ---------- E) SearchView：chips 生效 ----------
p = os.path.join(root, "CarPlayer", "SearchView.swift")
t = io.open(p, encoding="utf-8").read()
start = t.index("    // searchSources：音源筛选 chips")
end = t.index("    private var historyBox: some View {")
new = '''    // searchSources：音源筛选 chips（点一下立刻重搜）
    private var sourceChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(store.availableSources) { source in
                    let on = store.isSourceEnabled(source)
                    Button {
                        store.toggleSearchSource(source)
                    } label: {
                        Text(sourceTitle(source))
                            .font(FType.chip())
                            .foregroundColor(on ? Palette.accent : Palette.textSub)
                            .padding(.horizontal, 14)
                            .frame(height: 32)
                            .background(Capsule().fill(on ? Palette.accentFill : Palette.surface2))
                            .overlay(Capsule().stroke(on ? Palette.accentStroke : Color.clear, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(.top, 12)
    }

    /// 有青听配置时用线路名（小窝源/小Q源…），否则用平台名
    private func sourceTitle(_ source: SourceId) -> String {
        store.qing?.lines.first(where: { $0.sourceId == source })?.name ?? source.display
    }

'''
t = t[:start] + new + t[end:]
io.open(p, "w", encoding="utf-8").write(t)
print("SearchView chips fixed")

# ---------- F) PlayerView：去掉音量条 + 封面点击切歌词 ----------
v = os.path.join(root, "CarPlayer", "PlayerView.swift")
s = io.open(v, encoding="utf-8").read()

s = s.replace("    @State private var showQuality = false",
              "    @State private var showQuality = false\n    @State private var showLyric = false")

# 去掉音量滑块整行
s = s.replace('''            HStack(spacing: 10) {
                VectorIcon(icon: .note, size: 16, color: Palette.textSub.opacity(0.7))
                Slider(value: Binding(get: { player.volume }, set: { player.setVolume($0) }), in: 0...1)
                    .tint(Palette.accent)
            }

''', "")

# 封面/歌词二选一
s = s.replace('''                        cover(song)
                        titleBlock(song)
                        lyricBlock
                        progressBlock''',
'''                        coverOrLyric(song)
                        titleBlock(song)
                        progressBlock''')

# 新增 coverOrLyric 与 lyricPanel
old_cover_start = s.index("    private func cover(_ song: Song) -> some View {")
s = s[:old_cover_start] + '''    /// 单击封面 / 歌词区切换
    private func coverOrLyric(_ song: Song) -> some View {
        Group {
            if showLyric {
                lyricPanel
            } else {
                cover(song)
            }
        }
        .frame(height: 220)
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) { showLyric.toggle() }
        }
        .padding(.top, 4)
    }

    private var lyricPanel: some View {
        VStack(alignment: .leading, spacing: 0) {
            if let lyric = player.lyric, !lyric.lines.isEmpty {
                ScrollViewReader { proxy in
                    ScrollView(showsIndicators: false) {
                        LazyVStack(alignment: .leading, spacing: 10) {
                            ForEach(Array(lyric.lines.enumerated()), id: \\.offset) { index, line in
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(line.text.isEmpty ? "♪" : line.text)
                                        .font(.system(size: index == player.lyricIndex ? 17 : 14,
                                                      weight: index == player.lyricIndex ? .semibold : .regular))
                                        .foregroundColor(index == player.lyricIndex ? Palette.accent : Palette.textSub.opacity(0.8))
                                    if let trans = line.trans, !trans.isEmpty {
                                        Text(trans)
                                            .font(.system(size: 12))
                                            .foregroundColor(Palette.textSub.opacity(0.6))
                                    }
                                }
                                .id(index)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.vertical, 8)
                    }
                    .onChange(of: player.lyricIndex) { index in
                        withAnimation(.easeInOut(duration: 0.25)) {
                            proxy.scrollTo(max(index, 0), anchor: .center)
                        }
                    }
                }
            } else if player.isResolving {
                VStack(spacing: 8) {
                    ProgressView().tint(Palette.accent)
                    Text("正在加载歌词…").font(FType.sub()).foregroundColor(Palette.textSub)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                VStack(spacing: 6) {
                    Text("暂无歌词").font(FType.chip()).foregroundColor(Palette.textSub)
                    Text("轻点回到封面").font(FType.subSm()).foregroundColor(Palette.textSub.opacity(0.7))
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, 4)
        .background(RoundedRectangle(cornerRadius: Radius.cover, style: .continuous).fill(Palette.surface))
    }

    private func cover(_ song: Song) -> some View {''' + s[old_cover_start + len("    private func cover(_ song: Song) -> some View {"):]

# 封面下方提示
s = s.replace('''        .frame(maxWidth: .infinity)
        .padding(.top, 4)
    }''', '''        .frame(maxWidth: .infinity)
        .overlay(alignment: .bottomTrailing) {
            Text(showLyric ? "歌词" : "轻点看歌词")
                .font(FType.tiny())
                .foregroundColor(Palette.textSub)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Capsule().fill(Palette.sheet.opacity(0.9)))
                .padding(8)
        }
    }''', 1)
io.open(v, "w", encoding="utf-8").write(s)
print("PlayerView: volume removed + cover/lyric toggle")

# ---------- G) HomeView：热门歌单 ----------
h = os.path.join(root, "CarPlayer", "HomeView.swift")
s = io.open(h, encoding="utf-8").read()
s = s.replace('''                hotHeader
                hotColumns''', '''                hotHeader
                hotColumns
                hotPlaylistSection''')
s = s.replace('''            .padding(.bottom, 8)
        }
    }''', '''            .padding(.bottom, 8)
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
                Text("网易云")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                Button {
                    store.loadHotPlaylists(force: true)
                } label: {
                    Text("换一批")
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                        .padding(.horizontal, 12)
                        .frame(height: 30)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.plain)
                .padding(.leading, 8)
            }
            .padding(.top, 22)

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
    }''')
io.open(h, "w", encoding="utf-8").write(s)
print("HomeView: hot playlist section")
