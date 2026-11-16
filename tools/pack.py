import os, zipfile
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
out = os.path.join(root, "dist", "site", "CarPlayer-iOS-1.9.14-src.zip")
os.makedirs(os.path.dirname(out), exist_ok=True)
skip_dirs = {".git", "build", "dist", "__pycache__", "DerivedData"}
count = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if rel.startswith("dist") or rel.endswith(".pyc"):
                continue
            z.write(full, os.path.join("carplayer-ios", rel))
            count += 1
print("files", count, "size", os.path.getsize(out))
