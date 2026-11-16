import io, os, re
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "SettingsView.swift")
t = io.open(p, encoding="utf-8").read()

# 1) 删掉「粘贴脚本导入 / 怎么获取音源？」那一排
start = t.index('            HStack(spacing: 10) {\n                Button {\n                    showScriptSheet = true')
end = t.index('            Button {\n                showQingSheet = true')
t = t[:start] + '''            Text("点右上角「导入音源」：可粘贴 .js 脚本、青听 music.json 的网址或整段 JSON，也能从文件里选。")
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .padding(.horizontal, 4)
                .padding(.top, 6)

''' + t[end:]

# 2) 删掉「青听音源配置 → 导入 music.json」整行
start = t.index('            Button {\n                showQingSheet = true')
end = t.index('        }\n        .padding(.top, 8)\n    }', start)
t = t[:start] + t[end:]

# 3) 删除 qingSheet / importQing / 相关状态
for anchor_start, anchor_end in [
    ("    private var qingSheet: some View {", "    private var helpSheet: some View {"),
]:
    s = t.index(anchor_start); e = t.index(anchor_end)
    t = t[:s] + t[e:]

t = t.replace("    @State private var showQingSheet = false\n", "")
t = t.replace("    @State private var qingText = \"\"\n", "")

# importQing() 整个方法删除
s = t.index("    private func importQing() {")
e = t.index("    private func importPlaylist() {")
t = t[:s] + t[e:]

# 4) fileImporter：统一填入脚本框（自动识别 .js / music.json）
old_imp = '''            if importingScriptFile {
                scriptText = text
            } else {
                qingText = text
                importQing()
            }'''
if old_imp in t:
    t = t.replace(old_imp, '''            scriptText = text
            importingScriptFile = true''')

# 5) 去掉 qingSheet 的 presentation 挂载
t = t.replace('        .sheet(isPresented: $showQingSheet) { qingSheet.presentationDetents([.height(400)]) }\n', "")

io.open(p, "w", encoding="utf-8").write(t)
print("SettingsView trimmed to one import entry; chars:", len(t))
for k in ["showQingSheet", "qingText", "private var qingSheet", "importQing()"]:
    print(f"  {k} ->", "present" if k in t else "removed")
