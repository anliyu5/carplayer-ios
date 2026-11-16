import plistlib, json, io, os
site = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\dist\site"
p = os.path.join(site, "CarPlayer.mobileconfig")
with open(p, "rb") as f:
    prof = plistlib.load(f)
print("mobileconfig keys:", sorted(prof.keys()))
print("  type:", prof["PayloadType"], "| payloads:", [c["PayloadType"] for c in prof["PayloadContent"]])
print("  label:", prof["PayloadContent"][0]["Label"], "| url:", prof["PayloadContent"][0]["URL"])
print("  icon bytes:", len(prof["PayloadContent"][0]["Icon"]))
m = os.path.join(site, "manifest.plist")
with open(m, "rb") as f:
    man = plistlib.load(f)
asset_kinds = [a["kind"] for a in man["items"][0]["assets"]]
print("manifest assets:", asset_kinds, "| bundle-version:", man["items"][0]["metadata"]["bundle-version"])
s = json.load(io.open(os.path.join(site, "altstore-source.json"), encoding="utf-8"))
v = s["apps"][0]["versions"][0]
print("altstore source:", s["name"], "| app:", s["apps"][0]["name"], v["version"], "| size:", v["size"])
print("  downloadURL:", v["downloadURL"])
