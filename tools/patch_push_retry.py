import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "tools", "push_github.py")
t = io.open(p, encoding="utf-8").read()
old = '''        try:
            with urllib.request.urlopen(req, timeout=90) as resp:'''
new = '''        last_error = None
        for attempt in range(4):
            try:
                return self._send(req, method, path, expect, raw)
            except SystemExit:
                raise
            except Exception as exc:      # 网络抖动：退避重试
                last_error = exc
                time.sleep(2 + attempt * 3)
        raise SystemExit(f"{method} {path} failed after retries: {last_error}")

    def _send(self, req, method, path, expect, raw):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:'''
assert old in t
t = t.replace(old, new)
io.open(p, "w", encoding="utf-8").write(t)
print("push_github: retry added")
