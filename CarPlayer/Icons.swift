import SwiftUI

// Android 侧全部是 vector drawable（Material Icons 路径），这里直接复用 pathData，
// 保证图标形状、视觉重量与 Android 版完全一致，不用 SF Symbols 近似替代。
enum Icon: String {
    case home, library, search, settings, play, pause, prev, next
    case repeatAll = "repeat", repeatOne, shuffle, heart, link, close, back
    case delete, check, note, more, download, chevron, plus, history, clock, arrowBack

    var path: String {
        switch self {
        case .home:      return "M10,20v-6h4v6h5v-8h3L12,3 2,12h3v8z"
        case .library:   return "M4,6H2v14c0,1.1 0.9,2 2,2h14v-2H4V6zM20,2H8c-1.1,0 -2,0.9 -2,2v12c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V4c0,-1.1 -0.9,-2 -2,-2zM19,11H9V9h10v2zM15,15H9v-2h6v2zM19,7H9V5h10v2z"
        case .search:    return "M15.5,14h-0.79l-0.28,-0.27C15.41,12.59 16,11.11 16,9.5 16,5.91 13.09,3 9.5,3S3,5.91 3,9.5 5.91,16 9.5,16c1.61,0 3.09,-0.59 4.23,-1.57l0.27,0.28v0.79l5,4.99L20.49,19l-4.99,-5zM9.5,14C7.01,14 5,11.99 5,9.5S7.01,5 9.5,5 14,7.01 14,9.5 11.99,14 9.5,14z"
        case .settings:  return "M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"
        case .play:      return "M8,5v14l11,-7z"
        case .pause:     return "M6,19h4V5H6v14zM14,5v14h4V5h-4z"
        case .prev:      return "M6,6h2v12H6zM9.5,12l8.5,6V6z"
        case .next:      return "M6,18l8.5,-6L6,6zM16,6h2v12h-2z"
        case .repeatAll: return "M7,7h10v3l4,-4 -4,-4v3H5v6h2V7zM17,17H7v-3l-4,4 4,4v-3h12v-6h-2v4z"
        case .repeatOne: return "M7,7h10v3l4,-4 -4,-4v3H5v6h2V7zM17,17H7v-3l-4,4 4,4v-3h12v-6h-2v4zM13,15V9h-1l-2,1v1h1.5v4H13z"
        case .shuffle:   return "M10.59,9.17L5.41,4 4,5.41l5.17,5.17 1.42,-1.41zM14.5,4l2.04,2.04L4,18.59 5.41,20 17.96,7.46 20,9.5V4h-5.5zM14.83,13.41l-1.41,1.41 3.13,3.13L14.5,20H20v-5.5l-2.04,2.04 -3.13,-3.13z"
        case .heart:     return "M12,21.35l-1.45,-1.32C5.4,15.36 2,12.28 2,8.5 2,5.42 4.42,3 7.5,3c1.74,0 3.41,0.81 4.5,2.09C13.09,3.81 14.76,3 16.5,3 19.58,3 22,5.42 22,8.5c0,3.78 -3.4,6.86 -8.55,11.54L12,21.35z"
        case .link:      return "M3.9,12c0,-1.71 1.39,-3.1 3.1,-3.1h4V7H7c-2.76,0 -5,2.24 -5,5s2.24,5 5,5h4v-1.9H7c-1.71,0 -3.1,-1.39 -3.1,-3.1zM8,13h8v-2H8v2zM17,7h-4v1.9h4c1.71,0 3.1,1.39 3.1,3.1s-1.39,3.1 -3.1,3.1h-4V17h4c2.76,0 5,-2.24 5,-5s-2.24,-5 -5,-5z"
        case .close:     return "M19,6.41L17.59,5 12,10.59 6.41,5 5,6.41 10.59,12 5,17.59 6.41,19 12,13.41 17.59,19 19,17.59 13.41,12z"
        case .back:      return "M20,11H7.83l5.59,-5.59L12,4l-8,8 8,8 1.41,-1.41L7.83,13H20v-2z"
        case .arrowBack: return "M20,11H7.83l5.59,-5.59L12,4l-8,8 8,8 1.41,-1.41L7.83,13H20v-2z"
        case .delete:    return "M6,19c0,1.1 0.9,2 2,2h8c1.1,0 2,-0.9 2,-2V7H6v12zM19,4h-3.5l-1,-1h-5l-1,1H5v2h14V4z"
        case .check:     return "M9,16.17L4.83,12l-1.42,1.41L9,19 21,7l-1.41,-1.41z"
        case .note:      return "M12,3v10.55C11.41,13.21 10.72,13 10,13c-1.66,0 -3,1.34 -3,3s1.34,3 3,3 3,-1.34 3,-3V7h4V3h-5z"
        case .more:      return "M12,8c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM12,10c-1.1,0 -2,0.9 -2,2s0.9,2 2,2 2,-0.9 2,-2 -0.9,-2 -2,-2zM12,16c-1.1,0 -2,0.9 -2,2s0.9,2 2,2 2,-0.9 2,-2 -0.9,-2 -2,-2z"
        case .download:  return "M19,9h-4V3H9v6H5l7,7 7,-7zM5,18v2h14v-2H5z"
        case .chevron:   return "M8.59,16.59L13.17,12 8.59,7.41 10,6l6,6 -6,6z"
        case .plus:      return "M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"
        case .history:   return "M13,3c-4.97,0 -9,4.03 -9,9H1l3.89,3.89 0.07,0.14L9,12H6c0,-3.87 3.13,-7 7,-7s7,3.13 7,7 -3.13,7 -7,7c-1.93,0 -3.68,-0.79 -4.94,-2.06l-1.42,1.42C8.27,19.99 10.51,21 13,21c4.97,0 9,-4.03 9,-9s-4.03,-9 -9,-9zM12,8v5l4.28,2.54 0.72,-1.21 -3.5,-2.08V8H12z"
        case .clock:     return "M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM12,20c-4.41,0 -8,-3.59 -8,-8s3.59,-8 8,-8 8,3.59 8,8 -3.59,8 -8,8zM12.5,7H11v6l5.25,3.15 0.75,-1.23 -4.5,-2.67z"
        }
    }

    var viewport: CGSize { CGSize(width: 24, height: 24) }
}

struct VectorIcon: View {
    let icon: Icon
    var size: CGFloat = 24
    var color: Color = Palette.text

    var body: some View {
        SVGPathShape(pathData: icon.path, viewport: icon.viewport)
            .fill(color)
            .frame(width: size, height: size)
    }
}

/// 极简 SVG pathData 解析器（Material Icons 只用 M/L/H/V/C/S/Q/T/A/Z 及其相对形式）
struct SVGPathShape: Shape {
    let pathData: String
    let viewport: CGSize

    func path(in rect: CGRect) -> Path {
        var path = Path()
        let sx = rect.width / viewport.width
        let sy = rect.height / viewport.height
        let scale = CGAffineTransform(scaleX: sx, y: sy)
        let tokens = SVGPathShape.tokenize(pathData)
        var current = CGPoint.zero
        var start = CGPoint.zero
        var lastControl: CGPoint? = nil
        var command: Character = "M"
        var i = 0
        func num() -> CGFloat {
            guard i < tokens.count else { return 0 }
            if case let .number(v) = tokens[i] { i += 1; return v }
            return 0
        }
        func point(_ absolute: Bool, _ x: CGFloat, _ y: CGFloat) -> CGPoint {
            absolute ? CGPoint(x: x, y: y) : CGPoint(x: current.x + x, y: current.y + y)
        }
        while i < tokens.count {
            if let c = tokens.command(at: i) {
                command = c
                i += 1
            }
            let absolute = command.isUppercase
            switch command.uppercased() {
            case "M":
                let p = point(absolute, num(), num())
                path.move(to: p.applying(scale))
                current = p; start = p; lastControl = nil
            case "L":
                let p = point(absolute, num(), num())
                path.addLine(to: p.applying(scale))
                current = p; lastControl = nil
            case "H":
                let x = num(); let p = CGPoint(x: absolute ? x : current.x + x, y: current.y)
                path.addLine(to: p.applying(scale)); current = p; lastControl = nil
            case "V":
                let y = num(); let p = CGPoint(x: current.x, y: absolute ? y : current.y + y)
                path.addLine(to: p.applying(scale)); current = p; lastControl = nil
            case "C":
                let c1 = point(absolute, num(), num())
                let c2 = point(absolute, num(), num())
                let p  = point(absolute, num(), num())
                path.addCurve(to: p.applying(scale), control1: c1.applying(scale), control2: c2.applying(scale))
                current = p; lastControl = c2
            case "S":
                let c2 = point(absolute, num(), num())
                let p  = point(absolute, num(), num())
                let c1 = lastControl.map { CGPoint(x: 2 * current.x - $0.x, y: 2 * current.y - $0.y) } ?? current
                path.addCurve(to: p.applying(scale), control1: c1.applying(scale), control2: c2.applying(scale))
                current = p; lastControl = c2
            case "Q":
                let c = point(absolute, num(), num())
                let p = point(absolute, num(), num())
                path.addQuadCurve(to: p.applying(scale), control: c.applying(scale))
                current = p; lastControl = c
            case "T":
                let p = point(absolute, num(), num())
                let c = lastControl.map { CGPoint(x: 2 * current.x - $0.x, y: 2 * current.y - $0.y) } ?? current
                path.addQuadCurve(to: p.applying(scale), control: c.applying(scale))
                current = p; lastControl = c
            case "A":
                _ = num()   // rx
                _ = num()   // ry
                _ = num()   // rotation
                _ = num()   // large-arc
                _ = num()   // sweep
                let p = point(absolute, num(), num())
                path.addLine(to: p.applying(scale))   // 简化处理：仅 ic_speed 使用，不影响主界面
                current = p; lastControl = nil
            case "Z":
                path.closeSubpath()
                current = start; lastControl = nil
            default:
                i += 1
            }
        }
        return path
    }

    // 把 "M12,3v10.55c..." 拆成命令字符与数值序列
    static func tokenize(_ s: String) -> [Token] {
        var out: [Token] = []
        var numBuf = ""
        func flush() {
            if let d = Double(numBuf) { out.append(.number(CGFloat(d))) }
            numBuf = ""
        }
        for ch in s {
            if ch.isNumber || ch == "." || ch == "-" || ch == "+" {
                if ch == "-" && !numBuf.isEmpty { flush() }
                numBuf.append(ch)
            } else if ch == "e" || ch == "E" {
                numBuf.append(ch)
            } else if ch.isLetter {
                flush()
                // 关键：保留大小写！小写 = 相对坐标，大写 = 绝对坐标。
                // 之前这里 upperсased() 把 c/l/s/q/t/h/v 全变成绝对命令，图标才会糊成一团乱码。
                out.append(.command(ch))
            } else {
                flush()
            }
        }
        flush()
        return out
    }

    enum Token {
        case command(Character)
        case number(CGFloat)
    }
}

extension Array where Element == SVGPathShape.Token {
    func command(at index: Int) -> Character? {
        guard index < count else { return nil }
        if case let .command(c) = self[index] { return c }
        return nil
    }
}
