import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# --- 1) QingGate：超时 12s -> 4s，ticket 拿不到就直接放弃 ---
q = os.path.join(root, "CarPlayer", "QingGate.swift")
t = io.open(q, encoding="utf-8").read()
t = t.replace("cfg.timeoutIntervalForRequest = 12", "cfg.timeoutIntervalForRequest = 4")
t = t.replace('''        let ticket = await ensureTicket(base: base)''',
'''        let ticket: String?
        do {
            ticket = try await withTimeout(seconds: 5) { await ensureTicket(base: base) }
        }
        guard ticket != nil else { return nil }   // 授权拿不到就别耗时间，交给平台直连/跨源''')
t = t.replace('''    static func lyric(song: Song, config: QingConfig) async throws -> String? {''',
'''    /// 简单超时包装
    static func withTimeout<T>(seconds: Double, operation: @escaping () async -> T?) async throws -> T? {
        try await withThrowingTaskGroup(of: T?.self) { group in
            group.addTask { await operation() }
            group.addTask {
                try await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
                return nil
            }
            let first = try await group.next() ?? nil
            group.cancelAll()
            return first
        }
    }

    static func lyric(song: Song, config: QingConfig) async throws -> String? {''')
io.open(q, "w", encoding="utf-8").write(t)
print("QingGate timeouts shortened")

# --- 2) PlayerEngine：解析中状态 + 失败提示 ---
p = os.path.join(root, "CarPlayer", "PlayerEngine.swift")
s = io.open(p, encoding="utf-8").read()
s = s.replace("    @Published var errorText: String?",
              "    @Published var errorText: String?\n    @Published private(set) var isResolving = false")
s = s.replace('''        status = "正在解析音源…"
        errorText = nil''',
'''        status = "正在解析音源…"
        errorText = nil
        isResolving = true''')
s = s.replace('''            defer { isLoading = false }''',
'''            defer { isLoading = false; self.isResolving = false }''')
s = s.replace('''                status = "播放失败"
                errorText = "播放失败：\\(error.localizedDescription)"
                isPlaying = false''',
'''                status = "播放失败"
                let message = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
                errorText = "播放失败：" + message
                isPlaying = false
                store.show("播放失败：" + message)''')
io.open(p, "w", encoding="utf-8").write(s)
print("PlayerEngine resolving/error wired")
