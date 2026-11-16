import SwiftUI

enum Screen: Equatable {
    case main
    case player
    case playlist(String)
    case history
    case settings
    case downloads
    case search
}

enum Tab: Int {
    case home, library
}

@MainActor
final class Router: ObservableObject {
    @Published var screen: Screen = .main
    @Published var tab: Tab = .home
    @Published var searchVisible = false
}

@main
struct CarPlayerApp: App {
    @StateObject private var store = AppStore()
    @StateObject private var router = Router()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(store)
                .environmentObject(store.player)
                .environmentObject(router)
                .preferredColorScheme(.dark)
                .onAppear {
                    store.loadHotCharts()
                    if store.settings.autoPlayOnLaunch || store.settings.bootAutoStart {
                        resumeLastSong()
                    }
                }
        }
    }

    private func resumeLastSong() {
        guard let id = store.settings.lastSongId else { return }
        let all = store.playlists.flatMap { $0.songs } + store.favorites + store.history.map { $0.song }
        if let song = all.first(where: { $0.id == id }) {
            store.play(song: song, queue: [song])
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router

    var body: some View {
        ZStack {
            Palette.bg.ignoresSafeArea()
            switch router.screen {
            case .main:
                MainShell()
            case .player:
                PlayerView()
            case .playlist(let id):
                PlaylistView(playlistId: id)
            case .history:
                HistoryView()
            case .settings:
                SettingsView()
            case .downloads:
                DownloadView()
            case .search:
                SearchView()
            }
            if let toast = store.toast {
                VStack {
                    Spacer()
                    ToastView(text: toast)
                        .padding(.bottom, 120)
                    Spacer().frame(height: 0)
                }
                .transition(.opacity)
                .allowsHitTesting(false)
            }
        }
        .animation(.easeOut(duration: 0.16), value: store.toast)
    }
}
