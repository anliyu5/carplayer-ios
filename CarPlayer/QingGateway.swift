import Foundation
import CryptoKit

/// 青听网关客户端 —— 完全按 Android `com.carplayer.source.qing.QingGate` 的反编译结果实现。
///
/// 关键点（源码级还原）：
///   HOSTS = ["https://musicserver.haitangw.cc", "https://qt.haitangw.net"]（失败轮换）
///   APP_ID = "qingmusic-android"、APP_VERSION = "1.4.0"、HMAC 密钥 = qm-gw-…
///   签名串 = join("\n", [APP_ID, ts, nonce, "POST", path, sha256(body)])
///   X-Qing-Sign = HMAC-SHA256(secret, 签名串) 的 hex
///   ticket：POST /v1/gateway/ticket  {"deviceId","appVersion","platform"}
///   播放地址：POST /v1/music/resolve-url  {"source","rid","level"}  → data.url
enum QingGateway {
    static let hosts = ["https://musicserver.haitangw.cc", "https://qt.haitangw.net"]
    private static let appId = "qingmusic-android"
    private static let appVersion = "1.4.0"
    private static let secret = "qm-gw-7c1f4e9a2b8d5360e1a7c4f9b2d8036c"
    private static let ticketPath = "/v1/gateway/ticket"
    private static let resolvePath = "/v1/music/resolve-url"

    private static var ticket: String?
    private static var ticketAt: Date = .distantPast
    private static let ticketTTL: TimeInterval = 8 * 3600   // Android: TICKET_TTL = 28_800_000 ms
    private static var hostIndex = 0

    private static let session: URLSession = {
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 12
        cfg.httpAdditionalHeaders = ["User-Agent": "qingmusic-android"]
        return URLSession(configuration: cfg)
    }()

    // MARK: - 设备 ID（持久化，32 位 hex，与 Android Store.qingDeviceId 一致）
    static var deviceId: String {
        let key = "qing.deviceId"
        if let saved = UserDefaults.standard.string(forKey: key), !saved.isEmpty { return saved }
        let id = UUID().uuidString.replacingOccurrences(of: "-", with: "").lowercased()
        UserDefaults.standard.set(id, forKey: key)
        return id
    }

    static func resetAuth() {
        ticket = nil
        ticketAt = .distantPast
    }

    // MARK: - 签名
    private static func sha256Hex(_ text: String) -> String {
        SHA256.hash(data: Data(text.utf8)).map { String(format: "%02x", $0) }.joined()
    }

    private static func hmacHex(_ message: String) -> String {
        let key = SymmetricKey(data: Data(secret.utf8))
        let code = HMAC<SHA256>.authenticationCode(for: Data(message.utf8), using: key)
        return code.map { String(format: "%02x", $0) }.joined()
    }

    private static func makeRequest(path: String, body: String, bearer: String?) -> URLRequest {
        let ts = String(Int(Date().timeIntervalSince1970 * 1000))
        let nonce = (0..<16).map { _ in String(format: "%02x", Int.random(in: 0...255)) }.joined()
        let requestId = UUID().uuidString.replacingOccurrences(of: "-", with: "").lowercased()
        let canonical = [appId, ts, nonce, "POST", path, sha256Hex(body)].joined(separator: "\n")
        let sign = hmacHex(canonical)

        let base = hosts[hostIndex % hosts.count]
        var request = URLRequest(url: URL(string: base + path)!)
        request.httpMethod = "POST"
        request.httpBody = Data(body.utf8)
        request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue(requestId, forHTTPHeaderField: "X-Request-Id")
        request.setValue(appId, forHTTPHeaderField: "X-Qing-App-Id")
        request.setValue(appVersion, forHTTPHeaderField: "X-Qing-App-Version")
        request.setValue(deviceId, forHTTPHeaderField: "X-Qing-Device-Id")
        request.setValue(ts, forHTTPHeaderField: "X-Qing-Ts")
        request.setValue(nonce, forHTTPHeaderField: "X-Qing-Nonce")
        request.setValue(sign, forHTTPHeaderField: "X-Qing-Sign")
        if let bearer, !bearer.isEmpty {
            request.setValue("Bearer \(bearer)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    private static func post(path: String, json: [(key: String, value: String)], bearer: String?) async -> (Int, [String: Any])? {
        // 与 org.json 一致：保持调用方给的键顺序，保证签名串与请求体完全一致
        let body = "{" + json.map { "\"\($0.key)\":\"\($0.value)\"" }.joined(separator: ",") + "}"
        let request = makeRequest(path: path, body: body, bearer: bearer)
        guard let (data, response) = try? await session.data(for: request) else { return nil }
        let code = (response as? HTTPURLResponse)?.statusCode ?? 0
        let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
        return (code, obj)
    }

    // MARK: - 授权
    static func ensureTicket(force: Bool = false) async -> String? {
        if !force, let ticket, Date().timeIntervalSince(ticketAt) < ticketTTL { return ticket }
        let payload: [(key: String, value: String)] = [("deviceId", deviceId), ("appVersion", appVersion), ("platform", "android")]
        for attempt in 0..<2 {
            if let (code, obj) = await post(path: ticketPath, json: payload, bearer: nil),
               (code == 200 || code == 201),
               let value = obj["ticket"] as? String, !value.isEmpty {
                ticket = value
                ticketAt = Date()
                return value
            }
            if attempt == 0 { hostIndex += 1; await Task.yield() }
        }
        return nil
    }

    // MARK: - 播放地址
    /// source：kw/kg/tx/wy/mg/qs/bili；rid：各平台的歌曲 ID；level：网关音质名
    static func resolveURL(source: String, rid: String, level: String) async throws -> URL? {
        guard !rid.isEmpty else { throw SourceError.noResolver("歌曲 ID 为空，换一首试试") }
        guard var bearer = await ensureTicket() else {
            throw SourceError.noResolver("音源授权失败：没有拿到 ticket")
        }

        let payload: [(key: String, value: String)] = [("source", source), ("rid", rid), ("level", level)]
        for attempt in 0..<2 {
            guard let (code, obj) = await post(path: resolvePath, json: payload, bearer: bearer) else {
                hostIndex += 1
                continue
            }
            if code == 200 || code == 201 {
                if let data = obj["data"] as? [String: Any],
                   let urlString = data["url"] as? String,
                   let url = URL(string: urlString), url.scheme?.hasPrefix("http") == true {
                    QingDebug.lastError = nil
                    return url
                }
                let reason = (obj["reason"] as? String) ?? ""
                let message = (obj["message"] as? String) ?? "音源没有返回播放地址"
                let codeText = (obj["code"] as? String) ?? ""
                if attempt == 0, codeText.contains("SIGN") || codeText.contains("UPGRADE")
                    || reason.contains("SIGN") || reason.contains("UPGRADE") || message.contains("授权") {
                    // 授权过期：刷新 ticket 后重试
                    bearer = await ensureTicket(force: true) ?? bearer
                    continue
                }
                throw SourceError.noResolver("青听网关：\(message)\(reason.isEmpty ? "" : "（\(reason)）")")
            }
            // 401：换域名 + 重新取票
            hostIndex += 1
            bearer = await ensureTicket(force: true) ?? bearer
        }
        throw SourceError.noResolver("青听网关暂不可用（授权或网络异常）")
    }
}
