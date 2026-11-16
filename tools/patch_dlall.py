import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "DownloadView.swift")
t = io.open(p, encoding="utf-8").read()
old = """            content
        }"""
new = """            content

            if isManaging && !store.downloads.isEmpty {
                Button {
                    deleteAll()
                } label: {
                    Text("删除全部已下载（\\(store.downloads.count) 首）")
                        .font(FType.chip())
                        .foregroundColor(Palette.danger)
                        .frame(maxWidth: .infinity)
                        .frame(height: 46)
                        .background(Capsule().fill(Palette.surface2))
                }
                .buttonStyle(.borderless)
                .padding(.horizontal, 20)
                .padding(.bottom, 12)
                .padding(.top, 6)
            }
        }"""
assert old in t
t = t.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(t)
print("DownloadView: delete-all button")
