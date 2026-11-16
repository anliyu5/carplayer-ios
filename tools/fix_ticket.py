import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "QingGate.swift")
t = io.open(p, encoding="utf-8").read()
old = '''        let ticket: String?
        do {
            ticket = try await withTimeout(seconds: 5) { await ensureTicket(base: base) }
        }
        guard ticket != nil else { return nil }   // 授权拿不到就别耗时间，交给平台直连/跨源'''
new = '''        var ticket: String?
        do {
            ticket = try await withTimeout(seconds: 5) { await ensureTicket(base: base) }
        } catch {
            ticket = nil
        }
        guard ticket != nil else { return nil }   // 授权拿不到就别耗时间，交给平台直连/跨源'''
assert old in t
t = t.replace(old, new)
io.open(p, "w", encoding="utf-8").write(t)
print("ticket binding fixed")
