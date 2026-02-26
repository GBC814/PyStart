#!/bin/bash
# 用于构建 PyStart .pkg 软件包的脚本（macOS）

set -e

PKG_NAME="PyStart"
VERSION="1.0.0"
IDENTIFIER="com.pystart.app"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 从 MacOS/packaging/macos 回到项目根目录（需要向上3级）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build_pkg"
DIST_DIR="$PROJECT_ROOT/dist"
PKG_FILE="$DIST_DIR/${PKG_NAME}_v${VERSION}_x64.pkg"
COMPONENT_PKG="$BUILD_DIR/component.pkg"

cd "$PROJECT_ROOT"

if [ ! -d "dist/app" ]; then
    echo "错误: 请先运行 ./packaging/macos/build_nuitka_macos.sh 进行 Nuitka 打包！"
    exit 1
fi

echo "=========================================="
echo "正在构建 ${PKG_NAME} PKG 软件包"
echo "版本: ${VERSION}"
echo "=========================================="

echo "正在准备构建目录..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"
mkdir -p "$BUILD_DIR/payload/Applications/$PKG_NAME"

echo "正在复制应用程序文件..."
cp -a "dist/app/." "$BUILD_DIR/payload/Applications/$PKG_NAME/"

echo "正在创建安装后脚本..."
mkdir -p "$BUILD_DIR/scripts"
cat > "$BUILD_DIR/scripts/postinstall" <<'EOF'
#!/bin/bash
set -e
APP_DIR="/Applications/PyStart"
if [ -d "$APP_DIR" ]; then
    chmod +x "$APP_DIR/PyStart"
    xattr -cr "$APP_DIR" 2>/dev/null || true
fi
exit 0
EOF
chmod +x "$BUILD_DIR/scripts/postinstall"

echo "正在构建组件包..."
pkgbuild \
    --root "$BUILD_DIR/payload" \
    --scripts "$BUILD_DIR/scripts" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    --install-location "/" \
    "$COMPONENT_PKG"

echo "正在构建最终的 PKG 包..."
productbuild \
    --package "$COMPONENT_PKG" \
    "$PKG_FILE"

echo "正在清理临时文件..."
rm -rf "$BUILD_DIR/payload"
rm -f "$COMPONENT_PKG"

echo "=========================================="
echo "PKG 软件包构建成功！"
echo "文件位置: $PKG_FILE"
echo "文件大小: $(du -h "$PKG_FILE")"
echo "=========================================="
