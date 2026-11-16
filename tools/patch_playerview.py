import io, os
p = os.path.join(r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios", "CarPlayer", "PlayerView.swift")
t = io.open(p, encoding="utf-8").read()

# 1) 返回按钮：独立 overlay，64x64 命中区 + 手势兜底
old_bar_start = t.index("    private var topBar: some View {")
old_bar_end = t.index("    private func cover(_ song: Song) -> some View {")
new_bar = '''    /// 关闭播放页（多种触发方式共用，避免某个手势被别的视图吃掉）
    private func closePlayer() {
        router.screen = .main
    }

    private var topBar: some View {
        HStack(spacing: 6) {
            Button(action: closePlayer) {
                VectorIcon(icon: .back, size: 24, color: Palette.text)
                    .frame(width: 64, height: 60)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.borderless)

            Text("正在播放")
                .font(FType.body().bold())
                .foregroundColor(Palette.text)
            Spacer(minLength: 0)
            Text(player.mode.display)
                .font(FType.chip())
                .foregroundColor(Palette.accent)
                .padding(.horizontal, 12)
                .frame(height: 30)
                .background(Capsule().fill(Palette.accentFill))
                .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
                .onTapGesture { player.cycleMode() }
            Button {
                showQueue = true
            } label: {
                VectorIcon(icon: .library, size: 22, color: Palette.text)
                    .frame(width: 52, height: 60)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("播放列表")
        }
        .frame(height: 60)
        .padding(.leading, 4)
        .padding(.trailing, 12)
        .background(Palette.bg)
        .zIndex(2)
    }

'''
t = t[:old_bar_start] + new_bar + t[old_bar_end:]

# 2) body：加手势兜底 + 状态行
t = t.replace('''        .background(Palette.bg.ignoresSafeArea())
        .sheet(isPresented: $showQueue) {''',
'''        .background(Palette.bg.ignoresSafeArea())
        .overlay(alignment: .topLeading) {
            // 兜底返回区：即使顶部栏被别的手势吃掉也能退
            Color.clear
                .frame(width: 72, height: 72)
                .contentShape(Rectangle())
                .onTapGesture { closePlayer() }
        }
        .gesture(
            DragGesture(minimumDistance: 30)
                .onEnded { value in
                    if value.translation.height > 60 || value.translation.width > 80 { closePlayer() }
                }
        )
        .sheet(isPresented: $showQueue) {''')

# 3) 标题下方显示解析状态 / 失败原因
t = t.replace('''            Text("\\(song.displaySinger) · \\(song.displayAlbum)")
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .lineLimit(1)
        }
        .padding(.top, 16)''',
'''            Text("\\(song.displaySinger) · \\(song.displayAlbum)")
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .lineLimit(1)
            if player.isResolving {
                HStack(spacing: 6) {
                    ProgressView().scaleEffect(0.7).tint(Palette.accent)
                    Text(player.status)
                        .font(FType.subSm())
                        .foregroundColor(Palette.accent)
                }
                .padding(.top, 2)
            } else if let error = player.errorText {
                Text(error)
                    .font(FType.subSm())
                    .foregroundColor(Palette.danger)
                    .multilineTextAlignment(.center)
                    .padding(.top, 2)
            }
        }
        .padding(.top, 16)''')

io.open(p, "w", encoding="utf-8").write(t)
print("PlayerView patched:", len(t), "chars")
for k in ["closePlayer", "contentShape(Rectangle())", "isResolving"]:
    print("  ", k, "->", k in t)
