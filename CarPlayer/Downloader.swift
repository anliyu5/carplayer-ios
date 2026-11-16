import Foundation

/// 对应 Android com.carplayer.repo.Downloader：下载到「文件 App → CarPlayer/Music」，
/// Android 侧是 手机存储/Music/Music，iOS 侧等价路径为 App 沙盒 Documents/Music。
@MainActor
final class Downloader: NSObject, ObservableObject {
    static let shared = Downloader()

    /// 任务标识映射（线程安全）
    final class Registry: @unchecked Sendable {
        private var map: [Int: String] = [:]
        private let lock = NSLock()
        func set(_ key: String, for id: Int) { lock.lock(); map[id] = key; lock.unlock() }
        func key(for id: Int) -> String { lock.lock(); defer { lock.unlock() }; return map[id] ?? "" }
    }

    struct Job: Identifiable {
        let song: Song
        var progress: Double
        var state: State
        var id: String { song.id + ":" + song.source.rawValue }
    }

    enum State: String {
        case waiting = "等待中"
        case running = "下载中"
        case done = "下载完成"
        case failed = "下载失败"
    }

    @Published private(set) var jobs: [Job] = []

    private var session: URLSession!
    /// 下载完成后把记录写回 AppStore（弱引用避免循环）
    private weak var store: AppStore?
    /// taskIdentifier -> song key，delegate 回调在非主线程，故用锁保护
    nonisolated private let registry = Registry()

    private override init() {
        super.init()
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        session = URLSession(configuration: config, delegate: self, delegateQueue: nil)
    }

    var musicDirectory: URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let dir = docs.appendingPathComponent("Music", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    func download(song: Song, quality: Quality, store: AppStore) {
        self.store = store
        let key = song.id + ":" + song.source.rawValue
        if jobs.contains(where: { $0.id == key && $0.state == .done }) {
            store.show("这首歌已经下载过了")
            return
        }
        guard !jobs.contains(where: { $0.id == key && $0.state != .failed }) else {
            store.show("正在下载中…")
            return
        }
        store.show("开始下载：\(song.name)")
        jobs.append(Job(song: song, progress: 0, state: .waiting))
        let index = jobs.count - 1

        Task { @MainActor in
            do {
                let url = try await store.resolveURL(for: song, quality: quality)
                var request = URLRequest(url: url)
                request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
                let dl = session.downloadTask(with: request)
                registry.set(key, for: dl.taskIdentifier)
                dl.resume()
                jobs[index].state = .running
            } catch {
                jobs[index].state = .failed
                store.show("下载失败：\(error.localizedDescription)")
            }
        }
    }

    func downloadAll(_ songs: [Song], quality: Quality, store: AppStore) {
        guard !songs.isEmpty else { store.show("没有可下载的歌曲"); return }
        for song in songs { download(song: song, quality: quality, store: store) }
        store.show("开始下载 \(songs.count) 首")
    }

    func remove(_ job: Job) {
        jobs.removeAll { $0.id == job.id }
    }

    func clearDone() {
        jobs.removeAll { $0.state == .done }
    }

    private func finish(key: String, location: URL, success: Bool) {
        guard let index = jobs.firstIndex(where: { $0.id == key }) else { return }
        guard success else {
            jobs[index].state = .failed
            store?.show("下载失败：\(jobs[index].song.name)")
            return
        }
        // 校验：太小说明不是音频（多半是错误页/302 空响应）
        let attrs = try? FileManager.default.attributesOfItem(atPath: location.path)
        let byteSize = (attrs?[.size] as? NSNumber)?.intValue ?? 0
        guard byteSize > 16 * 1024 else {
            jobs[index].state = .failed
            store?.show("下载失败：文件异常（\(byteSize) 字节，可能不是音频）")
            return
        }
        let ext = Self.audioExtension(of: location) ?? "mp3"
        let name = sanitize("\(jobs[index].song.displaySinger) - \(jobs[index].song.name)") + "." + ext
        let target = musicDirectory.appendingPathComponent(name)
        try? FileManager.default.removeItem(at: target)
        do {
            try FileManager.default.moveItem(at: location, to: target)
            jobs[index].state = .done
            jobs[index].progress = 1
            var song = jobs[index].song
            song.localPath = target.path
            song.source = .local
            store?.registerDownload(song)
            store?.show("下载完成：\(song.name)")
        } catch {
            jobs[index].state = .failed
            store?.show("下载失败：写入文件出错")
        }
    }

    /// 删除已下载的文件（含任务记录）
    func deleteLocalFile(_ song: Song) {
        if let path = song.localPath {
            try? FileManager.default.removeItem(atPath: path)
        }
        jobs.removeAll { $0.song.name == song.name && $0.song.displaySinger == song.displaySinger }
    }

    /// 按文件头判断真实音频格式（服务器常把 m4a/flac 当成 mp3 返回）
    static func audioExtension(of url: URL) -> String? {
        guard let handle = try? FileHandle(forReadingFrom: url) else { return nil }
        defer { try? handle.close() }
        let data = (try? handle.read(upToCount: 16)) ?? Data()
        guard data.count >= 4 else { return nil }
        let b = [UInt8](data)
        if b[0] == 0x49, b[1] == 0x44, b[2] == 0x33 { return "mp3" }           // ID3
        if b[0] == 0x66, b[1] == 0x4C, b[2] == 0x61, b[3] == 0x43 { return "flac" }
        if b[0] == 0x4F, b[1] == 0x67, b[2] == 0x67, b[3] == 0x53 { return "ogg" }
        if b[0] == 0x52, b[1] == 0x49, b[2] == 0x46, b[3] == 0x46 { return "wav" }
        if b.count >= 8, b[4] == 0x66, b[5] == 0x74, b[6] == 0x79, b[7] == 0x70 { return "m4a" }
        if b[0] == 0xFF, (b[1] & 0xE0) == 0xE0 { return "mp3" }                 // MPEG 帧同步
        return nil
    }

    private func sanitize(_ name: String) -> String {
        let invalid = CharacterSet(charactersIn: "/\\:*?\"<>|")
        return name.components(separatedBy: invalid).joined(separator: "_")
    }

    /// 扫描本地已下载音乐（对应 LocalMusic）
    func scanLocalSongs() -> [Song] {
        guard let files = try? FileManager.default.contentsOfDirectory(at: musicDirectory,
                                                                     includingPropertiesForKeys: nil) else { return [] }
        return files.compactMap { file in
            guard !file.hasDirectoryPath else { return nil }
            let base = file.deletingPathExtension().lastPathComponent
            let parts = base.components(separatedBy: " - ")
            let singer = parts.count > 1 ? parts[0] : "未知歌手"
            let name = parts.count > 1 ? parts[1] : base
            return Song(id: file.lastPathComponent, source: .local, name: name, singer: singer,
                        albumName: nil, picUrl: nil, interval: 0,
                        qualitys: [.k320], localPath: file.path)
        }
    }
}

extension Downloader: URLSessionDownloadDelegate {
    nonisolated func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                                didFinishDownloadingTo location: URL) {
        let key = registry.key(for: downloadTask.taskIdentifier)
        let ok = (downloadTask.response as? HTTPURLResponse).map { (200..<300).contains($0.statusCode) } ?? true
        let temp = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try? FileManager.default.copyItem(at: location, to: temp)
        Task { @MainActor in
            self.finish(key: key, location: temp, success: ok)
        }
    }

    nonisolated func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                                didWriteData bytesWritten: Int64,
                                totalBytesWritten: Int64,
                                totalBytesExpectedToWrite: Int64) {
        guard totalBytesExpectedToWrite > 0 else { return }
        let ratio = Double(totalBytesWritten) / Double(totalBytesExpectedToWrite)
        let key = registry.key(for: downloadTask.taskIdentifier)
        Task { @MainActor in
            if let index = self.jobs.firstIndex(where: { $0.id == key }) {
                self.jobs[index].progress = ratio
            }
        }
    }

    nonisolated func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        guard error != nil else { return }
        let key = registry.key(for: task.taskIdentifier)
        Task { @MainActor in
            if let index = self.jobs.firstIndex(where: { $0.id == key }) {
                self.jobs[index].state = .failed
            }
        }
    }
}

