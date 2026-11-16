import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# 1) 热门歌单区块：标题 + 换一批 + 一行说明（对齐截图）
h = os.path.join(root, "CarPlayer", "HomeView.swift")
x = io.open(h, encoding="utf-8").read()
old = """            HStack {
                Text("热门歌单")
                    .font(FType.section())
                    .foregroundColor(Palette.text)
                Spacer()
                Text("网易云")
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                Button {
                    store.loadHotPlaylists(force: true)
                } label: {
                    Text("换一批")
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                        .padding(.horizontal, 12)
                        .frame(height: 30)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.plain)
                .padding(.leading, 8)
            }
            .padding(.top, 22)"""
new = """            HStack {
                Text("热门歌单")
                    .font(FType.section())
                    .foregroundColor(Palette.text)
                Spacer()
                Button {
                    store.loadHotPlaylists(force: true)
                } label: {
                    Text("换一批")
                        .font(FType.sub())
                        .foregroundColor(Palette.textSub)
                        .padding(.horizontal, 16)
                        .frame(height: 36)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.plain)
            }
            .padding(.top, 22)

            Text("网易云歌单 · 点封面播放并展开列表")
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 6)"""
assert old in x, "home header anchor missing"
x = x.replace(old, new)
io.open(h, "w", encoding="utf-8").write(x)
print("HomeView: hot playlist header aligned")

# 2) 歌单卡片：远程歌单显示「网易云 · N 首」
c = os.path.join(root, "CarPlayer", "Components.swift")
t = io.open(c, encoding="utf-8").read()
old_card = """            Text("\\(playlist.count) 首")
                .font(FType.subSm())
                .foregroundColor(Palette.textSub)
                .lineLimit(1)
                .padding(.top, 2)"""
new_card = """            Text(playlist.isRemote
                 ? "\\(playlist.source.display) · \\(playlist.count) 首"
                 : "\\(playlist.count) 首")
                .font(FType.subSm())
                .foregroundColor(Palette.textSub)
                .lineLimit(1)
                .padding(.top, 2)"""
assert old_card in t, "card anchor missing"
t = t.replace(old_card, new_card)
io.open(c, "w", encoding="utf-8").write(t)
print("Components: playlist card subtitle")
