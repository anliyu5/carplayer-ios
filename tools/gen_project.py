#!/usr/bin/env python3
"""生成可直接用 Xcode 打开的 CarPlayer.xcodeproj（不依赖 xcodegen / tuist）。"""
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_NAME = "CarPlayer"
SRC_DIR = os.path.join(ROOT, PROJECT_NAME)


def uid(key: str) -> str:
    return hashlib.md5(key.encode()).hexdigest()[:24].upper()


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


swift_files = []
resource_files = []
for dirpath, _dirnames, filenames in os.walk(SRC_DIR):
    for name in sorted(filenames):
        full = os.path.join(dirpath, name)
        r = rel(full)
        if name.endswith(".swift"):
            swift_files.append(r)
        elif name.endswith(".js") or name.endswith(".json") and "Assets" not in r:
            resource_files.append(r)

swift_files.sort()
resource_files.sort()

assets_rel = rel(os.path.join(SRC_DIR, "Assets.xcassets"))
plist_rel = rel(os.path.join(SRC_DIR, "Info.plist"))

lines = []
add = lines.append

add("// !$*UTF8*$!")
add("{")
add("\tarchiveVersion = 1;")
add("\tclasses = {")
add("\t};")
add("\tobjectVersion = 56;")
add("\tobjects = {")
add("")

# PBXBuildFile
add("/* Begin PBXBuildFile section */")
for f in swift_files:
    add(f"\t\t{uid('bf:' + f)} /* {os.path.basename(f)} in Sources */ = {{isa = PBXBuildFile; fileRef = {uid('fr:' + f)} /* {os.path.basename(f)} */; }};")
for f in resource_files:
    add(f"\t\t{uid('bf:' + f)} /* {os.path.basename(f)} in Resources */ = {{isa = PBXBuildFile; fileRef = {uid('fr:' + f)} /* {os.path.basename(f)} */; }};")
add(f"\t\t{uid('bf:assets')} /* Assets.xcassets in Resources */ = {{isa = PBXBuildFile; fileRef = {uid('fr:assets')} /* Assets.xcassets */; }};")
add("/* End PBXBuildFile section */")
add("")

# PBXFileReference
add("/* Begin PBXFileReference section */")
add(f"\t\t{uid('fr:app')} /* {PROJECT_NAME}.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = {PROJECT_NAME}.app; sourceTree = BUILT_PRODUCTS_DIR; }};")
for f in swift_files:
    add(f"\t\t{uid('fr:' + f)} /* {os.path.basename(f)} */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = {os.path.basename(f)}; sourceTree = \"<group>\"; }};")
for f in resource_files:
    add(f"\t\t{uid('fr:' + f)} /* {os.path.basename(f)} */ = {{isa = PBXFileReference; lastKnownFileType = text; path = {os.path.basename(f)}; sourceTree = \"<group>\"; }};")
add(f"\t\t{uid('fr:assets')} /* Assets.xcassets */ = {{isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Assets.xcassets; sourceTree = \"<group>\"; }};")
add(f"\t\t{uid('fr:plist')} /* Info.plist */ = {{isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = \"<group>\"; }};")
add("/* End PBXFileReference section */")
add("")

# Frameworks phase (empty, 系统框架由 import 自动链接)
add("/* Begin PBXFrameworksBuildPhase section */")
add(f"\t\t{uid('phase:frameworks')} /* Frameworks */ = {{")
add("\t\t\tisa = PBXFrameworksBuildPhase;")
add("\t\t\tbuildActionMask = 2147483647;")
add("\t\t\tfiles = (")
add("\t\t\t);")
add("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
add("\t\t};")
add("/* End PBXFrameworksBuildPhase section */")
add("")

# Groups
add("/* Begin PBXGroup section */")
add(f"\t\t{uid('group:root')} = {{")
add("\t\t\tisa = PBXGroup;")
add("\t\t\tchildren = (")
add(f"\t\t\t\t{uid('group:src')} /* {PROJECT_NAME} */,")
add(f"\t\t\t\t{uid('group:products')} /* Products */,")
add("\t\t\t);")
add("\t\t\tsourceTree = \"<group>\";")
add("\t\t};")
add(f"\t\t{uid('group:products')} /* Products */ = {{")
add("\t\t\tisa = PBXGroup;")
add("\t\t\tchildren = (")
add(f"\t\t\t\t{uid('fr:app')} /* {PROJECT_NAME}.app */,")
add("\t\t\t);")
add("\t\t\tname = Products;")
add("\t\t\tsourceTree = \"<group>\";")
add("\t\t};")
add(f"\t\t{uid('group:src')} /* {PROJECT_NAME} */ = {{")
add("\t\t\tisa = PBXGroup;")
add("\t\t\tchildren = (")
for f in swift_files:
    add(f"\t\t\t\t{uid('fr:' + f)} /* {os.path.basename(f)} */,")
add(f"\t\t\t\t{uid('group:resources')} /* Resources */,")
add(f"\t\t\t\t{uid('fr:assets')} /* Assets.xcassets */,")
add(f"\t\t\t\t{uid('fr:plist')} /* Info.plist */,")
add("\t\t\t);")
add(f"\t\t\tpath = {PROJECT_NAME};")
add("\t\t\tsourceTree = \"<group>\";")
add("\t\t};")
add(f"\t\t{uid('group:resources')} /* Resources */ = {{")
add("\t\t\tisa = PBXGroup;")
add("\t\t\tchildren = (")
for f in resource_files:
    add(f"\t\t\t\t{uid('fr:' + f)} /* {os.path.basename(f)} */,")
add("\t\t\t);")
add("\t\t\tpath = Resources;")
add("\t\t\tsourceTree = \"<group>\";")
add("\t\t};")
add("/* End PBXGroup section */")
add("")

# Target
add("/* Begin PBXNativeTarget section */")
add(f"\t\t{uid('target')} /* {PROJECT_NAME} */ = {{")
add("\t\t\tisa = PBXNativeTarget;")
add(f"\t\t\tbuildConfigurationList = {uid('cfglist:target')} /* Build configuration list for PBXNativeTarget \"{PROJECT_NAME}\" */;")
add("\t\t\tbuildPhases = (")
add(f"\t\t\t\t{uid('phase:sources')} /* Sources */,")
add(f"\t\t\t\t{uid('phase:frameworks')} /* Frameworks */,")
add(f"\t\t\t\t{uid('phase:resources')} /* Resources */,")
add("\t\t\t);")
add("\t\t\tbuildRules = (")
add("\t\t\t);")
add("\t\t\tdependencies = (")
add("\t\t\t);")
add(f"\t\t\tname = {PROJECT_NAME};")
add(f"\t\t\tproductName = {PROJECT_NAME};")
add(f"\t\t\tproductReference = {uid('fr:app')} /* {PROJECT_NAME}.app */;")
add("\t\t\tproductType = \"com.apple.product-type.application\";")
add("\t\t};")
add("/* End PBXNativeTarget section */")
add("")

# Project
add("/* Begin PBXProject section */")
add(f"\t\t{uid('project')} /* Project object */ = {{")
add("\t\t\tisa = PBXProject;")
add("\t\t\tattributes = {")
add("\t\t\t\tBuildIndependentTargetsInParallel = 1;")
add("\t\t\t\tLastSwiftUpdateCheck = 1500;")
add("\t\t\t\tLastUpgradeCheck = 1500;")
add("\t\t\t\tTargetAttributes = {")
add(f"\t\t\t\t\t{uid('target')} = {{")
add("\t\t\t\t\t\tCreatedOnToolsVersion = 15.0;")
add("\t\t\t\t\t};")
add("\t\t\t\t};")
add("\t\t\t};")
add(f"\t\t\tbuildConfigurationList = {uid('cfglist:project')} /* Build configuration list for PBXProject \"{PROJECT_NAME}\" */;")
add("\t\t\tcompatibilityVersion = \"Xcode 14.0\";")
add("\t\t\tdevelopmentRegion = zh_CN;")
add("\t\t\thasScannedForEncodings = 0;")
add("\t\t\tknownRegions = (")
add("\t\t\t\tzh_CN,")
add("\t\t\t\ten,")
add("\t\t\t\tBase,")
add("\t\t\t);")
add(f"\t\t\tmainGroup = {uid('group:root')};")
add(f"\t\t\tproductRefGroup = {uid('group:products')} /* Products */;")
add("\t\t\tprojectDirPath = \"\";")
add("\t\t\tprojectRoot = \"\";")
add("\t\t\ttargets = (")
add(f"\t\t\t\t{uid('target')} /* {PROJECT_NAME} */,")
add("\t\t\t);")
add("\t\t};")
add("/* End PBXProject section */")
add("")

# Resources phase
add("/* Begin PBXResourcesBuildPhase section */")
add(f"\t\t{uid('phase:resources')} /* Resources */ = {{")
add("\t\t\tisa = PBXResourcesBuildPhase;")
add("\t\t\tbuildActionMask = 2147483647;")
add("\t\t\tfiles = (")
for f in resource_files:
    add(f"\t\t\t\t{uid('bf:' + f)} /* {os.path.basename(f)} in Resources */,")
add(f"\t\t\t\t{uid('bf:assets')} /* Assets.xcassets in Resources */,")
add("\t\t\t);")
add("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
add("\t\t};")
add("/* End PBXResourcesBuildPhase section */")
add("")

# Sources phase
add("/* Begin PBXSourcesBuildPhase section */")
add(f"\t\t{uid('phase:sources')} /* Sources */ = {{")
add("\t\t\tisa = PBXSourcesBuildPhase;")
add("\t\t\tbuildActionMask = 2147483647;")
add("\t\t\tfiles = (")
for f in swift_files:
    add(f"\t\t\t\t{uid('bf:' + f)} /* {os.path.basename(f)} in Sources */,")
add("\t\t\t);")
add("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
add("\t\t};")
add("/* End PBXSourcesBuildPhase section */")
add("")

COMMON = [
    ("ALWAYS_SEARCH_USER_PATHS", "NO"),
    ("CLANG_ANALYZER_NONNULL", "YES"),
    ("CLANG_ENABLE_MODULES", "YES"),
    ("CLANG_ENABLE_OBJC_ARC", "YES"),
    ("COPY_PHASE_STRIP", "NO"),
    ("ENABLE_STRICT_OBJC_MSGSEND", "YES"),
    ("GCC_C_LANGUAGE_STANDARD", "gnu11"),
    ("IPHONEOS_DEPLOYMENT_TARGET", "16.0"),
    ("SDKROOT", "iphoneos"),
    ("SWIFT_VERSION", "5.0"),
    ("TARGETED_DEVICE_FAMILY", "\"1,2\""),
]

PROJECT_DEBUG = COMMON + [
    ("DEBUG_INFORMATION_FORMAT", "dwarf"),
    ("ENABLE_TESTABILITY", "YES"),
    ("GCC_OPTIMIZATION_LEVEL", "0"),
    ("GCC_PREPROCESSOR_DEFINITIONS", "(\n\t\t\t\t\t\"DEBUG=1\",\n\t\t\t\t\t\"$(inherited)\",\n\t\t\t\t)"),
    ("MTL_ENABLE_DEBUG_INFO", "INCLUDE_SOURCE"),
    ("ONLY_ACTIVE_ARCH", "YES"),
    ("SWIFT_ACTIVE_COMPILATION_CONDITIONS", "DEBUG"),
    ("SWIFT_OPTIMIZATION_LEVEL", "\"-Onone\""),
]

PROJECT_RELEASE = COMMON + [
    ("DEBUG_INFORMATION_FORMAT", "\"dwarf-with-dsym\""),
    ("ENABLE_NS_ASSERTIONS", "NO"),
    ("MTL_ENABLE_DEBUG_INFO", "NO"),
    ("SWIFT_COMPILATION_MODE", "wholemodule"),
    ("SWIFT_OPTIMIZATION_LEVEL", "\"-O\""),
    ("VALIDATE_PRODUCT", "YES"),
]

TARGET_COMMON = [
    ("ASSETCATALOG_COMPILER_APPICON_NAME", "AppIcon"),
    ("CODE_SIGN_STYLE", "Automatic"),
    ("CURRENT_PROJECT_VERSION", "27"),
    ("ENABLE_PREVIEWS", "YES"),
    ("GENERATE_INFOPLIST_FILE", "NO"),
    ("INFOPLIST_FILE", plist_rel),
    ("LD_RUNPATH_SEARCH_PATHS", "(\n\t\t\t\t\t\"$(inherited)\",\n\t\t\t\t\t\"@executable_path/Frameworks\",\n\t\t\t\t)"),
    ("MARKETING_VERSION", "1.9.14"),
    ("PRODUCT_BUNDLE_IDENTIFIER", "com.carplayer.music"),
    ("PRODUCT_NAME", "\"$(TARGET_NAME)\""),
    ("SWIFT_EMIT_LOC_STRINGS", "YES"),
    ("SWIFT_VERSION", "5.0"),
    ("TARGETED_DEVICE_FAMILY", "\"1,2\""),
]

add("/* Begin XCBuildConfiguration section */")
for scope, settings, name in [
    ("project", PROJECT_DEBUG, "Debug"),
    ("project", PROJECT_RELEASE, "Release"),
    ("target", TARGET_COMMON, "Debug"),
    ("target", TARGET_COMMON, "Release"),
]:
    add(f"\t\t{uid(f'cfg:{scope}:{name}')} /* {name} */ = {{")
    add("\t\t\tisa = XCBuildConfiguration;")
    add("\t\t\tbuildSettings = {")
    for key, value in settings:
        add(f"\t\t\t\t{key} = {value};")
    add("\t\t\t};")
    add(f"\t\t\tname = {name};")
    add("\t\t};")
add("/* End XCBuildConfiguration section */")
add("")

add("/* Begin XCConfigurationList section */")
for scope, label in [("project", f"PBXProject \"{PROJECT_NAME}\""), ("target", f"PBXNativeTarget \"{PROJECT_NAME}\"")]:
    add(f"\t\t{uid('cfglist:' + scope)} /* Build configuration list for {label} */ = {{")
    add("\t\t\tisa = XCConfigurationList;")
    add("\t\t\tbuildConfigurations = (")
    add(f"\t\t\t\t{uid(f'cfg:{scope}:Debug')} /* Debug */,")
    add(f"\t\t\t\t{uid(f'cfg:{scope}:Release')} /* Release */,")
    add("\t\t\t);")
    add("\t\t\tdefaultConfigurationIsVisible = 0;")
    add("\t\t\tdefaultConfigurationName = Release;")
    add("\t\t};")
add("/* End XCConfigurationList section */")
add("")
add("\t};")
add(f"\trootObject = {uid('project')} /* Project object */;")
add("}")

out_dir = os.path.join(ROOT, f"{PROJECT_NAME}.xcodeproj")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "project.pbxproj"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")

print(f"wrote {out_dir}/project.pbxproj")
print(f"sources: {len(swift_files)}  resources: {len(resource_files)}")
