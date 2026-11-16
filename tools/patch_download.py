import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ 1) Downloader：完成后登记到下载列表 + 全程 toast ============
d = os.path.join(root, "CarPlayer", "Downloader.swift")
t = io.open(d, encoding="utf-8").read()

t = t.replace("""    private var session: URLSession!""",
"""    private var session: URLSession!
    /// 下载完成后把记录写回 AppStore（弱引用避免循环）
    private weak var store: AppStore?""")

t = t.replace("""    func download(song: Song, quality: Quality, store: AppStore) {
        let key = song.id + ":" + song.source.rawValue
        guard !jobs.contains(where: { $0.id == key && $0.state != .failed }) else { return }""",
"""    func download(song: Song, quality: Quality, store: AppStore) {
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
        store.show("开始下载：\\(song.name)")""")

old_finish = """    private func finish(key: String, location: URL, success: Bool) {
        guard let index = jobs.firstIndex(where: { $0.id == key }) else { return }
        guard success else {
            jobs[index].state = .failed
            return
        }"""
new_finish = """    private func finish(key: String, location: URL, success: Bool) {
        guard let index = jobs.firstIndex(where: { $0.id == key }) else { return }
        guard success else {
            jobs[index].state = .failed
            store?.show("下载失败：\\(jobs[index].song.name)")
            return
        }"""
assert old_finish in t
t = t.replace(old_finish, new_finish)

old_ok = """        do {
            try FileManager.default.moveItem(at: location, to: target)
            jobs[index].state = .done
            jobs[index].progress = 1
        } catch {
            jobs[index].state = .failed
        }
    }"""
new_ok = """        do {
            try FileManager.default.moveItem(at: location, to: target)
            jobs[index].state = .done
            jobs[index].progress = 1
            var song = jobs[index].song
            song.localPath = target.path
            song.source = .local
            store?.registerDownload(song)
            store?.show("下载完成：\\(song.name)")
        } catch {
            jobs[index].state = .failed
            store?.show("下载失败：写入文件出错")
        }
    }

    /// 删除已下载的文件
    func deleteLocalFile(_ song: Song) {
        if let path = song.localPath {
            try? FileManager.default.removeItem(atPath: path)
        }
    }"""
assert old_ok in t
t = t.replace(old_ok, new_ok)
io.open(d, "w", encoding="utf-8").write(t)
print("Downloader: register + toasts")

# ============ 2) AppStore：登记 / 删除下载 ============
a = os.path.join(root, "CarPlayer", "AppStore.swift")
s = io.open(a, encoding="utf-8").read()
anchor = "    // MARK: - 播放封装"
addition = """    // MARK: - 下载记录
    func registerDownload(_ song: Song) {
        downloads.removeAll { $0.name == song.name && $0.displaySinger == song.displaySinger }
        downloads.insert(song, at: 0)
        save(downloads, "downloads")
    }

    func deleteDownload(_ song: Song) {
        if let path = song.localPath {
            try? FileManager.default.removeItem(atPath: path)
        }
        downloads.removeAll { $0.id == song.id }
        save(downloads, "downloads")
        show("已删除：\\(song.name)")
    }

    /// 把磁盘上已有的文件并进列表（重启后仍可见）
    func refreshLocalDownloads() {
        let scanned = Downloader.shared.scanLocalSongs()
        var merged = downloads
        for song in scanned where !merged.contains(where: { $0.localPath == song.localPath }) {
            merged.append(song)
        }
        merged.removeAll { song in
            guard let path = song.localPath else { return false }
            return !FileManager.default.fileExists(atPath: path)
        }
        if merged.count != downloads.count { downloads = merged; save(downloads, "downloads") }
    }

    // MARK: - 播放封装"""
assert anchor in s
s = s.replace(anchor, addition, 1)
io.open(a, "w", encoding="utf-8").write(s)
print("AppStore: download registry")
