import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "SettingsView.swift")
t = io.open(p, encoding="utf-8").read()

# 1) 粘贴文本：自动区分 青听配置(含 lines) / lx 脚本
old = '''            } else {
                let message = await store.importScript(text: text)
                store.show(message)
                if message.hasPrefix("已导入") { showScriptSheet = false }
            }'''
new = '''            } else if text.contains("\\"lines\\"") || text.contains("lines\\":") || text.contains("/**") {
                let message = await store.importQing(json: text)
                store.show(message)
                if message.hasPrefix("已导入") { showScriptSheet = false }
            } else {
                let message = await store.importScript(text: text)
                store.show(message)
                if message.hasPrefix("已导入") { showScriptSheet = false }
            }'''
assert old in t
t = t.replace(old, new)

# 2) 弹窗文案：改成「导入音源」，说明三种贴法
t = t.replace('sheetContainer(title: "粘贴音源脚本") {', 'sheetContainer(title: "导入音源") {')
t = t.replace('''            Text("把 .js 音源脚本的全部内容粘贴到这里；也支持 http/https 网址，或青听 music.json 的网址。")''',
'''            Text("三选一：① 青听 music.json 的网址　② .js 音源脚本的全部内容　③ 上面两者的网址。导入时会自动识别类型。")''')
io.open(p, "w", encoding="utf-8").write(t)
print("import entry unified")
