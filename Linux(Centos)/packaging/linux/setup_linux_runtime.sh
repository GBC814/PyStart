#!/bin/bash
# 设置 Linux 上的 PyStart 内置 Python 3.14.2 环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "PyStart Linux 内置 Python 环境设置"
echo "=========================================="
echo ""

# 1. 检查 runtime 目录
RUNTIME_DIR="runtime"
PYTHON_DIR="$RUNTIME_DIR/python-3.14.2"
PYTHON_EXE="$PYTHON_DIR/bin/python3"

if [ -f "$PYTHON_EXE" ]; then
    echo "✓ 内置 Python 3.14.2 已存在"
else
    echo "正在下载 Python 3.14.2 for Linux..."
    
    # 创建 runtime 目录
    mkdir -p "$RUNTIME_DIR"
    
    # 下载预编译的 Python
    PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20251205/cpython-3.14.2+20251205-x86_64-unknown-linux-gnu-install_only.tar.gz"
    TEMP_FILE="$RUNTIME_DIR/python_download.tar.gz"
    
    wget "$PYTHON_URL" -O "$TEMP_FILE"
    
    # 解压
    echo "正在解压 Python..."
    tar -xf "$TEMP_FILE" -C "$RUNTIME_DIR"
    
    # 重命名目录
    EXTRACTED_DIR=$(ls -d "$RUNTIME_DIR"/cpython-*-install_only 2>/dev/null | head -1)
    if [ -n "$EXTRACTED_DIR" ]; then
        mv "$EXTRACTED_DIR" "$PYTHON_DIR"
    fi
    
    # 清理下载文件
    rm "$TEMP_FILE"
    
    # 设置执行权限
    chmod +x "$PYTHON_EXE"
    chmod +x "$PYTHON_DIR/bin/pip3" 2>/dev/null || true
    
    echo "✓ Python 3.14.2 下载并解压完成"
fi

# 2. 验证 Python
echo ""
echo "正在验证 Python..."
"$PYTHON_EXE" --version
echo ""

# 3. 安装依赖
REQUIREMENTS_FILE="requirements-3.14.2-linux.txt"

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "正在为内置 Python 安装依赖..."
    echo "(这不会影响系统的 Python 3.10.11)"
    echo ""
    
    # 升级 pip
    "$PYTHON_EXE" -m pip install --upgrade pip
    
    # 安装依赖
    "$PYTHON_EXE" -m pip install -r "$REQUIREMENTS_FILE" --no-warn-script-location
    
    echo ""
    echo "✓ 依赖安装完成"
else
    echo "警告: 未找到 $REQUIREMENTS_FILE"
fi

echo ""
echo "=========================================="
echo "设置完成！"
echo "=========================================="
echo ""
echo "内置 Python 位置: $PYTHON_EXE"
echo ""
echo "您现在可以："
echo "1. 运行程序: python3 src/main.py"
echo "2. 构建 deb 包: ./packaging/linux/build_deb.sh"
echo "3. 构建 rpm 包: ./packaging/linux/build_rpm.sh"
echo ""
