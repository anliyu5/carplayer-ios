import hashlib, os, re, glob
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
uid = lambda k: hashlib.md5(k.encode()).hexdigest()[:24].upper()
target = uid("target")
scheme = os.path.join(root, "CarPlayer.xcodeproj", "xcshareddata", "xcschemes", "CarPlayer.xcscheme")
with open(scheme, encoding="utf-8") as f:
    text = f.read()
text = text.replace("TARGET_PLACEHOLDER", target)
with open(scheme, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print("scheme target =", target)

# pbxproj 引用完整性
pbx = open(os.path.join(root, "CarPlayer.xcodeproj", "project.pbxproj"), encoding="utf-8").read()
defined = set(re.findall(r"^\t\t([0-9A-F]{24}) ", pbx, re.M))
used = set(re.findall(r"([0-9A-F]{24})", pbx))
missing = sorted(used - defined)
print("defined", len(defined), "used", len(used), "missing", len(missing), missing[:5])

# Swift 花括号 / 圆括号平衡粗检
bad = []
for path in glob.glob(os.path.join(root, "CarPlayer", "*.swift")):
    src = open(path, encoding="utf-8").read()
    # 去掉字符串字面量与注释（粗粒度）
    stripped = re.sub(r'"""(?:.|\n)*?"""', '""', src)
    stripped = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', stripped)
    stripped = re.sub(r"//[^\n]*", "", stripped)
    stripped = re.sub(r"/\*(?:.|\n)*?\*/", "", stripped)
    for open_ch, close_ch, name in [("{", "}", "brace"), ("(", ")", "paren"), ("[", "]", "bracket")]:
        if stripped.count(open_ch) != stripped.count(close_ch):
            bad.append((os.path.basename(path), name, stripped.count(open_ch), stripped.count(close_ch)))
print("balance issues:", bad if bad else "none")
