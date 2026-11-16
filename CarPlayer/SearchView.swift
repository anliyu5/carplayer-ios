import SwiftUI

/// 搜索页：对齐 view_search（res/Fj.xml）
struct SearchView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router
    @FocusState private var focused: Bool
    @State private var keyword: String = ""
    @State private var menuSong: Song?

    var body: some View {
        VStack(spacing: 0) {
            titleBar
            searchBar
            sourceChips
            if !store.searchHistory.isEmpty && store.searchResults.isEmpty {
                historyBox
            }
            Text(store.searchStatus)
                .font(FType.chip())
                .foregroundColor(Palette.textSub)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 12)
            results
        }
        .padding(.horizontal, 20)
        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            Color.clear
                .frame(width: 76, height: 56)
                .contentShape(Rectangle())
                .onTapGesture { router.screen = .main }
        }
        .sheet(item: $menuSong) { song in
            SongActionSheet(song: song)
                .presentationDetents([.height(360)])
        }
    }

    private var titleBar: some View {
        HStack(spacing: 4) {
            Button {
                router.screen = .main
            } label: {
                VectorIcon(icon: .close, size: 20, color: Palette.text)
                    .frame(width: 64, height: 56)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("关闭搜索")
            Text("搜索")
                .font(FType.h2())
                .foregroundColor(Palette.text)
            Spacer(minLength: 0)
        }
        .frame(height: 56)
    }

    private var searchBar: some View {
        HStack(spacing: 10) {
            VectorIcon(icon: .search, size: 20, color: Palette.textSub.opacity(0.6))
            TextField("", text: $keyword, prompt: Text("搜索歌曲、歌手").foregroundColor(Palette.textSub))
                .font(FType.rowTitle())
                .foregroundColor(Palette.text)
                .focused($focused)
                .submitLabel(.search)
                .onSubmit(performSearch)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
            Button(action: performSearch) {
                Text("搜索")
                    .font(FType.rowTitle())
                    .foregroundColor(Palette.accent)
                    .padding(.horizontal, 16)
                    .frame(maxHeight: .infinity)
            }
            .buttonStyle(.plain)
        }
        .padding(.leading, 18)
        .padding(.trailing, 8)
        .frame(height: 56)
        .background(Capsule().fill(Palette.surface))
        .overlay(Capsule().stroke(Palette.stroke, lineWidth: 1))
    }

    // searchSources：音源筛选 chips（点一下立刻重搜）
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

    private var historyBox: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("搜索历史")
                    .font(FType.rowTitle().bold())
                    .foregroundColor(Palette.text)
                Spacer()
                Button {
                    store.clearSearchHistory()
                } label: {
                    Text("清空")
                        .font(FType.chip())
                        .foregroundColor(Palette.textSub)
                        .padding(6)
                }
                .buttonStyle(.plain)
            }
            FlowChips(items: store.searchHistory) { item in
                keyword = item
                performSearch()
            }
        }
        .padding(.top, 12)
    }

    private var results: some View {
        ScrollView(showsIndicators: false) {
            LazyVStack(spacing: 0) {
                if store.searching {
                    ProgressView().tint(Palette.accent).padding(.top, 40)
                }
                ForEach(Array(store.searchResults.enumerated()), id: \.element.id) { index, song in
                    SongRowView(song: song, index: index + 1) {
                        store.playAll(store.searchResults, startAt: index)
                        router.screen = .player
                    } onMore: {
                        menuSong = song
                    }
                }
            }
            .padding(.top, 6)
            .padding(.bottom, 12)
        }
    }

    private func performSearch() {
        focused = false
        store.search(keyword.isEmpty ? store.searchKeyword : keyword)
    }
}

/// 简易流式 chips（搜索历史）
struct FlowChips: View {
    let items: [String]
    var onTap: (String) -> Void
    private let columns = [GridItem(.adaptive(minimum: 80), spacing: 8)]

    var body: some View {
        LazyVGrid(columns: columns, alignment: .leading, spacing: 8) {
            ForEach(items, id: \.self) { item in
                Button {
                    onTap(item)
                } label: {
                    Text(item)
                        .font(FType.chip())
                        .foregroundColor(Palette.textSub)
                        .lineLimit(1)
                        .padding(.horizontal, 12)
                        .frame(height: 30)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.plain)
            }
        }
    }
}
