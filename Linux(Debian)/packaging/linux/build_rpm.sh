#!/bin/bash
# 用于构建 PyStart .rpm 软件包的脚本（适用于 Fedora/RHEL/CentOS）

set -e

# 配置
PKG_NAME="PyStart"
ARCH="x86_64"
MAINTAINER="PyStart Team <pystart@example.com>"
DESCRIPTION="Python IDE for beginners"
DEPENDS=""
URL="https://github.com/PyStart/PyStart"
LICENSE="MIT"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build_rpm"
DIST_DIR="$PROJECT_ROOT/dist"
TAR_NAME="${PKG_NAME,,}"

# 引入通用函数
source "$SCRIPT_DIR/build_common.sh"

cd "$PROJECT_ROOT"

# 检查 Nuitka 打包是否完成
if [ ! -d "dist/app" ]; then
    echo "错误: 请先运行 ./packaging/linux/build_nuitka.sh 进行 Nuitka 打包！"
    exit 1
fi

# 获取版本号
VERSION="$(get_version)"
PKG_VERSION="${VERSION}"
RELEASE="1"
RPM_FILE="${DIST_DIR}/${PKG_NAME}_v${VERSION}_amd64.rpm"

echo "=========================================="
echo "正在构建 ${PKG_NAME} RPM 软件包"
echo "版本: ${VERSION}"
echo "架构: ${ARCH}"
echo "=========================================="

# 准备目录
mkdir -p "$DIST_DIR"
mkdir -p "$BUILD_DIR/$TAR_NAME"

# 准备构建内容
echo "正在准备构建目录..."
mkdir -p "$BUILD_DIR/$TAR_NAME/opt/$PKG_NAME"
mkdir -p "$BUILD_DIR/$TAR_NAME/usr/bin"
mkdir -p "$BUILD_DIR/$TAR_NAME/usr/share/applications"
mkdir -p "$BUILD_DIR/$TAR_NAME/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/$TAR_NAME/usr/share/doc/$PKG_NAME"
echo "构建目录结构创建成功"

# 复制 Nuitka 打包后的文件
echo "正在复制 Nuitka 打包后的文件..."
cp -r "dist/app/"* "$BUILD_DIR/$TAR_NAME/opt/$PKG_NAME/"
echo "文件复制成功"

# 安装桌面文件
echo "正在安装桌面文件..."
cp "packaging/linux/PyStart.desktop" "$BUILD_DIR/$TAR_NAME/usr/share/applications/$PKG_NAME.desktop"
if [ -f "assets/PyStart.png" ]; then
    cp "assets/PyStart.png" "$BUILD_DIR/$TAR_NAME/usr/share/icons/hicolor/256x256/apps/$PKG_NAME.png"
fi
echo "桌面文件安装成功"

# 创建包装脚本
echo "正在创建包装脚本..."
cat > "$BUILD_DIR/$TAR_NAME/usr/bin/$PKG_NAME" <<EOF
#!/bin/bash
PYSTART_HOME="/opt/$PKG_NAME"
exec "\$PYSTART_HOME/$PKG_NAME" "\$@"
EOF
chmod +x "$BUILD_DIR/$TAR_NAME/usr/bin/$PKG_NAME"
echo "包装脚本创建成功"

# 创建 spec 文件
SPEC_FILE="$BUILD_DIR/$PKG_NAME.spec"

cat > "$SPEC_FILE" <<EOF
Name:           ${PKG_NAME,,}
Version:        ${PKG_VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        ${DESCRIPTION}

License:        ${LICENSE}
URL:            ${URL}

BuildArch:      ${ARCH}

%description
${DESCRIPTION}

%install
mkdir -p %{buildroot}
cp -r * %{buildroot}/

%post
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor
fi

%postun
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor
fi

%files
/opt/${PKG_NAME}/
/usr/bin/${PKG_NAME}
/usr/share/applications/${PKG_NAME}.desktop
/usr/share/icons/hicolor/256x256/apps/${PKG_NAME}.png
/usr/share/doc/${PKG_NAME}/
%doc

%changelog
* $(date +"%a %b %d %Y") ${MAINTAINER} - ${PKG_VERSION}
- 首次发布
EOF

# 构建 RPM
echo "正在构建 rpm 软件包..."
cd "$BUILD_DIR"
rpmbuild --quiet -bb --buildroot "$BUILD_DIR/$TAR_NAME" "$SPEC_FILE" 2>/dev/null || {
    echo "rpmbuild 失败，尝试使用不同的方法..."
    TAR_FILE="${TAR_NAME}-${PKG_VERSION}.tar.gz"
    cd "$BUILD_DIR/$TAR_NAME"
    tar czf "../$TAR_FILE" .
    cd ".."
    cp "$TAR_FILE" "$DIST_DIR/" 2>/dev/null || true
    echo "由于 rpmbuild 配置问题，已生成 tar.gz 包"
    echo "位置: $DIST_DIR/$TAR_FILE"
    echo "使用 rpmbuild 环境后可构建完整 rpm 包"
    exit 0
}

# 查找生成的 RPM 并复制
RPM_BUILD_DIR="${HOME}/rpmbuild/RPMS/${ARCH}"
if [ -d "$RPM_BUILD_DIR" ]; then
    BUILT_RPM=$(ls -1t "$RPM_BUILD_DIR/${PKG_NAME,,}-${PKG_VERSION}"*.rpm 2>/dev/null | head -1)
    if [ -f "$BUILT_RPM" ]; then
        cp "$BUILT_RPM" "$RPM_FILE"
        echo "=========================================="
        echo "RPM 软件包构建成功！"
        echo "文件位置: ${RPM_FILE}"
        echo "=========================================="
    else
        echo "注意: 无法定位生成的 rpm 包，请查看 ${HOME}/rpmbuild/RPMS/ 目录"
    fi
fi

# 清理
cd "$PROJECT_ROOT"
rm -rf "$BUILD_DIR"
