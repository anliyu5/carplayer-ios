import io, os
root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"

# 1) Components.swift 追加通用音质选择 sheet
c = os.path.join(root, "CarPlayer", "Components.swift")
t = io.open(c, encoding="utf-8").read()
if "struct QualityPickerSheet" not in t:
    t += '''
/// 音质选择（替代 confirmationDialog：iOS 16 上动态内容的 dialog 出现过吞掉点击的问题）
struct QualityPickerSheet: View {
    let title: String
    let options: [Quality]
    let selected: Quality
    var onPick: (Quality) -> Void
    @Environment(\\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            Capsule().fill(Palette.divider).frame(width: 36, height: 4).padding(.top, 10)
            Text(title)
                .font(FType.sectionSm())
                .foregroundColor(Palette.text)
                .padding(.top, 14)
                .padding(.bottom, 10)
            ForEach(options) { quality in
                Button {
                    onPick(quality)
                    dismiss()
                } label: {
                    HStack {
                        Text(quality.display)
                            .font(FType.rowTitle())
                            .foregroundColor(quality == selected ? Palette.accent : Palette.text)
                        Spacer()
                        if quality == selected {
                            VectorIcon(icon: .check, size: 18, color: Palette.accent)
                        }
                    }
                    .padding(.horizontal, 20)
                    .frame(height: 50)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }
            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Palette.sheet.ignoresSafeArea())
    }
}
'''
    io.open(c, "w", encoding="utf-8").write(t)
    print("Components + QualityPickerSheet")

# 2) PlayerView：confirmationDialog -> sheet
p = os.path.join(root, "CarPlayer", "PlayerView.swift")
v = io.open(p, encoding="utf-8").read()
start = v.index("        .confirmationDialog(\"音质\"")
end = v.index("    }\n\n    /// 关闭播放页")
v = v[:start] + '''        .sheet(isPresented: $showQuality) {
            QualityPickerSheet(title: "音质",
                               options: song?.qualitys ?? [.k320],
                               selected: store.settings.playQuality) { quality in
                store.settings.playQuality = quality
                store.persistAll()
                store.show("音质已设为 \\(quality.display)")
            }
            .presentationDetents([.height(CGFloat(120 + (song?.qualitys.count ?? 1) * 50))])
        }
''' + v[end:]
io.open(p, "w", encoding="utf-8").write(v)
print("PlayerView dialog -> sheet")

# 3) DownloadView / SettingsView 同样替换
for name, title in [("DownloadView.swift", "下载音质"), ("SettingsView.swift", "下载音质")]:
    f = os.path.join(root, "CarPlayer", name)
    s = io.open(f, encoding="utf-8").read()
    if ".confirmationDialog" not in s:
        continue
    st = s.index("        .confirmationDialog(")
    en = s.index("\n        }\n", st) + len("\n        }\n")
    s = s[:st] + '''        .sheet(isPresented: $showQuality) {
            QualityPickerSheet(title: "%s",
                               options: Quality.downloadOptions,
                               selected: store.settings.downloadQuality) { quality in
                store.settings.downloadQuality = quality
                store.persistAll()
            }
            .presentationDetents([.height(CGFloat(120 + Quality.downloadOptions.count * 50))])
        }
''' % title + s[en:]
    io.open(f, "w", encoding="utf-8").write(s)
    print(name, "dialog -> sheet")
