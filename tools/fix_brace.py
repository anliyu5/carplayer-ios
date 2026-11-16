import io
p = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\CarPlayer\BuiltinSources.swift"
t = io.open(p, encoding="utf-8").read()
if "\n}\n\nenum SourceError" not in t:
    t = t.replace("\nenum SourceError", "\n}\n\nenum SourceError", 1)
io.open(p, "w", encoding="utf-8").write(t)
print("class brace inserted:", "\n}\n\nenum SourceError" in t)
