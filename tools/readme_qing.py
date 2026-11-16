import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "README.md")
t = io.open(p, encoding="utf-8").read()
section = """
## 6. 青听音源配置（music.json）实测结构

官方配置长这样（`https://13413.kstore.vip/QingMusic/music.json`）：

```jsonc
/**
 * @name 青听音源
 * @version 1.1
 * @author 微信公众号: 元力菌
 */
{
  "lines": [
    { "id": "kw", "name": "小窝源", "enabled": true,
      "searchApi": "fetchSearchMusic", "detailApi": "fetchMusicDetail",
      "levels": ["standard","exhigh","lossless","atmos","atmos_plus","master"] },
    { "id": "kg", "name": "小狗源", "levels": ["standard","exhigh","lossless","hires","atmos","clear"] },
    { "id": "wy", "name": "小云源", "levels": ["standard","exhigh","lossless","hires","sky","jyeffect","jymaster"] },
    { "id": "tx", "name": "小Q源", "levels": ["standard","exhigh","lossless","sur","jymaster"] },
    { "id": "qs", "name": "汽水源", "levels": ["standard","exhigh","lossless","hires","atmos"] },
    { "id": "bili", "name": "哔哩哔哩", "levels": ["bili192"] },
    { "id": "mg", "name": "小粉源", "levels": ["standard"] }
  ]
}
```

要点：

- **lines 里没有 url 字段**；网关根地址由配置自身网址推导：`https://13413.kstore.vip/QingMusic/music.json` → `https://13413.kstore.vip`。
- 头部 `/** @name … */` 会被解析成音源标题/版本/作者并显示在设置页。
- `id` 映射到平台（kw/kg/wy/tx/qs/bili/mg → 酷我/酷狗/网易/QQ/汽水/哔哩哔哩/咪咕）；
- `levels` 映射到音质：`standard→128K`、`exhigh→320K`、`lossless→FLAC`、`hires→Hi-Res`、`atmos/atmos_plus/clear→全景声`、`master/jymaster→母带`、`sky/sur/jyeffect→沉浸环绕`、`bili192→FLAC`。
- 播放地址走网关：`GET {base}/v1/music/resolve-url`（依次尝试 `source/id/level`、`platform/musicId/quality`、`api/source/id/level` 等参数组合，返回体里任意 http 链接都会被采纳），授权走 `{base}/v1/gateway/ticket`（拿不到 ticket 不阻断）。
- 搜索不依赖网关：按配置里启用的线路直接用各平台公开接口搜（`SourceEngine` 那套），保证「导入即可搜」。

"""
if "## 6. 青听音源配置" not in t:
    t = t.rstrip() + "\n" + section
    io.open(p, "w", encoding="utf-8").write(t)
    print("README + qing section")
else:
    print("already present")
