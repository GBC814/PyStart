#!/bin/bash
# 用于 Linux 平台的 Nuitka 打包脚本

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "正在使用 Nuitka 打包 PyStart (Linux)"
echo "=========================================="

# 检查版本文件
if [ ! -f "src/VERSION" ]; then
    echo "错误: 找不到 src/VERSION 文件！"
    exit 1
fi

# 读取版本号
VERSION="$(cat src/VERSION | tr -d '[:space:]')"
echo "版本号: ${VERSION}"

# 清理旧目录
if [ -d "dist" ]; then
    echo "正在清理旧构建..."
    if [ -d "dist/app" ]; then
        rm -rf "dist/app"
    fi
    rm -f "dist/*.deb" "dist/*.rpm" 2>/dev/null
else
    mkdir -p "dist"
fi

echo "[1/2] Nuitka 打包中..."

# 使用 Nuitka 打包（禁用 perf 计数器来避免 AssertionError）
NUITKA_USE_PERF_COUNTERS=0 python3 -m nuitka \
    --standalone \
    --plugin-enable=pyqt6 \
    --include-data-dir=src/locale=src/locale \
    --include-data-dir=assets=assets \
    --include-data-files=src/LICENSE=LICENSE \
    --output-dir=dist \
    --output-filename=PyStart \
    src/main.py

echo "[信息] 正在整理打包产物..."

# 兼容处理：重命名为 app
if [ -d "dist/PyStart.dist" ]; then
    echo "[信息] 找到 dist/PyStart.dist，正在重命名为 app..."
    if [ -d "dist/app" ]; then
        rm -rf "dist/app"
    fi
    mv "dist/PyStart.dist" "dist/app"
elif [ -d "dist/main.dist" ]; then
    echo "[警告] 找到 dist/main.dist - 默认名，正在重命名为 app..."
    if [ -d "dist/app" ]; then
        rm -rf "dist/app"
    fi
    mv "dist/main.dist" "dist/app"
fi

if [ ! -f "dist/app/PyStart" ]; then
    echo "[错误] 未找到 dist/app/PyStart"
    ls -la dist
    exit 1
fi

echo "[信息] 正在同步数据目录到 app 文件夹..."

# 1. 复制 runtime 目录
if [ -d "runtime" ]; then
    echo "[信息] 正在复制 runtime 目录..."
    cp -a "runtime" "dist/app/"
    echo "[信息] runtime 同步成功"
else
    echo "[警告] 找不到 runtime 目录，跳过同步"
fi

# 2. 确保 locale 目录存在（如果 Nuitka 没复制）
if [ -d "src/locale" ] && [ ! -d "dist/app/src/locale" ]; then
    echo "[信息] 正在补充复制 locale 目录..."
    mkdir -p "dist/app/src"
    cp -a "src/locale" "dist/app/src/"
    echo "[信息] locale 同步成功"
fi

# 3. 检查最终内容
echo "[信息] 最终 app 目录内容:"
ls -la "dist/app/"

echo "[2/2] Nuitka 打包完成！"
echo ""
echo "=========================================="
echo "打包成功！"
echo "输出目录: dist/app/"
echo "可执行文件: dist/app/PyStart"
echo "=========================================="
