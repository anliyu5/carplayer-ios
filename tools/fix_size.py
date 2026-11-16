import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "Downloader.swift")
t = io.open(p, encoding="utf-8").read()
old = """        let size = (try? FileManager.default.attributesOfItem(atPath: location.path)[.size] as? Int) ?? 0
        guard let byteSize = size as? Int ?? (size as? NSNumber)?.intValue, byteSize > 16 * 1024 else {
            jobs[index].state = .failed
            store?.show("下载失败：文件异常（\\(byteSize) 字节）")
            return
        }"""
new = """        let attrs = try? FileManager.default.attributesOfItem(atPath: location.path)
        let byteSize = (attrs?[.size] as? NSNumber)?.intValue ?? 0
        guard byteSize > 16 * 1024 else {
            jobs[index].state = .failed
            store?.show("下载失败：文件异常（\\(byteSize) 字节，可能不是音频）")
            return
        }"""
assert old in t, "size anchor missing"
t = t.replace(old, new)
io.open(p, "w", encoding="utf-8").write(t)
print("Downloader: size guard fixed")
