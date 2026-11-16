import json, io, plistlib, os
site = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\docs"
print("manifest ipa url:", plistlib.load(open(os.path.join(site,"manifest.plist"),"rb"))["items"][0]["assets"][0]["url"])
s = json.load(io.open(os.path.join(site,"altstore-source.json"), encoding="utf-8"))
print("altstore url:", s["apps"][0]["versions"][0]["downloadURL"])
print("source url:", s["apps"][0]["iconURL"])
p = plistlib.load(open(os.path.join(site,"CarPlayer.mobileconfig"),"rb"))
print("webclip url:", p["PayloadContent"][0]["URL"])
