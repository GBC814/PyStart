#!/bin/bash
# PyStart Linux 软件包通用构建函数

# 从 VERSION 文件获取版本号
get_version() {
    if [ -f "src/VERSION" ]; then
        cat "src/VERSION" | tr -d '[:space:]'
    else
        echo "1.0.0"
    fi
}

# 准备构建目录结构
prepare_build_dir() {
    local build_dir="$1"
    local pkg_name="$2"
    local version="$3"
    local arch="$4"
    
    echo "正在准备构建目录: $build_dir"
    
    # 清理并创建构建目录
    rm -rf "$build_dir"
    mkdir -p "$build_dir"
    
    # 创建标准目录结构
    mkdir -p "$build_dir/opt/$pkg_name"
    mkdir -p "$build_dir/usr/bin"
    mkdir -p "$build_dir/usr/share/applications"
    mkdir -p "$build_dir/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$build_dir/usr/share/doc/$pkg_name"
    
    echo "构建目录结构创建成功"
}

# 复制应用程序文件
copy_app_files() {
    local build_dir="$1"
    local pkg_name="$2"
    
    echo "正在复制应用程序文件..."
    
    # 复制应用程序代码
    cp -r src "$build_dir/opt/$pkg_name/"
    cp -r assets "$build_dir/opt/$pkg_name/" 2>/dev/null || true
    cp -r runtime "$build_dir/opt/$pkg_name/" 2>/dev/null || true
    cp README.md "$build_dir/usr/share/doc/$pkg_name/" 2>/dev/null || true
    cp requirements.txt "$build_dir/opt/$pkg_name/" 2>/dev/null || true
    cp requirements-3.14.2-linux.txt "$build_dir/opt/$pkg_name/" 2>/dev/null || true
    
    echo "应用程序文件复制成功"
}

# 安装依赖到内置 Python
install_dependencies_to_runtime() {
    local build_dir="$1"
    local pkg_name="$2"
    
    echo "正在检查内置 Python 环境..."
    
    local python_path="$build_dir/opt/$pkg_name/runtime/python-3.14.2/bin/python3"
    
    # 检查是否有内置 Python
    if [ -f "$python_path" ]; then
        echo "正在为内置 Python 3.14.2 安装依赖..."
        
        # 复制 requirements 文件
        if [ -f "requirements-3.14.2-linux.txt" ]; then
            cp "requirements-3.14.2-linux.txt" "$build_dir/opt/$pkg_name/"
        fi
        
        # 使用内置 Python 的 pip 安装依赖
        "$python_path" -m pip install --upgrade pip
        
        # 1. 先安装系统仓库可能没有的基础库
        echo "正在安装系统缺失的基础库 (PyQt6-Fluent-Widgets、PyQt6-QScintilla)..."
        "$python_path" -m pip install PyQt6-Fluent-Widgets PyQt6-QScintilla --no-warn-script-location
        
        # 2. 再安装您指定的额外库（matplotlib、numpy、pandas 等）
        if [ -f "requirements-3.14.2-linux.txt" ]; then
            echo "正在安装您指定的额外库..."
            "$python_path" -m pip install -r "requirements-3.14.2-linux.txt" --no-deps --no-warn-script-location
        fi
        
        echo "内置 Python 依赖安装成功"
    else
        echo "警告: 未找到内置 Python 3.14.2，跳过依赖安装"
    fi
}

# 安装桌面文件
install_desktop_files() {
    local build_dir="$1"
    local pkg_name="$2"
    
    echo "正在安装桌面文件..."
    
    # 安装 .desktop 文件
    cp "packaging/linux/PyStart.desktop" "$build_dir/usr/share/applications/$pkg_name.desktop"
    
    # 安装图标
    if [ -f "assets/PyStart.png" ]; then
        cp "assets/PyStart.png" "$build_dir/usr/share/icons/hicolor/256x256/apps/$pkg_name.png"
    fi
    
    echo "桌面文件安装成功"
}

# 创建包装脚本
create_wrapper_script() {
    local build_dir="$1"
    local pkg_name="$2"
    
    echo "正在创建包装脚本..."
    
    cat > "$build_dir/usr/bin/$pkg_name" <<EOF
#!/bin/bash
PYSTART_HOME="/opt/$pkg_name"

# 使用系统 Python，但加载内置 Python 的库
PYTHON_EXEC="python3"

# 如果有内置 Python，将其库路径加到 PYTHONPATH 中
if [ -d "\$PYSTART_HOME/runtime/python-3.14.2/lib/python3.14/site-packages" ]; then
    export PYTHONPATH="\$PYSTART_HOME/runtime/python-3.14.2/lib/python3.14/site-packages:\$PYTHONPATH"
fi

cd "\$PYSTART_HOME"
exec "\$PYTHON_EXEC" "\$PYSTART_HOME/src/main.py" "\$@"
EOF
    
    chmod +x "$build_dir/usr/bin/$pkg_name"
    
    echo "包装脚本创建成功"
}
