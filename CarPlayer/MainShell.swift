import SwiftUI

/// 主界面：完全对齐 activity_main（res/v9.xml）
/// 结构：header(64+padding) → content(weight1) → miniPlayer(72) → navBar(78)
struct MainShell: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var player: PlayerEngine
    @EnvironmentObject private var router: Router

    var body: some View {
        VStack(spacing: 0) {
            header
            Group {
                switch router.tab {
                case .home: HomeView()
                case .library: LibraryView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            miniPlayer
            navBar
        }
        .background(Palette.bg.ignoresSafeArea())
    }

    // MARK: - header
    private var header: some View {
        HStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 3) {
                Text("Music")
                    .font(FType.h1())
                    .foregroundColor(Palette.text)
                Text("听你想听")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
            }
            Spacer(minLength: 0)
            Button {
                router.screen = .settings
            } label: {
                VectorIcon(icon: .settings, size: 24, color: Palette.text)
                    .frame(width: 52, height: 52)
                    .background(Circle().fill(Color.white.opacity(0.04)))
            }
            .buttonStyle(.plain)
            .accessibilityLabel("音源与设置")
        }
        .padding(.top, 18)
        .padding(.bottom, 8)
        .padding(.leading, 24)
        .padding(.trailing, 16)
    }

    // MARK: - miniPlayer
    @ViewBuilder
    private var miniPlayer: some View {
        if let song = player.current {
            HStack(spacing: 0) {
                CoverImage(url: song.picUrl, size: 46, radius: Radius.cover)
                VStack(alignment: .leading, spacing: 2) {
                    Text(song.name)
                        .font(FType.rowTitle())
                        .foregroundColor(Palette.text)
                        .lineLimit(1)
                    Text(song.displaySinger)
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                        .lineLimit(1)
                }
                .padding(.leading, 14)
                .frame(maxWidth: .infinity, alignment: .leading)

                Button {
                    player.toggle()
                } label: {
                    VectorIcon(icon: player.isPlaying ? .pause : .play, size: 24, color: Palette.text)
                        .frame(width: 52, height: 52)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("播放暂停")

                Button {
                    player.next()
                } label: {
                    VectorIcon(icon: .next, size: 24, color: Palette.text)
                        .frame(width: 52, height: 52)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("下一首")
            }
            .frame(height: 72)
            .padding(.horizontal, 14)
            .background(RoundedRectangle(cornerRadius: Radius.surface, style: .continuous).fill(Palette.surface))
            .padding(.horizontal, 16)
            .padding(.bottom, 8)
            .contentShape(Rectangle())
            .onTapGesture { router.screen = .player }
        }
    }

    // MARK: - navBar
    private var navBar: some View {
        HStack(spacing: 0) {
            navItem(tab: .home, icon: .home, title: "首页")
            navItem(tab: .library, icon: .library, title: "歌单")
        }
        .frame(height: 78)
        .background(Palette.navBg.ignoresSafeArea(edges: .bottom))
    }

    private func navItem(tab: Tab, icon: Icon, title: String) -> some View {
        let selected = router.tab == tab
        return Button {
            router.tab = tab
        } label: {
            VStack(spacing: 3) {
                VectorIcon(icon: icon, size: 26, color: selected ? Palette.accent : Palette.textSub)
                Text(title)
                    .font(FType.nav())
                    .foregroundColor(selected ? Palette.accent : Palette.textSub)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .buttonStyle(.plain)
    }
}
