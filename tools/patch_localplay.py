import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# ============ A) Downloader：校验文件 + 按魔数纠正扩展名 ============
d = os.path.join(root, "CarPlayer", "Downloader.swift")
t = io.open(d, encoding="utf-8").read()

old = """        let ext = location.pathExtension.isEmpty ? "mp3" : location.pathExtension.lowercased()
        let name = sanitize("\\(jobs[index].song.displaySinger) - \\(jobs[index].song.name)") + "." + ext
        let target = musicDirectory.appendingPathComponent(name)"""
new = """        // 校验：太小说明不是音频（多半是错误页/302 空响应）
        let size = (try? FileManager.default.attributesOfItem(atPath: location.path)[.size] as? Int) ?? 0
        guard let byteSize = size as? Int ?? (size as? NSNumber)?.intValue, byteSize > 16 * 1024 else {
            jobs[index].state = .failed
            store?.show("下载失败：文件异常（\\(byteSize) 字节）")
            return
        }
        let ext = Self.audioExtension(of: location) ?? "mp3"
        let name = sanitize("\\(jobs[index].song.displaySinger) - \\(jobs[index].song.name)") + "." + ext
        let target = musicDirectory.appendingPathComponent(name)"""
assert old in t, "ext anchor"
t = t.replace(old, new)

# 追加扩展名嗅探 + 磁盘管理
helper_anchor = """    private func sanitize(_ name: String) -> String {"""
helper = """    /// 按文件头判断真实音频格式（服务器常把 m4a/flac 当成 mp3 返回）
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

    private func sanitize(_ name: String) -> String {"""
assert helper_anchor in t
t = t.replace(helper_anchor, helper)

# 删除时同时清掉任务记录
old_del = """    /// 删除已下载的文件
    func deleteLocalFile(_ song: Song) {
        if let path = song.localPath {
            try? FileManager.default.removeItem(atPath: path)
        }
    }"""
new_del = """    /// 删除已下载的文件（含任务记录）
    func deleteLocalFile(_ song: Song) {
        if let path = song.localPath {
            try? FileManager.default.removeItem(atPath: path)
        }
        jobs.removeAll { $0.song.name == song.name && $0.song.displaySinger == song.displaySinger }
    }"""
if old_del in t:
    t = t.replace(old_del, new_del)
io.open(d, "w", encoding="utf-8").write(t)
print("Downloader: validate + real extension")

# ============ B) PlayerEngine：本地文件用 AVURLAsset 校验，失败给明确原因 ============
e = os.path.join(root, "CarPlayer", "PlayerEngine.swift")
v = io.open(e, encoding="utf-8").read()
old_start = """    private func startPlayback(url: URL, song: Song) {
        if let timeObserver, let player { player.removeTimeObserver(timeObserver) }
        if let itemEndObserver { NotificationCenter.default.removeObserver(itemEndObserver) }

        let item = AVPlayerItem(url: url)"""
new_start = """    private func startPlayback(url: URL, song: Song) {
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

        let item = AVPlayerItem(url: url)"""
assert old_start in v, "playback anchor"
v = v.replace(old_start, new_start)
io.open(e, "w", encoding="utf-8").write(v)
print("PlayerEngine: local file validation")
