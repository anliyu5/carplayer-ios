import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "Icons.swift")
t = io.open(p, encoding="utf-8").read()

old_tok = '''            } else if ch.isLetter {
                flush()
                out.append(.command(Character(ch.uppercased())))
            } else {'''
new_tok = '''            } else if ch.isLetter {
                flush()
                // 关键：保留大小写！小写 = 相对坐标，大写 = 绝对坐标。
                // 之前这里 upperсased() 把 c/l/s/q/t/h/v 全变成绝对命令，图标才会糊成一团乱码。
                out.append(.command(ch))
            } else {'''
assert old_tok in t
t = t.replace(old_tok, new_tok)

# 命令判定处也保持原样（switch 用 uppercased 归一化已是对的）
io.open(p, "w", encoding="utf-8").write(t)
print("Icons.swift patched, chars:", len(t))
print("  keeps case:", "out.append(.command(ch))" in t)
