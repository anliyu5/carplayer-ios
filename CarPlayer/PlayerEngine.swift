import Foundation
import AVFoundation
import MediaPlayer
import Combine

struct LyricLine: Identifiable, Hashable {
    let id = UUID()
    let time: Double
    let text: String
    let trans: String?
}

struct Lyric {
    var lines: [LyricLine]

    static func parse(_ lrc: String, trans tlyric: String? = nil) -> Lyric {
        var transMap: [Double: String] = [:]
        if let tlyric {
            for line in parseRaw(tlyric) { transMap[line.time] = line.text }
        }
        let main = parseRaw(lrc).sorted { $0.time < $1.time }
        let lines = main.map { LyricLine(time: $0.time, text: $0.text, trans: transMap[$0.time]) }
        return Lyric(lines: lines)
    }

    private static func parseRaw(_ text: String) -> [(time: Double, text: String)] {
        var out: [(Double, String)] = []
        let pattern = try? NSRegularExpression(pattern: #"\[(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?\]"#)
        for raw in text.split(separator: "\n") {
            let line = String(raw)
            guard let regex = pattern else { continue }
            let matches = regex.matches(in: line, range: NSRange(line.startIndex..., in: line))
            guard !matches.isEmpty else { continue }
            let content = regex.stringByReplacingMatches(in: line, range: NSRange(line.startIndex..., in: line), withTemplate: "")
                .trimmingCharacters(in: .whitespaces)
            for m in matches {
                guard m.numberOfRanges >= 3,
                      let mr = Range(m.range(at: 1), in: line),
                      let sr = Range(m.range(at: 2), in: line) else { continue }
                let minute = Double(line[mr]) ?? 0
                let second = Double(line[sr]) ?? 0
                var ms = 0.0
                if m.numberOfRanges >= 4, let tr = Range(m.range(at: 3), in: line) {
                    let frac = line[tr]
                    ms = (Double(frac) ?? 0) / pow(10, Double(frac.count))
                }
                out.append((minute * 60 + second + ms, content))
            }
        }
        return out
    }

    func index(at time: Double) -> Int? {
        guard !lines.isEmpty else { return nil }
        var lo = 0, hi = lines.count - 1, ans: Int?
        while lo <= hi {
            let mid = (lo + hi) / 2
            if lines[mid].time <= time { ans = mid; lo = mid + 1 } else { hi = mid - 1 }
        }
        return ans
    }
}

@MainActor
final class PlayerEngine: NSObject, ObservableObject {
    @Published private(set) var current: Song?
    @Published private(set) var queue: [Song] = []
    @Published private(set) var index: Int = 0
    @Published private(set) var isPlaying: Bool = false
    @Published private(set) var progress: Double = 0
    @Published private(set) var duration: Double = 0
    @Published private(set) var mode: PlayMode = .order
    @Published private(set) var lyric: Lyric?
    @Published var lyricIndex: Int = -1
    @Published var volume: Double = 0.85
    @Published var status: String = "准备播放"
    @Published var errorText: String?
    @Published private(set) var isResolving = false

    private let store: AppStore
    private var player: AVPlayer?
    private var timeObserver: Any?
    private var itemEndObserver: NSObjectProtocol?
    private var isLoading = false

    init(store: AppStore) {
        self.store = store
        super.init()
        configureSession()
        configureRemoteCommands()
    }

    // MARK: - 音频会话（对应 PlaybackService 前台服务 + 耳机/车机按键）
    private func configureSession() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback, mode: .default, options: [.allowBluetoothA2DP, .allowAirPlay])
        try? session.setActive(true)
    }

    private func configureRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()
        center.playCommand.addTarget { [weak self] _ in
            self?.resume(); return .success
        }
        center.pauseCommand.addTarget { [weak self] _ in
            self?.pause(); return .success
        }
        center.nextTrackCommand.addTarget { [weak self] _ in
            self?.next(); return .success
        }
        center.previousTrackCommand.addTarget { [weak self] _ in
            self?.prev(); return .success
        }
        center.changePlaybackPositionCommand.addTarget { [weak self] event in
            guard let e = event as? MPChangePlaybackPositionCommandEvent else { return .commandFailed }
            self?.seek(e.positionTime)
            return .success
        }
    }

    // MARK: - 播放控制
    func play(song: Song, queue: [Song]) {
        self.queue = queue
        self.index = queue.firstIndex(where: { $0.id == song.id && $0.source == song.source }) ?? 0
        load(song: song)
    }

    private func load(song: Song) {
        guard !isLoading else { return }
        isLoading = true
        current = song
        status = "正在解析音源…"
        errorText = nil
        isResolving = true
        progress = 0
        duration = song.interval
        lyric = nil
        lyricIndex = -1

        Task { @MainActor in
            defer { isLoading = false; self.isResolving = false }
            do {
                let url = try await store.resolveURL(for: song, quality: quality(for: song))
                startPlayback(url: url, song: song)
                store.addHistory(song)
                Task { @MainActor in
                    if let lrc = await store.resolveLyric(for: song) {
                        self.lyric = lrc
                        if let idx = lrc.index(at: self.progress) {
                            self.lyricIndex = idx
                        }
                    }
                }
            } catch {
                status = "播放失败"
                let message = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
                errorText = "播放失败：" + message
                isPlaying = false
                store.show("播放失败：" + message)
            }
        }
    }

    private func quality(for song: Song) -> Quality {
        if song.qualitys.contains(store.settings.playQuality) { return store.settings.playQuality }
        return song.bestQuality ?? .k320
    }

    private func startPlayback(url: URL, song: Song) {
        if let timeObserver, let player { player.removeTimeObserver(timeObserver) }
        if let itemEndObserver { NotificationCenter.default.removeObserver(itemEndObserver) }

        // 本地文件先确认能播（下载到的并非音频时立刻报错，而不是静默没声）
        if url.isFileURL {
            let asset = AVURLAsset(url: url)
            guard asset.isPlayable, asset.duration.seconds.isFinite else {
                status = "播放失败"
                errorText = "本地文件无法播放（可能不是音频文件），请删除后重新下载"
                isPlaying = false
                store.show("本地文件无法播放，请删除后重新下载")
                return
            }
            duration = asset.duration.seconds
        }

        let item = AVPlayerItem(url: url)
        let player = self.player ?? AVPlayer()
        self.player = player
        player.replaceCurrentItem(with: item)
        player.volume = Float(volume)
        player.play()
        isPlaying = true
        status = "正在播放"

        timeObserver = player.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.4, preferredTimescale: 600),
                                                     queue: .main) { [weak self] time in
            let seconds = CMTimeGetSeconds(time)
            let itemDuration = player.currentItem?.duration.seconds ?? .nan
            Task { @MainActor in
                guard let self, seconds.isFinite else { return }
                self.progress = seconds
                if itemDuration.isFinite, itemDuration > 0 { self.duration = itemDuration }
                if let lyric = self.lyric, let idx = lyric.index(at: seconds), idx != self.lyricIndex {
                    self.lyricIndex = idx
                }
            }
        }

        itemEndObserver = NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime,
                                                                object: item, queue: .main) { [weak self] _ in
            Task { @MainActor in self?.handleEnd() }
        }

        store.settings.lastSongId = song.id
        updateNowPlaying()
    }

    func resume() {
        player?.play()
        isPlaying = true
        status = "正在播放"
    }

    func pause() {
        player?.pause()
        isPlaying = false
        status = "已暂停"
    }

    func toggle() {
        guard current != nil else { return }
        isPlaying ? pause() : resume()
    }

    func seek(_ time: Double) {
        let clamped = max(0, min(time, duration))
        player?.seek(to: CMTime(seconds: clamped, preferredTimescale: 600))
        progress = clamped
        if let lyric, let idx = lyric.index(at: clamped) {
            lyricIndex = idx
        }
        updateNowPlaying()
    }

    func next() {
        guard !queue.isEmpty else { return }
        switch mode {
        case .repeatOne:
            seek(0); resume()
        case .shuffle:
            index = Int.random(in: 0..<queue.count)
            load(song: queue[index])
        case .order:
            if index + 1 < queue.count {
                index += 1
                load(song: queue[index])
            } else {
                index = 0
                load(song: queue[index])
            }
        }
    }

    func prev() {
        guard !queue.isEmpty else { return }
        if progress > 5 { seek(0); return }
        index = index == 0 ? queue.count - 1 : index - 1
        load(song: queue[index])
    }

    /// 播完一首：单曲循环重播，其余按顺序/随机
    private func handleEnd() {
        if mode == .repeatOne {
            seek(0)
            resume()
        } else {
            next()
        }
    }

    func cycleMode() {
        mode = mode.next
        store.show(mode.display)
    }

    func setVolume(_ value: Double) {
        volume = value
        player?.volume = Float(value)
        store.settings.volume = value
    }

    func updateNowPlaying() {
        guard let song = current else { return }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: song.name,
            MPMediaItemPropertyArtist: song.displaySinger,
            MPMediaItemPropertyAlbumTitle: song.displayAlbum,
            MPMediaItemPropertyPlaybackDuration: duration,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: progress,
            MPNowPlayingInfoPropertyPlaybackRate: isPlaying ? 1.0 : 0.0
        ]
        if let artwork = CoverLoader.shared.cachedImage(song.picUrl) {
            info[MPMediaItemPropertyArtwork] = MPMediaItemArtwork(boundsSize: artwork.size) { _ in artwork }
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }
}
