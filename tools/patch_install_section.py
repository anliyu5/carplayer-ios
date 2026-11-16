import io, os
pages = "https://anliyu5.github.io/carplayer-ios"

section = f'''  <h2>装到 iPhone 桌面</h2>

  <div class="card">
    <div class="row">
      <div class="grow">
        <div class="name">① 描述文件 CarPlayer.mobileconfig</div>
        <div class="meta">装完桌面直接出现 <b>Music</b> 图标（Web Clip），点开进安装页 · 不需要签名 / 开发者账号<br>
          下载后若没自动进设置：文件 App → 点开 .mobileconfig → 设置 → 安装</div>
      </div>
      <a class="btn" href="{pages}/CarPlayer.mobileconfig" download>下载描述文件</a>
    </div>
  </div>

  <div class="card">
    <div class="row">
      <div class="grow">
        <div class="name">② AltStore / SideStore 源 → 真 App 图标</div>
        <div class="meta">免费 Apple ID 即可，手机端自动签名安装，图标可正常启动（7 天自动续签）<br>
          源地址：<code>{pages}/altstore-source.json</code></div>
      </div>
      <a class="btn" href="{pages}/altstore-source.json" target="_blank" rel="noreferrer">打开源</a>
    </div>
  </div>

  <div class="card">
    <div class="row">
      <div class="grow">
        <div class="name">③ OTA 安装页（itms-services）</div>
        <div class="meta">一次点击装到桌面 · 需要<b>已签名</b> ipa（含本机 UDID），未签名包系统会拒绝<br>
          <code>{pages}/install.html</code></div>
      </div>
      <a class="btn plain" href="{pages}/install.html" target="_blank" rel="noreferrer">打开 OTA 页</a>
    </div>
  </div>

  <div class="card flat">
    <div class="warn" style="border-left:0;padding-left:0">
      iOS 没有「安装配置文件 → 自动装 App」这种能力：配置文件只能加桌面图标（Web Clip）。
      真·App 上桌面只有三条路 —— OTA（需签名 ipa）、AltStore 自签、MDM 推送。
      详细对比与命令见 <a href="{pages}/INSTALL.md" style="color:#FFB020">INSTALL.md</a>。
    </div>
  </div>

'''

for p in [r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\dist\site\index.html", r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios\docs\index.html"]:
    t = io.open(p, encoding="utf-8").read()
    anchor = '  <h2>出 ipa 的两条路</h2>'
    if '装到 iPhone 桌面' in t:
        print("already patched:", p)
        continue
    assert anchor in t, p
    t = t.replace(anchor, section + anchor)
    io.open(p, "w", encoding="utf-8").write(t)
    print("patched:", p, len(t), "chars")
