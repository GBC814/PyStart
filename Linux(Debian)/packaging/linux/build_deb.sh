#!/bin/bash
# 用于构建 PyStart .deb 软件包的脚本（简单且稳健的版本）

set -e

# 配置
PKG_NAME="PyStart"
ARCH="amd64"
VERSION="1.0.0"
MAINTAINER="PyStart Team"
DESCRIPTION="Python IDE for beginners"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build_deb"
DIST_DIR="$PROJECT_ROOT/dist"
DEB_FILE="$DIST_DIR/${PKG_NAME}_v${VERSION}_${ARCH}.deb"

cd "$PROJECT_ROOT"

# 检查 Nuitka 打包是否完成
if [ ! -d "dist/app" ]; then
    echo "错误: 请先运行 ./packaging/linux/build_nuitka.sh 进行 Nuitka 打包！"
    exit 1
fi

echo "=========================================="
echo "正在构建 ${PKG_NAME} DEB 软件包"
echo "版本: ${VERSION}"
echo "架构: ${ARCH}"
echo "=========================================="

# 1. 清理并准备目录
echo "正在准备构建目录..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# 2. 创建标准目录结构
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/$PKG_NAME"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/usr/share/doc/$PKG_NAME"
echo "目录结构创建成功"

# 3. 复制 Nuitka 打包的文件（使用 cp -a 保留属性）
echo "正在复制 Nuitka 打包文件..."
cp -a "dist/app/." "$BUILD_DIR/opt/$PKG_NAME/"
echo "Nuitka 文件复制成功"

# 4. 安装桌面文件
echo "正在安装桌面文件..."
if [ -f "packaging/linux/PyStart.desktop" ]; then
    cp "packaging/linux/PyStart.desktop" "$BUILD_DIR/usr/share/applications/$PKG_NAME.desktop"
fi
if [ -f "assets/PyStart.png" ]; then
    cp "assets/PyStart.png" "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/$PKG_NAME.png"
fi
echo "桌面文件安装成功"

# 5. 创建包装脚本
echo "正在创建启动脚本..."
cat > "$BUILD_DIR/usr/bin/$PKG_NAME" <<EOF
#!/bin/bash
PYSTART_HOME="/opt/$PKG_NAME"
cd "\$PYSTART_HOME"
exec "\$PYSTART_HOME/$PKG_NAME" "\$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/$PKG_NAME"
echo "启动脚本创建成功"

# 6. 创建 control 文件
echo "正在创建 control 文件..."
cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: ${PKG_NAME,,}
Version: ${VERSION}
Architecture: ${ARCH}
Section: devel
Priority: optional
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
EOF

# 计算并添加已安装大小
INSTALLED_SIZE=$(du -s -k "$BUILD_DIR" | cut -f1)
echo "Installed-Size: $INSTALLED_SIZE" >> "$BUILD_DIR/DEBIAN/control"

# 7. 创建 postinst 脚本
cat > "$BUILD_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e

if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# 8. 创建 prerm 脚本
cat > "$BUILD_DIR/DEBIAN/prerm" <<'EOF'
#!/bin/bash
set -e
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

# 9. 正确设置权限
echo "正在设置文件权限..."
chmod -R 755 "$BUILD_DIR/opt/$PKG_NAME"
chmod 644 "$BUILD_DIR/DEBIAN/control"
echo "权限设置成功"

# 10. 构建 deb 包（使用 gzip 压缩）
echo "正在构建 deb 软件包..."
fakeroot dpkg-deb -Zgzip --build "$BUILD_DIR" "$DEB_FILE"

# 11. 清理
echo "正在清理..."
rm -rf "$BUILD_DIR"

echo "=========================================="
echo "DEB 软件包构建成功！"
echo "文件位置: $DEB_FILE"
echo "文件大小: $(du -h "$DEB_FILE")"
echo "=========================================="
