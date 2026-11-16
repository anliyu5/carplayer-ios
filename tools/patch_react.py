import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# 1) 把 PlayerEngine 注入环境
p = os.path.join(root, "CarPlayer", "CarPlayerApp.swift")
t = io.open(p, encoding="utf-8").read()
old = """            RootView()
                .environmentObject(store)
                .environmentObject(router)"""
new = """            RootView()
                .environmentObject(store)
                .environmentObject(store.player)
                .environmentObject(router)"""
assert old in t, "app anchor missing"
t = t.replace(old, new)
io.open(p, "w", encoding="utf-8").write(t)
print("App: player injected")

# 2) MainShell 订阅 player
m = os.path.join(root, "CarPlayer", "MainShell.swift")
s = io.open(m, encoding="utf-8").read()
s = s.replace("""    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var router: Router""",
"""    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var player: PlayerEngine
    @EnvironmentObject private var router: Router""")
for a, b in [("store.player.current", "player.current"),
             ("store.player.toggle()", "player.toggle()"),
             ("store.player.next()", "player.next()"),
             ("store.player.isPlaying", "player.isPlaying")]:
    s = s.replace(a, b)
io.open(m, "w", encoding="utf-8").write(s)
print("MainShell: observes player")

# 3) PlayerEngine：seek 立即同步 + 歌词到达后对齐
e = os.path.join(root, "CarPlayer", "PlayerEngine.swift")
v = io.open(e, encoding="utf-8").read()
old_seek = """    func seek(_ time: Double) {
        let target = CMTime(seconds: max(0, min(time, duration)), preferredTimescale: 600)
        player?.seek(to: target)
        progress = target.seconds
        updateNowPlaying()
    }"""
new_seek = """    func seek(_ time: Double) {
        let clamped = max(0, min(time, duration))
        player?.seek(to: CMTime(seconds: clamped, preferredTimescale: 600))
        progress = clamped
        if let lyric, let idx = lyric.index(at: clamped) {
            lyricIndex = idx
        }
        updateNowPlaying()
    }"""
assert old_seek in v, "seek anchor missing"
v = v.replace(old_seek, new_seek)

old_lyric = """                Task { @MainActor in
                    if let lrc = await store.resolveLyric(for: song) {
                        self.lyric = lrc
                    }
                }"""
new_lyric = """                Task { @MainActor in
                    if let lrc = await store.resolveLyric(for: song) {
                        self.lyric = lrc
                        if let idx = lrc.index(at: self.progress) {
                            self.lyricIndex = idx
                        }
                    }
                }"""
assert old_lyric in v, "lyric anchor missing"
v = v.replace(old_lyric, new_lyric)
io.open(e, "w", encoding="utf-8").write(v)
print("PlayerEngine: seek/lyric sync")

# 4) 首页顺序：热门歌单在热歌榜上方
h = os.path.join(root, "CarPlayer", "HomeView.swift")
x = io.open(h, encoding="utf-8").read()
old_order = """                hotHeader
                hotColumns
                hotPlaylistSection"""
new_order = """                hotPlaylistSection
                hotHeader
                hotColumns"""
assert old_order in x, "home order anchor missing"
x = x.replace(old_order, new_order)
io.open(h, "w", encoding="utf-8").write(x)
print("HomeView: hot playlists above charts")

# 5) SongActions 改用 player 环境对象（避免读到不刷新的快照）
sa = os.path.join(root, "CarPlayer", "SongActions.swift")
s2 = io.open(sa, encoding="utf-8").read()
s2 = s2.replace("""    @EnvironmentObject private var store: AppStore
    @Environment(\\.dismiss) private var dismiss""",
"""    @EnvironmentObject private var store: AppStore
    @EnvironmentObject private var player: PlayerEngine
    @Environment(\\.dismiss) private var dismiss""")
s2 = s2.replace("store.player.queue", "player.queue")
s2 = s2.replace("store.player.current", "player.current")
s2 = s2.replace("store.player.play(song: current, queue: queue)", "player.play(song: current, queue: queue)")
io.open(sa, "w", encoding="utf-8").write(s2)
print("SongActions: uses player env")
