import re
def detect(t):
    tl = t.lower()
    def first(pat):
        m = re.search(pat, t)
        return m.group(1) if m else None
    if "qq.com" in tl:
        for pat in (r"playlist/(\d{4,})", r"[?&](?:id|disstid|songlistid)=(\d{4,})", r"(?:disstid|songlistid)=(\d{4,})"):
            v = first(pat)
            if v: return ("tx", v)
    if "163.com" in tl or "163cn.tv" in tl:
        for pat in (r"/playlist/(\d{4,})", r"[?&]id=(\d{4,})", r"playlist[^\s]*?id=(\d{4,})"):
            v = first(pat)
            if v: return ("wy", v)
    if t.isdigit() and len(t) >= 4: return ("wy", t)
    return None

samples = [
 "https://163cn.tv/bk98xAFn",
 "https://music.163.com/m/playlist?app_version=9.6.27&id=8807204379&userid=2048932908&dlt=0846",
 "https://music.163.com/playlist?id=443637511&user=abc",
 "https://music.163.com/#/playlist?id=443637511",
 "https://y.music.163.com/m/playlist?id=8807204379",
 "https://y.qq.com/n/ryqq/playlist/7944390462",
 "https://i.y.qq.com/n2/m/share/details/playlist.html?id=7944390462&ADTAG=share",
 "https://c6.y.qq.com/base/fcgi-bin/u?__=AbCdEf",
 "7944390462",
]
for s0 in samples:
    print(f"{detect(s0)!s:26s} <- {s0[:76]}")
