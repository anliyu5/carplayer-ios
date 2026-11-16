import io
p = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\dist\site\index.html"
t = io.open(p, encoding="utf-8").read()

anchor = '  <h2>出 ipa 的两条路</h2>'
card = '''  <div class="card">
    <div class="row">
      <div class="grow">
        <div class="name">GitHub 仓库 · CI 记录</div>
        <div class="meta">anliyu5/carplayer-ios · Actions 已跑通（macos-15-intel + Xcode 16.4）</div>
      </div>
      <a class="btn plain" href="https://github.com/anliyu5/carplayer-ios" target="_blank" rel="noreferrer">打开仓库</a>
    </div>
  </div>

'''
assert anchor in t
t = t.replace(anchor, card + anchor)

t = t.replace('''      <div class="name">② 没有 Mac：GitHub Actions 自动出包</div>''',
              '''      <div class="name">② 没有 Mac：GitHub Actions 自动出包（已跑通）</div>''')
t = t.replace('''      workflow 已内置在 <code>.github/workflows/ios-build.yml</code>（macos-14，免签名编译并打包 Payload → ipa）。''',
              '''      workflow 已内置在 <code>.github/workflows/ios-build.yml</code>，用 <code>macos-15-intel</code> + Xcode 16.4 免签名编译并打包 Payload → ipa。<br>
      <code>tools/push_github.py</code> 已把「建库 → 推送 → 触发 → 抓 ipa → 更新本页」全部自动化，单次约 2 分半。''')
io.open(p, "w", encoding="utf-8").write(t)
print("index.html patched,", len(t), "chars")
