import json, urllib.parse, urllib.request
UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Referer":"https://music.163.com/"})
    return urllib.request.urlopen(req, timeout=25).read()
j=json.loads(get("https://music.163.com/api/v6/playlist/detail?id=8807204379&n=1000"))
pl=j["playlist"]
partial=pl.get("tracks") or []
ids=[t["id"] for t in pl.get("trackIds") or []]
print("name:", pl["name"], "| tracks:", len(partial), "| trackIds:", len(ids))
songs={str(t["id"]):t["name"] for t in partial}
missing=[i for i in ids if str(i) not in songs]
print("missing:", len(missing))
batches=0
while missing:
    chunk=missing[:100]; missing=missing[100:]
    c=json.dumps([{"id":i} for i in chunk], separators=(",",":"))
    u="https://music.163.com/api/v3/song/detail?c="+urllib.parse.quote(c)
    d=json.loads(get(u))
    for s in d.get("songs") or []:
        songs[str(s["id"])]=s["name"]
    batches+=1
print("batches:", batches, "| resolved:", len(songs), "/", len(ids))
order_ok = all(str(i) in songs for i in ids)
print("all ids resolved:", order_ok)
print("sample:", [songs[str(i)] for i in ids[:5]])
