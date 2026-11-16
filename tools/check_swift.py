import io, os, glob, re

def strip_swift(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        # 多行字符串 """
        if src.startswith('"""', i):
            j = src.find('"""', i + 3)
            i = n if j < 0 else j + 3
            out.append('""')
            continue
        # 原始字符串 #"..."#
        if c == '#' and i + 1 < n and src[i+1] == '"':
            j = src.find('"#', i + 2)
            i = n if j < 0 else j + 2
            out.append('""')
            continue
        # 普通字符串
        if c == '"':
            i += 1
            while i < n:
                if src[i] == '\\': i += 2; continue
                if src[i] == '"': i += 1; break
                i += 1
            out.append('""')
            continue
        # 行注释
        if src.startswith('//', i):
            j = src.find('\n', i)
            i = n if j < 0 else j
            continue
        # 块注释
        if src.startswith('/*', i):
            j = src.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)

bad = []
for f in sorted(glob.glob(os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "*.swift"))):
    body = strip_swift(io.open(f, encoding="utf-8").read())
    for o, c, name in [("{", "}", "brace"), ("(", ")", "paren"), ("[", "]", "bracket")]:
        if body.count(o) != body.count(c):
            bad.append((os.path.basename(f), name, body.count(o), body.count(c)))
print("issues:", bad if bad else "none")
