import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "SettingsView.swift")
t = io.open(p, encoding="utf-8").read()

# 青听卡片：显示配置名/版本 + 每条线路（名称 · id · 等级）+ 启用开关
old_start = t.index('            if let qing = store.qing {')
old_end = t.index('            ForEach(scriptedSources) { meta in')
new_block = '''            if let qing = store.qing {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(alignment: .top, spacing: 12) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("\\(qing.title) \\(qing.version)")
                                .font(FType.body())
                                .foregroundColor(Palette.text)
                            Text("\\(qing.lines.count) 条线路 · 网关 \\(qing.gatewayBase)")
                                .font(FType.subSm())
                                .foregroundColor(Palette.textSub)
                                .lineLimit(1)
                        }
                        Spacer(minLength: 0)
                        Button {
                            store.clearQing()
                        } label: {
                            Text("清除")
                                .font(FType.subSm())
                                .foregroundColor(Palette.danger)
                                .padding(.horizontal, 12)
                                .frame(height: 30)
                                .background(Capsule().fill(Palette.surface2))
                        }
                        .buttonStyle(.plain)
                    }

                    ForEach(qing.lines) { line in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(line.enabled ? Palette.accent : Palette.textSub.opacity(0.4))
                                .frame(width: 6, height: 6)
                            Text(line.name)
                                .font(FType.sub())
                                .foregroundColor(line.enabled ? Palette.text : Palette.textSub)
                            Text(line.id)
                                .font(FType.tiny())
                                .foregroundColor(Palette.textSub)
                            Spacer(minLength: 6)
                            Text(line.levelsText)
                                .font(FType.tiny())
                                .foregroundColor(Palette.textSub)
                                .lineLimit(1)
                            Toggle("", isOn: Binding(
                                get: { line.enabled },
                                set: { _ in store.toggleQingLine(line.id) }))
                            .labelsHidden()
                            .tint(Palette.accent)
                        }
                        .padding(.horizontal, 10)
                        .frame(height: 38)
                        .background(RoundedRectangle(cornerRadius: 10, style: .continuous).fill(Palette.surface2))
                    }
                }
                .padding(14)
                .surfaceCard()
            }

'''
t = t[:old_start] + new_block + t[old_end:]

# 摘要文案：带上配置标题
t = t.replace('if let qing = store.qing { return "青听 · \\(qing.lines.count) 条线路" }',
              'if let qing = store.qing { return "青听 · \\(qing.title) · \\(qing.lines.count) 条线路" }')

io.open(p, "w", encoding="utf-8").write(t)
print("SettingsView patched:", len(t), "chars")
print("  linesText:", "line.levelsText" in t, "| toggleQingLine:", "store.toggleQingLine" in t)
