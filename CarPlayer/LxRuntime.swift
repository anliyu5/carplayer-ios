import Foundation
import JavaScriptCore
import CommonCrypto

/// LX 自定义音源脚本运行时（对应 Android com.carplayer.source.custom.LxRuntime / CustomSourceManager）
///
/// 完全按 lx 官方 runtime.js 的协议实现：
///   1. 注入 __lx_native_call__ / utils.* 宿主函数
///   2. 执行 assets/lx/runtime.js（与 Android 版同一份脚本，已作为资源打进 App）
///   3. 调用 lx_setup(key, id, name, description, version, author, homepage, rawScript)
///   4. 执行脚本本体：脚本内部通过 lx.on('request') / lx.send('inited') 与宿主交互
final class LxRuntimeEngine {

    /// 单次脚本会话（一个 JSContext 对应一个脚本）
    private final class Session {
        let context: JSContext
        let key: String
        var initInfo: [String: Any]?
        var response: [String: Any]?
        var logs: [String] = []
        var timers: [Timer] = []

        init(context: JSContext, key: String) {
            self.context = context
            self.key = key
        }

        func fire(_ action: String, _ payload: [String: Any]) {
            guard let data = try? JSONSerialization.data(withJSONObject: payload),
                  let text = String(data: data, encoding: .utf8) else { return }
            _ = context.objectForKeyedSubscript("__lx_native__")?.call(withArguments: [key, action, text])
        }

        func fireRaw(_ action: String, _ value: Int) {
            _ = context.objectForKeyedSubscript("__lx_native__")?.call(withArguments: [key, action, value])
        }

        /// 在串行队列上泵事件循环，等待条件成立（脚本里可能出现 await / setTimeout）
        func wait(_ timeout: TimeInterval, until condition: () -> Bool) -> Bool {
            let deadline = Date().addingTimeInterval(timeout)
            while Date() < deadline {
                if condition() { return true }
                RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.02))
            }
            return condition()
        }
    }

    private let queue = DispatchQueue(label: "com.carplayer.lx", qos: .userInitiated)
    private let logLock = NSLock()
    private(set) var logs: [String] = []

    // MARK: - 对外 API
    func probe(script: String) async -> ScriptMeta? {
        await withCheckedContinuation { cont in
            queue.async { cont.resume(returning: self.runProbe(script: script)) }
        }
    }

    func musicURL(meta: ScriptMeta, song: Song, quality: Quality) async throws -> URL {
        let raw: String? = await withCheckedContinuation { cont in
            queue.async {
                let info: [String: Any] = ["type": quality.lxKey, "musicInfo": self.scriptSong(song)]
                cont.resume(returning: try? self.request(meta: meta, action: "musicUrl", song: song, info: info))
            }
        }
        guard let raw, let url = URL(string: raw), url.scheme?.hasPrefix("http") == true else {
            throw SourceError.noResolver("音源未返回播放地址")
        }
        return url
    }

    func lyric(meta: ScriptMeta, song: Song) async throws -> String? {
        await withCheckedContinuation { cont in
            queue.async {
                let info: [String: Any] = ["musicInfo": self.scriptSong(song)]
                let obj = try? self.requestObject(meta: meta, action: "lyric", song: song, info: info)
                cont.resume(returning: obj?["lyric"] as? String)
            }
        }
    }

    func artwork(meta: ScriptMeta, song: Song) async -> String? {
        await withCheckedContinuation { cont in
            queue.async {
                let info: [String: Any] = ["musicInfo": self.scriptSong(song)]
                cont.resume(returning: try? self.request(meta: meta, action: "pic", song: song, info: info))
            }
        }
    }

    // MARK: - 载荷
    private func scriptSong(_ song: Song) -> [String: Any] {
        var dict: [String: Any] = [
            "songmid": song.id,
            "id": song.id,
            "name": song.name,
            "singer": song.displaySinger,
            "albumName": song.displayAlbum,
            "interval": String(format: "%02d:%02d", Int(song.interval) / 60, Int(song.interval) % 60),
            "source": song.source.rawValue,
            "qualitys": song.qualitys.map { $0.lxKey }
        ]
        for (k, v) in song.extra { dict[k] = v }
        if let pic = song.picUrl { dict["img"] = pic }
        return dict
    }

    // MARK: - runtime.js
    private static let runtimeSource: String = {
        if let url = Bundle.main.url(forResource: "lx-runtime", withExtension: "js"),
           let text = try? String(contentsOf: url, encoding: .utf8) {
            return text
        }
        return ""
    }()

    private func makeSession(script: String) -> Session? {
        guard !LxRuntimeEngine.runtimeSource.isEmpty, let context = JSContext() else { return nil }
        let session = Session(context: context, key: UUID().uuidString)
        let key = session.key

        let console = JSValue(newObjectIn: context)
        let logBlock: @convention(block) (JSValue) -> Void = { value in
            let line = value.toString() ?? ""
            self.logLock.lock()
            self.logs.append(line)
            if self.logs.count > 500 { self.logs.removeFirst(200) }
            self.logLock.unlock()
        }
        console?.setObject(logBlock, forKeyedSubscript: "log" as NSString)
        console?.setObject(logBlock, forKeyedSubscript: "warn" as NSString)
        console?.setObject(logBlock, forKeyedSubscript: "error" as NSString)
        context.setObject(console, forKeyedSubscript: "console" as NSString)

        // 脚本 → 宿主
        let native: @convention(block) (JSValue, JSValue, JSValue) -> Void = { _, action, data in
            self.handleNative(session: session, action: action.toString() ?? "", dataJSON: data.toString() ?? "null")
        }
        context.setObject(native, forKeyedSubscript: "__lx_native_call__" as NSString)

        // utils
        let str2b64: @convention(block) (String) -> String = { input in
            Data(input.utf8).base64EncodedString()
        }
        context.setObject(str2b64, forKeyedSubscript: "__lx_native_call__utils_str2b64" as NSString)

        let b642buf: @convention(block) (String) -> String = { input in
            let data = Data(base64Encoded: input) ?? Data()
            return "[" + [UInt8](data).map { String($0) }.joined(separator: ",") + "]"
        }
        context.setObject(b642buf, forKeyedSubscript: "__lx_native_call__utils_b642buf" as NSString)

        let str2md5: @convention(block) (String) -> String = { input in md5(input) }
        context.setObject(str2md5, forKeyedSubscript: "__lx_native_call__utils_str2md5" as NSString)

        let aes: @convention(block) (String, String, String, JSValue) -> String = { data, keyB64, ivB64, mode in
            let ecb = (mode.toString() ?? "").contains("ECB")
            return aesCBCPKCS7(dataB64: data, keyB64: keyB64, ivB64: ivB64, ecb: ecb)
        }
        context.setObject(aes, forKeyedSubscript: "__lx_native_call__utils_aes_encrypt" as NSString)

        let rsa: @convention(block) (String, String, JSValue) -> String = { _, _, _ in "" }
        context.setObject(rsa, forKeyedSubscript: "__lx_native_call__utils_rsa_encrypt" as NSString)

        let timer: @convention(block) (Int, Int) -> Void = { identifier, _ in
            let t = Timer(timeInterval: 0, repeats: false) { _ in
                session.fireRaw("__set_timeout__", identifier)
            }
            session.timers.append(t)
            RunLoop.current.add(t, forMode: .default)
        }
        context.setObject(timer, forKeyedSubscript: "__lx_native_call__set_timeout" as NSString)

        context.exceptionHandler = { _, exception in
            self.logLock.lock()
            self.logs.append("JS错误: " + (exception?.toString() ?? ""))
            self.logLock.unlock()
        }

        context.evaluateScript(LxRuntimeEngine.runtimeSource)
        guard let setup = context.objectForKeyedSubscript("lx_setup") else { return nil }
        setup.call(withArguments: [key, key, "自定义音源", "LX 自定义源脚本", "1.0.0", "unknown", "", script])
        context.evaluateScript(script)
        return session
    }

    private func runProbe(script: String) -> ScriptMeta? {
        guard let session = makeSession(script: script) else { return nil }
        _ = session.wait(8) { session.initInfo != nil }
        guard let initInfo = session.initInfo,
              let sourceInfo = initInfo["sources"] as? [String: Any] else { return nil }

        var sources: [String: [String]] = [:]
        for (name, value) in sourceInfo {
            if let dict = value as? [String: Any], let qualitys = dict["qualitys"] as? [String] {
                sources[name] = qualitys
            }
        }
        guard !sources.isEmpty else { return nil }

        let info = session.context.objectForKeyedSubscript("lx")?.objectForKeyedSubscript("currentScriptInfo")
        let name = info?.objectForKeyedSubscript("name")?.toString() ?? "未命名音源"
        let version = info?.objectForKeyedSubscript("version")?.toString() ?? "1.0.0"
        let author = info?.objectForKeyedSubscript("author")?.toString() ?? ""
        let desc = info?.objectForKeyedSubscript("description")?.toString() ?? ""
        let homepage = info?.objectForKeyedSubscript("homepage")?.toString() ?? ""

        return ScriptMeta(id: sha1(script), name: name, version: version, author: author,
                          description: desc, homepage: homepage, sources: sources, script: script)
    }

    private func request(meta: ScriptMeta, action: String, song: Song, info: [String: Any]) throws -> String {
        guard let obj = try requestObject(meta: meta, action: action, song: song, info: info) else {
            throw SourceError.noResolver("音源没有返回播放地址")
        }
        if let data = obj["data"] as? [String: Any], let url = data["url"] as? String { return url }
        if let str = obj["data"] as? String { return str }
        throw SourceError.noResolver("音源没有返回播放地址")
    }

    private func requestObject(meta: ScriptMeta, action: String, song: Song, info: [String: Any]) throws -> [String: Any]? {
        guard let session = makeSession(script: meta.script) else {
            throw SourceError.noResolver("脚本环境加载失败")
        }
        session.wait(3) { session.initInfo != nil }

        session.fire("request", [
            "requestKey": meta.id,
            "data": ["source": song.source.rawValue, "action": action, "info": info]
        ])
        _ = session.wait(15) { session.response != nil }
        guard let response = session.response, (response["status"] as? Bool) == true else {
            let message = (session.response?["errorMessage"] as? String) ?? "音源没有返回播放地址"
            throw SourceError.noResolver(message)
        }
        return response["result"] as? [String: Any]
    }

    // MARK: - 宿主事件
    private func handleNative(session: Session, action: String, dataJSON: String) {
        guard let data = try? JSONSerialization.jsonObject(with: Data(dataJSON.utf8)) as? [String: Any] else { return }
        switch action {
        case "init":
            session.initInfo = data["info"] as? [String: Any]

        case "request":
            // 脚本通过 lx.request() 发起的 http 请求
            let requestKey = data["requestKey"] as? String ?? ""
            let inner = data["data"] as? [String: Any] ?? [:]
            let resp = syncRequest(inner)
            let ok = (resp["status"] as? Bool) ?? false
            let payload: [String: Any] = [
                "requestKey": requestKey,
                "error": ok ? NSNull() : (resp["errorMessage"] as? String ?? "请求失败"),
                "response": ok
                    ? ["statusCode": resp["statusCode"] ?? 200,
                       "body": resp["body"] ?? "",
                       "headers": resp["headers"] ?? [:]]
                    : NSNull()
            ]
            session.fire("response", payload)

        case "response":
            // 脚本对 musicUrl / lyric / pic 的最终应答：{requestKey, status, result}
            session.response = data

        default:
            break
        }
    }

    /// 同步执行脚本发出的 http 请求（运行在 runtime 串行队列）
    private func syncRequest(_ data: [String: Any]) -> [String: Any] {
        guard let urlString = data["url"] as? String, let url = URL(string: urlString) else {
            return ["status": false, "errorMessage": "请求地址为空"]
        }
        let options = data["options"] as? [String: Any] ?? [:]
        var request = URLRequest(url: url)
        request.httpMethod = (options["method"] as? String) ?? "GET"
        request.timeoutInterval = 12
        if let headers = options["headers"] as? [String: String] {
            headers.forEach { request.setValue($0.value, forHTTPHeaderField: $0.key) }
        }
        if let body = options["body"] as? String {
            request.httpBody = body.data(using: .utf8)
        } else if let form = options["form"] as? [String: String] {
            var comps = URLComponents()
            comps.queryItems = form.map { URLQueryItem(name: $0.key, value: "\($0.value)") }
            request.httpBody = comps.percentEncodedQuery?.data(using: .utf8)
            request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        }

        var result: [String: Any] = ["status": false, "errorMessage": "请求超时"]
        let semaphore = DispatchSemaphore(value: 0)
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() }
            if let error {
                result = ["status": false, "errorMessage": error.localizedDescription]
                return
            }
            let http = response as? HTTPURLResponse
            var headers: [String: String] = [:]
            http?.allHeaderFields.forEach { key, value in
                if let k = key as? String, let v = value as? String { headers[k] = v }
            }
            let text = String(data: data ?? Data(), encoding: .utf8) ?? ""
            result = ["status": true, "body": text, "headers": headers,
                      "statusCode": http?.statusCode ?? 200]
        }
        task.resume()
        _ = semaphore.wait(timeout: .now() + 14)
        return result
    }
}

// MARK: - 工具
func md5(_ input: String) -> String {
    let data = Data(input.utf8)
    var digest = [UInt8](repeating: 0, count: Int(CC_MD5_DIGEST_LENGTH))
    data.withUnsafeBytes { buffer in
        _ = CC_MD5(buffer.baseAddress, CC_LONG(data.count), &digest)
    }
    return digest.map { String(format: "%02x", $0) }.joined()
}

func sha1(_ input: String) -> String {
    let data = Data(input.utf8)
    var digest = [UInt8](repeating: 0, count: Int(CC_SHA1_DIGEST_LENGTH))
    data.withUnsafeBytes { buffer in
        _ = CC_SHA1(buffer.baseAddress, CC_LONG(data.count), &digest)
    }
    return digest.map { String(format: "%02x", $0) }.joined()
}

private func aesCBCPKCS7(dataB64: String, keyB64: String, ivB64: String, ecb: Bool) -> String {
    guard let data = Data(base64Encoded: dataB64), let key = Data(base64Encoded: keyB64) else { return "" }
    let iv = Data(base64Encoded: ivB64) ?? Data(repeating: 0, count: 16)
    var outLength = 0
    var out = Data(count: data.count + kCCBlockSizeAES128)
    let capacity = out.count            // 先取容量，避免闭包内再访问 out 造成独占访问冲突
    let options = ecb ? CCOptions(kCCOptionECBMode | kCCOptionPKCS7Padding) : CCOptions(kCCOptionPKCS7Padding)
    let status = out.withUnsafeMutableBytes { outBytes -> CCCryptorStatus in
        guard let outPtr = outBytes.baseAddress else { return CCCryptorStatus(kCCMemoryFailure) }
        return data.withUnsafeBytes { dataBytes in
            key.withUnsafeBytes { keyBytes in
                iv.withUnsafeBytes { ivBytes in
                    CCCrypt(CCOperation(kCCEncrypt), CCAlgorithm(kCCAlgorithmAES), options,
                            keyBytes.baseAddress, key.count,
                            ecb ? nil : ivBytes.baseAddress,
                            dataBytes.baseAddress, data.count,
                            outPtr, capacity, &outLength)
                }
            }
        }
    }
    guard status == kCCSuccess else { return "" }
    out.removeSubrange(outLength..<out.count)
    return out.base64EncodedString()
}
