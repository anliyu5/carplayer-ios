#!/usr/bin/env bash
# 一键出包：在 macOS + Xcode 15/16 上运行，产出未签名 ipa（可用 Sideloadly/AltStore 自签安装）
# 用法：
#   ./scripts/build_ipa.sh              # 未签名 ipa
#   TEAM_ID=ABCDE12345 ./scripts/build_ipa.sh signed   # 用你的开发者账号导出带签名 ipa
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT="CarPlayer.xcodeproj"
SCHEME="CarPlayer"
BUILD_DIR="build"
OUT_DIR="dist"
MODE="${1:-unsigned}"

rm -rf "$BUILD_DIR" "$OUT_DIR"
mkdir -p "$OUT_DIR"

echo "==> xcodebuild -showBuildSettings 校验工程"
xcodebuild -project "$PROJECT" -scheme "$SCHEME" -showBuildSettings >/dev/null

if [[ "$MODE" == "signed" ]]; then
  : "${TEAM_ID:?请设置 TEAM_ID=你的开发者团队ID}"

  echo "==> Archive"
  xcodebuild -project "$PROJECT" -scheme "$SCHEME" \
    -configuration Release \
    -destination "generic/platform=iOS" \
    -archivePath "$BUILD_DIR/CarPlayer.xcarchive" \
    DEVELOPMENT_TEAM="$TEAM_ID" \
    CODE_SIGN_STYLE=Automatic \
    archive

  cat > "$BUILD_DIR/ExportOptions.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key><string>development</string>
  <key>teamID</key><string>${TEAM_ID}</string>
  <key>signingStyle</key><string>automatic</string>
  <key>stripSwiftSymbols</key><true/>
  <key>compileBitcode</key><false/>
</dict>
</plist>
PLIST

  echo "==> Export ipa"
  xcodebuild -exportArchive \
    -archivePath "$BUILD_DIR/CarPlayer.xcarchive" \
    -exportOptionsPlist "$BUILD_DIR/ExportOptions.plist" \
    -exportPath "$OUT_DIR"
else
  echo "==> 未签名构建（仅编译，不做代码签名）"
  xcodebuild -project "$PROJECT" -scheme "$SCHEME" \
    -configuration Release \
    -sdk iphoneos \
    -destination "generic/platform=iOS" \
    -derivedDataPath "$BUILD_DIR/DerivedData" \
    CODE_SIGNING_ALLOWED=NO \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGN_IDENTITY="" \
    build

  APP_PATH="$BUILD_DIR/DerivedData/Build/Products/Release-iphoneos/CarPlayer.app"
  echo "==> 打包 Payload"
  rm -rf "$BUILD_DIR/Payload"
  mkdir -p "$BUILD_DIR/Payload"
  cp -R "$APP_PATH" "$BUILD_DIR/Payload/"
  (cd "$BUILD_DIR" && zip -qry "../$OUT_DIR/CarPlayer-1.9.14-unsigned.ipa" Payload)
  echo "已产出：$OUT_DIR/CarPlayer-1.9.14-unsigned.ipa"
fi

ls -lh "$OUT_DIR"
