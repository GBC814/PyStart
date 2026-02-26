#!/bin/bash
# 用于构建 PyStart .rpm 软件包的简化脚本（适用于 Fedora/RHEL/CentOS/AnolisOS）

set -e

# 配置
PKG_NAME="PyStart"
ARCH="x86_64"
MAINTAINER="PyStart Team <pystart@example.com>"
DESCRIPTION="Python IDE for beginners"
URL="https://github.com/PyStart/PyStart"
LICENSE="MIT"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build_rpm"
DIST_DIR="$PROJECT_ROOT/dist"

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

# 准备 rpmbuild 目录结构
echo "正在准备 rpmbuild 目录..."
RPMBUILD_DIR="${HOME}/rpmbuild"
rm -rf "${RPMBUILD_DIR}"
mkdir -p "${RPMBUILD_DIR}/BUILD"
mkdir -p "${RPMBUILD_DIR}/RPMS/${ARCH}"
mkdir -p "${RPMBUILD_DIR}/SOURCES"
mkdir -p "${RPMBUILD_DIR}/SPECS"
mkdir -p "${RPMBUILD_DIR}/SRPMS"

# 创建源目录
echo "正在创建源包..."
mkdir -p "$BUILD_DIR"
rm -rf "$BUILD_DIR/$PKG_NAME"
cp -r "dist/app" "$BUILD_DIR/$PKG_NAME"
# 确保不包含开发环境的残留配置文件，强制用户首次启动时生成新配置
rm -f "$BUILD_DIR/$PKG_NAME/config.json"
cp "packaging/linux/PyStart.desktop" "$BUILD_DIR/"
# 确保 .desktop 文件使用 Unix 风格的换行符（LF）
sed -i 's/\r$//' "$BUILD_DIR/PyStart.desktop"
if [ -f "assets/PyStart.png" ]; then
    cp "assets/PyStart.png" "$BUILD_DIR/"
fi

    cat > "${RPMBUILD_DIR}/SPECS/${PKG_NAME,,}.spec" <<EOF
Name:           ${PKG_NAME,,}
Version:        ${PKG_VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        ${DESCRIPTION}

License:        ${LICENSE}
URL:            ${URL}

BuildArch:      ${ARCH}
AutoReqProv:    no
# 禁用所有 brp 检查
%global __os_install_post %{nil}
%global __brp_mangle_shebangs %{nil}
%global __brp_compress %{nil}
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_static_archive %{nil}
%global __brp_check_rpaths %{nil}
%global __brp_remove_la_files %{nil}
%global __brp_python_bytecompile %{nil}
%global __brp_check_desktop %{nil}
%undefine __brp_mangle_shebangs
# 禁用 debuginfo 包生成，防止 strip
%define debug_package %{nil}

%description
${DESCRIPTION}

%prep
# 清理

%install
# 创建目录
mkdir -p %{buildroot}/opt/${PKG_NAME}
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

# 复制 Nuitka 打包后的文件
cp -r ${DIST_DIR}/app/* %{buildroot}/opt/${PKG_NAME}/

# 显式复制 assets 目录到 /opt/PyStart/assets
# 确保字体文件一定存在
if [ -d "${PROJECT_ROOT}/src/assets" ]; then
    mkdir -p %{buildroot}/opt/${PKG_NAME}/assets
    cp -r "${PROJECT_ROOT}/src/assets/"* %{buildroot}/opt/${PKG_NAME}/assets/
elif [ -d "${PROJECT_ROOT}/assets" ]; then
    mkdir -p %{buildroot}/opt/${PKG_NAME}/assets
    cp -r "${PROJECT_ROOT}/assets/"* %{buildroot}/opt/${PKG_NAME}/assets/
fi

# 复制图标
if [ -f "${PROJECT_ROOT}/assets/PyStart.png" ]; then
    cp "${PROJECT_ROOT}/assets/PyStart.png" %{buildroot}/usr/share/icons/hicolor/256x256/apps/${PKG_NAME}.png
fi

# 安装桌面文件
cp ${BUILD_DIR}/${PKG_NAME}.desktop %{buildroot}/usr/share/applications/${PKG_NAME}.desktop

# 创建启动脚本
# 使用 exec -a 来保留 argv[0]，防止 Nuitka 误判
# 注意：使用 'WRAPPER_EOF' 防止 rpmbuild 阶段的变量展开，但 build_rpm.sh 自身生成 spec 时需要转义 $
cat > %{buildroot}/usr/bin/${PKG_NAME} <<'WRAPPER_EOF'
#!/bin/bash
export PYSTART_HOME="/opt/PyStart"
cd "\$PYSTART_HOME"

# 如果存在 lib 目录，尝试加入 LD_LIBRARY_PATH
if [ -d "\$PYSTART_HOME/lib" ]; then
    export LD_LIBRARY_PATH="\$PYSTART_HOME/lib:\$LD_LIBRARY_PATH"
fi

# 确保主程序有执行权限
chmod +x "\$PYSTART_HOME/PyStart"

# 启动并捕获输出到日志文件（如果在调试模式）
if [ "\$1" == "--debug" ]; then
    exec "./PyStart" "\$@" > /tmp/PyStart_debug.log 2>&1
else
    exec "./PyStart" "\$@"
fi
WRAPPER_EOF
chmod +x %{buildroot}/usr/bin/${PKG_NAME}

%files
/opt/${PKG_NAME}/
/usr/bin/${PKG_NAME}
/usr/share/applications/${PKG_NAME}.desktop
/usr/share/icons/hicolor/256x256/apps/${PKG_NAME}.png

%changelog
* Thu Feb 20 2026 ${MAINTAINER} - ${PKG_VERSION}
- Initial release
EOF

# 构建 RPM（禁用所有检查）
echo "正在构建 rpm 软件包..."
cd "$RPMBUILD_DIR"
QA_RPATHS=$(( 0x0001|0x0002|0x0004|0x0008|0x0010|0x0020 )) \
LC_TIME=C \
rpmbuild -bb \
    --define "_topdir $RPMBUILD_DIR" \
    --define "__brp_mangle_shebangs %{nil}" \
    --define "__brp_check_rpaths %{nil}" \
    --define "__brp_check_desktop %{nil}" \
    "SPECS/${PKG_NAME,,}.spec"

# 查找生成的 RPM 并复制
BUILT_RPM=$(ls -1t "$RPMBUILD_DIR/RPMS/${ARCH}/${PKG_NAME,,}-${PKG_VERSION}"*.rpm 2>/dev/null | head -1)
if [ -f "$BUILT_RPM" ]; then
    cp "$BUILT_RPM" "$RPM_FILE"
    echo "=========================================="
    echo "RPM 软件包构建成功！"
    echo "文件位置: ${RPM_FILE}"
    echo "=========================================="
    
    # 清理
    cd "$PROJECT_ROOT"
    rm -rf "$BUILD_DIR"
else
    echo "错误: 无法定位生成的 rpm 包"
    echo "请查看: ${RPMBUILD_DIR}/RPMS/${ARCH}/"
    exit 1
fi
