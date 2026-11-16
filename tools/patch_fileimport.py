import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "SettingsView.swift")
t = io.open(p, encoding="utf-8").read()

# import UniformTypeIdentifiers
if "import UniformTypeIdentifiers" not in t:
    t = t.replace("import UIKit", "import UIKit\nimport UniformTypeIdentifiers")

# 新增状态
t = t.replace("    @State private var busy = false",
'''    @State private var busy = false
    @State private var showFileImporter = false
    @State private var importingScriptFile = false''')

# 挂 fileImporter（放在 body 的最后一个 .sheet 之后）
anchor = "        .sheet(isPresented: $showCrash) { crashSheet.presentationDetents([.medium]) }"
addition = anchor + '''
        .fileImporter(isPresented: $showFileImporter,
                      allowedContentTypes: [.json, .plainText, .data],
                      allowsMultipleSelection: false) { result in
            guard case .success(let urls) = result, let url = urls.first else { return }
            let scoped = url.startAccessingSecurityScopedResource()
            defer { if scoped { url.stopAccessingSecurityScopedResource() } }
            guard let text = try? String(contentsOf: url, encoding: .utf8) else {
                store.show("读取文件失败，换个文件试试")
                return
            }
            if importingScriptFile {
                scriptText = text
            } else {
                qingText = text
                importQing()
            }
        }'''
assert anchor in t
t = t.replace(anchor, addition)

# 青听 sheet 增加「从文件选择」
qing_btn_anchor = '''            Button {
                importQing()
            } label: {
                Text(busy ? "正在导入…" : "导入配置")'''
qing_file_btn = '''            Button {
                importingScriptFile = false
                showFileImporter = true
            } label: {
                Text("从文件选择 music.json")
                    .font(FType.chip())
                    .foregroundColor(Palette.text)
                    .frame(maxWidth: .infinity).frame(height: 44)
                    .surfaceCard()
            }
            .buttonStyle(.plain)
            .padding(.top, 10)

''' + qing_btn_anchor
assert qing_btn_anchor in t
t = t.replace(qing_btn_anchor, qing_file_btn)

# 脚本 sheet 增加「从文件选择」
script_btn_anchor = '''                Button {
                    importScript()
                } label: {'''
script_file = '''                Button {
                    importingScriptFile = true
                    showFileImporter = true
                } label: {
                    Text("从文件")
                        .font(FType.chip())
                        .foregroundColor(Palette.text)
                        .frame(maxWidth: .infinity).frame(height: 44)
                        .surfaceCard()
                }
                .buttonStyle(.plain)

''' + script_btn_anchor
assert script_btn_anchor in t
t = t.replace(script_btn_anchor, script_file, 1)

io.open(p, "w", encoding="utf-8").write(t)
print("SettingsView file importer added:", len(t), "chars")
print("  fileImporter:", ".fileImporter(" in t, "| UTI import:", "UniformTypeIdentifiers" in t)
