import re

# 复刻 Swift 版解析逻辑（含修复后的保留大小写），计算每个图标路径的包围盒
def tokens(s, keep_case=True):
    out, buf = [], ""
    def flush():
        nonlocal buf
        if buf:
            try: out.append(float(buf))
            except: pass
            buf = ""
    for ch in s:
        if ch.isdigit() or ch in ".-+":
            if ch == "-" and buf: flush()
            buf += ch
        elif ch in "eE":
            buf += ch
        elif ch.isalpha():
            flush(); out.append(ch if keep_case else ch.upper())
        else:
            flush()
    flush()
    return out

def bbox(d, keep_case=True):
    toks = tokens(d, keep_case)
    i = 0; cmd = "M"; cur = (0.0, 0.0); pts = []
    def num():
        nonlocal i
        if i < len(toks) and isinstance(toks[i], float):
            i += 1; return toks[i-1]
        return 0.0
    while i < len(toks):
        if isinstance(toks[i], str):
            cmd = toks[i]; i += 1
        abs_ = cmd.isupper()
        c = cmd.upper()
        if c == "M":
            x, y = num(), num(); cur = (x, y) if abs_ else (cur[0]+x, cur[1]+y); pts.append(cur)
        elif c == "L":
            x, y = num(), num(); cur = (x, y) if abs_ else (cur[0]+x, cur[1]+y); pts.append(cur)
        elif c == "H":
            x = num(); cur = (x if abs_ else cur[0]+x, cur[1]); pts.append(cur)
        elif c == "V":
            y = num(); cur = (cur[0], y if abs_ else cur[1]+y); pts.append(cur)
        elif c in "CQST":
            n = 6 if c == "C" else 4 if c in "QS" else 2
            for _ in range(n // 2):
                x, y = num(), num()
                p = (x, y) if abs_ else (cur[0]+x, cur[1]+y)
                pts.append(p)
            cur = pts[-1]
        elif c == "A":
            for _ in range(5): num()
            x, y = num(), num(); cur = (x, y) if abs_ else (cur[0]+x, cur[1]+y); pts.append(cur)
        elif c == "Z":
            pass
        else:
            i += 1
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (round(min(xs),1), round(min(ys),1), round(max(xs),1), round(max(ys),1))

src = open(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\CarPlayer\Icons.swift", encoding="utf-8").read()
paths = dict(re.findall(r'case \.(\w+):\s*return "([^"]+)"', src))
sample = ["home","library","search","settings","play","pause","prev","next","more","download","heart","chevron","back","delete","check","note"]
print(f"{'icon':10s} {'修复后 bbox (保留大小写)':38s} {'旧的 bbox (全大写)':30s}")
for k in sample:
    d = paths.get(k)
    if not d: continue
    good, bad = bbox(d, True), bbox(d, False)
    flag = "" if (good[0] >= -2 and good[1] >= -2 and good[2] <= 26 and good[3] <= 26) else "  <-- 仍需检查"
    print(f"{k:10s} {str(good):38s} {str(bad):30s}{flag}")
