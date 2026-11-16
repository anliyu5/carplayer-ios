import urllib.request, json, re
text = urllib.request.urlopen(urllib.request.Request(
    "https://13413.kstore.vip/QingMusic/music.json", headers={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}),
    timeout=20).read().decode("utf-8")

meta = {}
body = text.replace("\ufeff", "")
while True:
    s = body.find("/*")
    e = body.find("*/", s + 2) if s >= 0 else -1
    if s < 0 or e < 0: break
    for raw in body[s+2:e].split("\n"):
        line = raw.strip(" \t\r*")
        if not line.startswith("@"): continue
        parts = line[1:].split(" ", 1)
        if len(parts) == 2: meta[parts[0].lower()] = parts[1].strip()
    body = body[:s] + body[e+2:]
body = body.strip()

def slice_json(t):
    i, j = t.find("{"), t.rfind("}")
    return t[i:j+1] if 0 <= i < j else t

ok = False
for cand in (body, slice_json(body)):
    try:
        root = json.loads(cand)
    except Exception as ex:
        print("  json fail:", ex); continue
    lines = root.get("lines") or (root.get("data") or {}).get("lines") or []
    if not lines:
        print("  no lines in candidate"); continue
    ok = True
    print("解析成功：meta=", meta.get("name"), meta.get("version"))
    for l in lines:
        print("   ", l.get("id"), l.get("name"), l.get("enabled"), l.get("levels"))
    break
print("RESULT:", "OK" if ok else "FAIL")
