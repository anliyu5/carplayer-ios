import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
# 1) 删掉误写的占位行
p = os.path.join(root, "CarPlayer", "QingGate.swift")
t = io.open(p, encoding="utf-8").read()
bad = '        if let lineComment = body.range(of: "//") whereFalse: do { _ = lineComment }\n'
if bad in t:
    t = t.replace(bad, "")
    io.open(p, "w", encoding="utf-8").write(t)
    print("bad placeholder line removed")
else:
    # 兜底：按包含特征删除
    lines = [l for l in t.split("\n") if "whereFalse" not in l]
    t = "\n".join(lines)
    io.open(p, "w", encoding="utf-8").write(t)
    print("filtered whereFalse lines")
print("  whereFalse left:", "whereFalse" in io.open(p, encoding="utf-8").read())

# 2) 导入失败时把诊断信息带出来
a = os.path.join(root, "CarPlayer", "AppStore.swift")
s = io.open(a, encoding="utf-8").read()
old = '''        guard let config else {
            return "这份内容没能解析成青听音源配置（需要 lines 字段）。请确认粘贴的是 music.json 的网址，或完整的 JSON 内容。"
        }'''
new = '''        guard let config else {
            let detail = QingDebug.lastError.map { "\\n诊断：\\($0)" } ?? ""
            return "这份内容没能解析成青听音源配置（需要 lines 字段）。请确认粘贴的是 music.json 的网址，或完整的 JSON 内容。\\(detail)"
        }'''
assert old in s
s = s.replace(old, new)
io.open(a, "w", encoding="utf-8").write(s)
print("AppStore diagnostic message wired")

# 3) 设置页「诊断」里显示最近一次音源错误
f = os.path.join(root, "CarPlayer", "SettingsView.swift")
v = io.open(f, encoding="utf-8").read()
old_diag = '''            Text(store.crashLog.isEmpty ? "没有崩溃记录" : String(store.crashLog.prefix(240)))'''
new_diag = '''            Text(diagnosisText)'''
assert old_diag in v
v = v.replace(old_diag, new_diag)
anchor = "    private var versionRow: some View {"
helper = '''    private var diagnosisText: String {
        var parts: [String] = []
        if let error = QingDebug.lastError { parts.append("音源：" + error) }
        if !store.crashLog.isEmpty { parts.append(String(store.crashLog.prefix(200))) }
        if parts.isEmpty { parts.append("没有崩溃记录") }
        return parts.joined(separator: "\\n")
    }

'''
v = v.replace(anchor, helper + anchor)
io.open(f, "w", encoding="utf-8").write(v)
print("SettingsView diagnosis wired")
