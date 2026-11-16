import re
def detect(t):
    rules = [
        (r'y\.qq\.com[^\s]*(?:playlist/|id=|disstid=)(\d{4,})', 'tx'),
        (r'(?:disstid|songlistid)=(\d{4,})', 'tx'),
        (r'music\.163\.com[^\s]*(?:playlist[/?#]|id=)(\d{4,})', 'wy'),
    ]
    for pat, plat in rules:
        m = re.search(pat, t)
        if m: return plat, m.group(1)
    if t.isdigit() and len(t) >= 4: return 'wy', t
    return None

samples = [
 "https://163cn.tv/bk98xAFn",
 "https://music.163.com/m/playlist?app_version=9.6.27&id=8807204379&userid=2048932908",
 "https://music.163.com/playlist?id=443637511&user=abc",
 "https://music.163.com/#/playlist?id=443637511",
 "https://y.qq.com/n/ryqq/playlist/7944390462",
 "https://y.qq.com/n/yqq/playlist/7944390462.html",
 "https://i.y.qq.com/n2/m/share/details/playlist.html?id=7944390462&ADTAG=share",
 "7944390462",
]
for s0 in samples:
    print(f"{detect(s0)!s:28s} <- {s0[:70]}")
