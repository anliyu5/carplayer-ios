import io
import os

root = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\carplayer-ios"
b = os.path.join(root, "CarPlayer", "BuiltinSources.swift")
t = io.open(b, encoding="utf-8").read()

# 只替换 qqHotPlaylists 整个函数（从函数头到下一个 MARK/函数）
start = t.index("    /// QQ 歌单广场（Android 用的是同一套 fcg 接口）")
end = t.index("    private func get(_ urlString: String, referer: String? = nil) async throws -> Data {")
new = '''    /// QQ 歌单广场（Android 用的是同一套 fcg 接口）
    /// 注意：广场里有部分歌单取不到曲目，这里先并发校验，只保留真能拿到歌的
    private func qqHotPlaylists(limit: Int) async -> [Playlist] {
        let candidates = 30
        let raw = "https://c.y.qq.com/splcloud/fcgi-bin/fcg_get_diss_by_tag.fcg?picmid=1&rnd=0.5&g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&categoryId=10000000&sortId=5&sin=0&ein=\\(max(candidates - 1, 0))"
        guard let data = try? await get(raw, referer: "https://y.qq.com/"),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let dataDict = dict["data"] as? [String: Any],
              let list = dataDict["list"] as? [[String: Any]] else { return [] }

        struct Candidate {
            let id: String
            let name: String
            let cover: String
        }
        let items: [Candidate] = list.compactMap { item in
            guard let dissid = item["dissid"].map({ "\\($0)" }) else { return nil }
            var cover = item["imgurl"] as? String ?? ""
            if cover.hasPrefix("http://") { cover = "https://" + cover.dropFirst("http://".count) }
            return Candidate(id: dissid, name: item["dissname"] as? String ?? "QQ 歌单", cover: cover)
        }
        guard !items.isEmpty else { return [] }

        // 分批并发校验（每批 8 个），凑够 limit 就停
        var result: [Playlist] = []
        var index = 0
        while index < items.count && result.count < limit {
            let batch = Array(items[index..<min(index + 8, items.count)])
            index += batch.count
            let checked = await withTaskGroup(of: Playlist?.self) { group -> [Playlist?] in
                for item in batch {
                    group.addTask {
                        guard let count = await Self.qqSongCount(dissid: item.id), count > 0 else { return nil }
                        return Playlist(id: "tx-\\(item.id)",
                                        name: item.name,
                                        songs: [],
                                        picUrl: item.cover.isEmpty ? nil : item.cover,
                                        source: .tx,
                                        isRemote: true,
                                        trackCount: count)
                    }
                }
                var out: [Playlist?] = []
                for await value in group { out.append(value) }
                return out
            }
            result.append(contentsOf: checked.compactMap { $0 })
        }
        return Array(result.prefix(limit))
    }

    /// 校验 QQ 歌单可读 + 拿到真实曲目数（拿不到返回 nil）
    static func qqSongCount(dissid: String) async -> Int? {
        let raw = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?type=1&json=1&utf8=1&onlysong=0&disstid=\\(dissid)&format=json&g_tk=5381"
        guard let url = URL(string: raw) else { return nil }
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.setValue("https://y.qq.com/", forHTTPHeaderField: "Referer")
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        guard let (data, _) = try? await URLSession.shared.data(for: request),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let cdlist = dict["cdlist"] as? [[String: Any]],
              let cd = cdlist.first,
              let list = cd["songlist"] as? [[String: Any]],
              !list.isEmpty else { return nil }
        return list.count
    }

'''
t = t[:start] + new + t[end:]
io.open(b, "w", encoding="utf-8").write(t)
print("BuiltinSources: qq hot playlists validated; count=", t.count("private func qqHotPlaylists"))
