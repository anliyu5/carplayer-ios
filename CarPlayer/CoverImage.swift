import Foundation
import SwiftUI
import UIKit
import Combine

/// 对应 Android util/ImageLoader + CoverLoader：内存 + 磁盘两级缓存
final class CoverLoader {
    static let shared = CoverLoader()

    private let memory = NSCache<NSString, UIImage>()
    private let session: URLSession
    private var inflight: [String: Task<UIImage?, Never>] = [:]
    private let lock = NSLock()

    private lazy var disk: URL = {
        let base = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("covers", isDirectory: true)
        try? FileManager.default.createDirectory(at: base, withIntermediateDirectories: true)
        return base
    }()

    init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        config.urlCache = URLCache(memoryCapacity: 8 << 20, diskCapacity: 64 << 20)
        session = URLSession(configuration: config)
    }

    func cachedImage(_ urlString: String?) -> UIImage? {
        guard let urlString, !urlString.isEmpty else { return nil }
        return memory.object(forKey: urlString as NSString)
    }

    func load(_ urlString: String?) async -> UIImage? {
        guard let urlString, let url = URL(string: urlString) else { return nil }
        if let hit = memory.object(forKey: urlString as NSString) { return hit }

        lock.lock()
        if let task = inflight[urlString] {
            lock.unlock()
            return await task.value
        }
        let task = Task<UIImage?, Never> { [weak self] in
            guard let self else { return nil }
            let file = self.disk.appendingPathComponent(self.key(urlString))
            if let data = try? Data(contentsOf: file), let img = UIImage(data: data) {
                self.memory.setObject(img, forKey: urlString as NSString)
                return img
            }
            do {
                let (data, _) = try await self.session.data(from: url)
                if let img = UIImage(data: data) {
                    self.memory.setObject(img, forKey: urlString as NSString)
                    try? data.write(to: file)
                    return img
                }
            } catch { }
            return nil
        }
        inflight[urlString] = task
        lock.unlock()
        let image = await task.value
        lock.lock(); inflight[urlString] = nil; lock.unlock()
        return image
    }

    private func key(_ s: String) -> String {
        let data = Data(s.utf8)
        var hash: UInt64 = 1469598103934665603
        for byte in data { hash = (hash ^ UInt64(byte)) &* 1099511628211 }
        return String(hash, radix: 16)
    }
}

/// 封面视图：占位底色 = drawable/bg_cover (#262A34, 16dp 圆角)
struct CoverImage: View {
    let url: String?
    var size: CGFloat
    var radius: CGFloat = Radius.cover
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: radius, style: .continuous).fill(Palette.cover)
            if let image = image {
                Image(uiImage: image).resizable().scaledToFill()
            } else {
                VectorIcon(icon: .note, size: size * 0.42, color: Palette.textSub.opacity(0.55))
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: radius, style: .continuous))
        .task(id: url) {
            if let img = await CoverLoader.shared.load(url) { image = img }
        }
    }

    @State private var image: UIImage?
}

/// 自适应尺寸封面（榜单卡 / 歌单卡 / 播放页大图用）
struct CoverBanner: View {
    let url: String?
    var radius: CGFloat = Radius.cover
    @State private var image: UIImage?

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: radius, style: .continuous).fill(Palette.cover)
            if let image {
                Image(uiImage: image).resizable().scaledToFill()
            } else {
                VectorIcon(icon: .note, size: 34, color: Palette.textSub.opacity(0.5))
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: radius, style: .continuous))
        .task(id: url) {
            if let img = await CoverLoader.shared.load(url) { image = img }
        }
    }
}
