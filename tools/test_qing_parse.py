import io, json, re, urllib.request
url = "https://13413.kstore.vip/QingMusic/music.json"
req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
text = urllib.request.urlopen(req, timeout=20).read().decode("utf-8")

meta = {}
body = text
s = body.find("/**")
e = body.find("*/", s+3)
if s >= 0 and e > 0:
    header = body[s+3:e]
    for raw in header.split("\n"):
        line = raw.strip(" \t\r*")
        if not line.startswith("@"): continue
        parts = line[1:].split(" ", 1)
        if len(parts) == 2:
            meta[parts[0].lower()] = parts[1].strip()
    body = body[e+2:]

obj = json.loads(body)
lines = obj["lines"]
print("meta:", meta)
print("lines:", len(lines))
quality_map = {
 "standard":"k128","exhigh":"k320","lossless":"flac","flac":"flac","bili192":"flac",
 "hires":"hires","atmos":"atmos","atmos_plus":"atmos_plus","clear":"atmos_plus",
 "master":"master","jymaster":"master","sky":"spatial","sur":"spatial","jyeffect":"spatial"}
src_map = {"kw":"kw","kuwo":"kw","kg":"kg","kugou":"kg","tx":"tx","qq":"tx","wy":"wy",
           "netease":"wy","mg":"mg","migu":"mg","qs":"qs","qishui":"qs","bili":"bili","bilibili":"bili"}
bad = []
for l in lines:
    lid = l.get("id") or l.get("source")
    mapped = src_map.get((lid or "").lower())
    lv = l.get("levels") or []
    mapped_lv = [quality_map.get(x.lower()) for x in lv]
    unknown = [x for x, m in zip(lv, mapped_lv) if m is None]
    print(f'  line {lid:5s} name={l.get("name"):8s} enabled={l.get("enabled")} source={mapped} levels={lv} -> {mapped_lv} 未知={unknown}')
    if mapped is None or unknown: bad.append((lid, unknown))
print("\n全部可映射:", not bad, bad)
