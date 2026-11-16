import SwiftUI

// MARK: - item_song（列表歌曲行，64dp）
struct SongRowView: View {
    let song: Song
    var index: Int?
    var showQuality: Bool = true
    var onTap: () -> Void
    var onMore: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            if let index {
                Text("\(index)")
                    .font(FType.chip())
                    .foregroundColor(Palette.textSub)
                    .frame(width: 26)
            }
            CoverImage(url: song.picUrl, size: 44, radius: Radius.cover)
                .padding(.leading, index == nil ? 0 : 4)
            VStack(alignment: .leading, spacing: 3) {
                Text(song.name)
                    .font(FType.rowTitle())
                    .foregroundColor(Palette.text)
                    .lineLimit(1)
                Text(song.displaySinger)
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .lineLimit(1)
            }
            .padding(.leading, 10)
            Spacer(minLength: 8)
            if showQuality, let q = song.bestQuality {
                Text(q.badge)
                    .font(FType.tiny())
                    .foregroundColor(Palette.accent)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Capsule().fill(Palette.surface2))
            }
            Button(action: onMore) {
                VectorIcon(icon: .more, size: 24, color: Palette.textSub)
                    .frame(width: 52, height: 52)
            }
            .buttonStyle(.plain)
        }
        .frame(height: 64)
        .padding(.horizontal, 4)
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
    }
}

// MARK: - item_history（历史行，64dp）
struct HistoryRowView: View {
    let entry: HistoryEntry
    var onTap: () -> Void
    var onMore: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            CoverImage(url: entry.song.picUrl, size: 44, radius: Radius.cover)
                .padding(.leading, 8)
            VStack(alignment: .leading, spacing: 3) {
                Text(entry.song.name)
                    .font(FType.rowTitle())
                    .foregroundColor(Palette.text)
                    .lineLimit(1)
                Text(entry.song.displaySinger)
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .lineLimit(1)
            }
            .padding(.leading, 10)
            Spacer(minLength: 6)
            Text(Fmt.clock(entry.time))
                .font(FType.subSm())
                .foregroundColor(Palette.textSub)
                .padding(.leading, 8)
            Button(action: onMore) {
                VectorIcon(icon: .more, size: 16, color: Palette.textSub)
                    .frame(width: 40, height: 40)
            }
            .buttonStyle(.plain)
        }
        .frame(height: 64)
        .padding(.horizontal, 4)
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
    }
}

// MARK: - item_playlist_row（歌单行，76dp）
struct PlaylistRowView: View {
    let playlist: Playlist
    var onTap: () -> Void
    var onMore: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            CoverImage(url: playlist.picUrl, size: 58, radius: Radius.cover)
            VStack(alignment: .leading, spacing: 3) {
                Text(playlist.name)
                    .font(FType.rowTitle())
                    .foregroundColor(Palette.text)
                    .lineLimit(1)
                Text(playlist.subtitle)
                    .font(FType.sub())
                    .foregroundColor(Palette.textSub)
                    .lineLimit(1)
            }
            .padding(.leading, 14)
            Spacer(minLength: 6)
            Button(action: onMore) {
                VectorIcon(icon: .more, size: 22, color: Palette.textSub)
                    .frame(width: 52, height: 52)
            }
            .buttonStyle(.plain)
        }
        .frame(height: 76)
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
    }
}

// MARK: - item_hot_column（首页小Q/小云热歌行，56dp）
struct HotColumnRowView: View {
    let index: Int
    let song: Song
    var onTap: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            Text("\(index)")
                .font(FType.sub())
                .foregroundColor(Palette.textSub)
                .frame(width: 20)
                .multilineTextAlignment(.center)
            CoverImage(url: song.picUrl, size: 40, radius: 12)
                .padding(.leading, 2)
            VStack(alignment: .leading, spacing: 1) {
                Text(song.name)
                    .font(FType.chip())
                    .foregroundColor(Palette.text)
                    .lineLimit(1)
                Text(song.displaySinger)
                    .font(FType.tiny())
                    .foregroundColor(Palette.textSub)
                    .lineLimit(1)
            }
            .padding(.leading, 8)
            Spacer(minLength: 0)
        }
        .frame(height: 56)
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
    }
}

// MARK: - item_chart（榜单卡片）
struct ChartCardView: View {
    let song: Song
    let rank: Int
    var onTap: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            ZStack(alignment: .bottomTrailing) {
                CoverBanner(url: song.picUrl, radius: Radius.cover)
                    .frame(height: 120)
                    .frame(maxWidth: .infinity)
                Text("\(rank)")
                    .font(FType.subSm().bold())
                    .foregroundColor(Palette.accent)
                    .padding(.horizontal, 9)
                    .padding(.vertical, 2)
                    .background(Capsule().fill(Palette.accentFill))
                    .overlay(Capsule().stroke(Palette.accentStroke, lineWidth: 1))
                    .padding(6)
            }
            .frame(height: 120)
            .clipShape(RoundedRectangle(cornerRadius: Radius.cover, style: .continuous))
            Text(song.name)
                .font(FType.chip())
                .foregroundColor(Palette.text)
                .lineLimit(1)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 7)
                .padding(.horizontal, 10)
            Text(song.displaySinger)
                .font(FType.subSm())
                .foregroundColor(Palette.textSub)
                .lineLimit(1)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 2)
                .padding(.bottom, 9)
                .padding(.horizontal, 10)
        }
        .background(RoundedRectangle(cornerRadius: Radius.card, style: .continuous).fill(Palette.card))
        .padding(.bottom, 6)
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
    }
}

// MARK: - item_playlist_card（横向歌单卡，140dp）
struct PlaylistCardView: View {
    let playlist: Playlist
    var onTap: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ZStack(alignment: .bottomLeading) {
                CoverBanner(url: playlist.picUrl, radius: Radius.cover)
                    .frame(width: 140, height: 140)
                if playlist.isRemote {
                    Text("歌单")
                        .font(FType.badge())
                        .foregroundColor(Palette.accent)
                        .padding(.horizontal, 7)
                        .padding(.vertical, 2)
                        .background(Capsule().fill(Palette.surface2))
                        .padding(6)
                }
            }
            Text(playlist.name)
                .font(FType.body())
                .foregroundColor(Palette.text)
                .lineLimit(1)
                .padding(.top, 8)
            Text(playlist.isRemote
                 ? (playlist.count > 0
                    ? "\(playlist.source.display) · \(playlist.count) 首"
                    : "\(playlist.source.display) 歌单")
                 : "\(playlist.count) 首")
                .font(FType.subSm())
                .foregroundColor(Palette.textSub)
                .lineLimit(1)
                .padding(.top, 2)
        }
        .frame(width: 140, alignment: .leading)
        .padding(.bottom, 6)
        .padding(.trailing, 12)
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
    }
}

// MARK: - 通用组件
struct PillText: View {
    let text: String
    var accent: Bool = false
    var height: CGFloat = 36
    var font: Font = FType.sub()
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(text)
                .font(font)
                .foregroundColor(accent ? Palette.accent : Palette.text)
                .padding(.horizontal, accent ? 16 : 18)
                .frame(height: height)
                .background(
                    Capsule().fill(accent ? Palette.accentFill : Palette.surface2)
                )
                .overlay(Capsule().stroke(accent ? Palette.accentStroke : Color.clear, lineWidth: 1))
        }
        .buttonStyle(.plain)
    }
}

struct SectionTitle: View {
    let text: String
    var font: Font = FType.section()
    var body: some View {
        Text(text)
            .font(font)
            .foregroundColor(Palette.text)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct NavHeader: View {
    let title: String
    var trailing: AnyView?
    var onBack: (() -> Void)?

    var body: some View {
        HStack(spacing: 6) {
            if let onBack {
                Button(action: onBack) {
                    VectorIcon(icon: .back, size: 24, color: Palette.text)
                        .frame(width: 52, height: 52)
                }
                .buttonStyle(.plain)
            }
            Text(title)
                .font(FType.h2())
                .foregroundColor(Palette.text)
                .lineLimit(1)
            Spacer(minLength: 0)
            if let trailing { trailing }
        }
        .frame(height: 64)
        .padding(.leading, onBack == nil ? 24 : 8)
        .padding(.trailing, 16)
    }
}

struct EmptyHint: View {
    let text: String
    var body: some View {
        Text(text)
            .font(FType.chip())
            .foregroundColor(Palette.textSub)
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 30)
    }
}

struct ToastView: View {
    let text: String
    var body: some View {
        Text(text)
            .font(FType.chip())
            .foregroundColor(Palette.text)
            .padding(.horizontal, 18)
            .padding(.vertical, 12)
            .background(Capsule().fill(Palette.sheet))
            .overlay(Capsule().stroke(Palette.stroke, lineWidth: 1))
            .shadow(color: .black.opacity(0.4), radius: 12, y: 4)
    }
}


/// 音质选择（替代 confirmationDialog：iOS 16 上动态内容的 dialog 出现过吞掉点击的问题）
struct QualityPickerSheet: View {
    let title: String
    let options: [Quality]
    let selected: Quality
    var onPick: (Quality) -> Void
    @Environment(\.dismiss) private var dismiss

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
