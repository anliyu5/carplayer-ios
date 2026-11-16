import SwiftUI

// 设计令牌：全部取自 Android 版 resources.arsc / 布局 XML，1:1 复刻，不做风格改造
enum Palette {
    static let bg          = Color(hex: 0x0E0F13)   // color/bg
    static let navBg       = Color(hex: 0x14161B)   // drawable/bg_nav
    static let surface     = Color(hex: 0x1F222B)   // drawable/bg_surface
    static let surface2    = Color(hex: 0x22262F)   // drawable/bg_pill
    static let sheet       = Color(hex: 0x1B1E25)   // drawable/bg_sheet
    static let card        = Color(hex: 0x17191F)   // drawable/bg_card
    static let cover       = Color(hex: 0x262A34)   // drawable/bg_cover
    static let divider     = Color(hex: 0x262933)   // color/divider
    static let stroke      = Color(hex: 0x2A2E38)   // bg_search / bg_sheet 描边
    static let accent      = Color(hex: 0xFFB020)   // color/accent
    static let accentDim   = Color(hex: 0xC98A1E)   // color/accent_dim
    static let text        = Color(hex: 0xF2F4F8)   // color/text
    static let textSub     = Color(hex: 0x9AA0AC)   // color/text_sub
    static let danger      = Color(hex: 0xE5534B)   // color/danger
    static let trackBg     = Color(hex: 0x353947)   // drawable/seekbar 底槽
    static let hairline    = Color.white.opacity(0.13)

    static let accentFill  = Palette.accent.opacity(0.20)  // bg_pill_accent solid #33FFB020
    static let accentStroke = Palette.accent.opacity(0.40) // bg_pill_accent stroke #66FFB020
    static let progressGradient = LinearGradient(
        colors: [Color(hex: 0xFFD25A), Color(hex: 0xFFB020), Color(hex: 0xFF9500)],
        startPoint: .leading, endPoint: .trailing)
    static let coverScrim = LinearGradient(
        colors: [.clear, Color.black.opacity(0.80)],
        startPoint: .top, endPoint: .bottom)
}

// 圆角常量同样来自 drawable：surface 14dp / card 18dp / sheet 24dp / cover 16dp
enum Radius {
    static let surface: CGFloat = 14
    static let card: CGFloat = 18
    static let sheet: CGFloat = 24
    static let cover: CGFloat = 16
    static let bar: CGFloat = 4
    static let pill: CGFloat = 999
}

// 字号沿用布局里的 sp 值（Android 车机通常 1sp≈1pt 于 iOS 渲染，这里直接等价映射）
enum FType {
    static func h1() -> Font { .system(size: 24, weight: .bold) }
    static func h2() -> Font { .system(size: 18, weight: .bold) }
    static func section() -> Font { .system(size: 17, weight: .bold) }
    static func sectionSm() -> Font { .system(size: 16, weight: .bold) }
    static func hotTitle() -> Font { .system(size: 14, weight: .bold) }
    static func rowTitle() -> Font { .system(size: 15) }
    static func body() -> Font { .system(size: 14) }
    static func chip() -> Font { .system(size: 13) }
    static func sub() -> Font { .system(size: 12) }
    static func subSm() -> Font { .system(size: 11) }
    static func tiny() -> Font { .system(size: 10) }
    static func badge() -> Font { .system(size: 9, weight: .bold) }
    static func nav() -> Font { .system(size: 11) }
}

// 复用的背景样式
struct SurfaceCard: ViewModifier {
    var radius: CGFloat = Radius.surface
    var fill: Color = Palette.surface
    func body(content: Content) -> some View {
        content.background(RoundedRectangle(cornerRadius: radius, style: .continuous).fill(fill))
    }
}

struct SheetCard: ViewModifier {
    var radius: CGFloat = Radius.sheet
    func body(content: Content) -> some View {
        content
            .background(RoundedRectangle(cornerRadius: radius, style: .continuous).fill(Palette.sheet))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous).stroke(Palette.stroke, lineWidth: 1))
    }
}

extension View {
    func surfaceCard(_ radius: CGFloat = Radius.surface, fill: Color = Palette.surface) -> some View {
        modifier(SurfaceCard(radius: radius, fill: fill))
    }
    func sheetCard(_ radius: CGFloat = Radius.sheet) -> some View { modifier(SheetCard(radius: radius)) }
}

extension Color {
    init(hex: UInt32, alpha: Double = 1.0) {
        let r = Double((hex >> 16) & 0xFF) / 255
        let g = Double((hex >> 8) & 0xFF) / 255
        let b = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: r, green: g, blue: b, opacity: alpha)
    }
}

// 时间格式：与 Android 侧 HistoryFormat / 列表秒数一致
enum Fmt {
    static func duration(_ seconds: Double) -> String {
        guard seconds.isFinite, seconds > 0 else { return "00:00" }
        let total = Int(seconds.rounded())
        return String(format: "%02d:%02d", total / 60, total % 60)
    }
    static func dayGroup(_ date: Date) -> String {
        let cal = Calendar.current
        if cal.isDateInToday(date) { return "今天" }
        if cal.isDateInYesterday(date) { return "昨天" }
        let df = DateFormatter()
        df.locale = Locale(identifier: "zh_CN")
        df.dateFormat = "M月d日"
        return df.string(from: date)
    }
    static func clock(_ date: Date) -> String {
        let df = DateFormatter()
        df.locale = Locale(identifier: "zh_CN")
        df.dateFormat = "HH:mm"
        return df.string(from: date)
    }
}
