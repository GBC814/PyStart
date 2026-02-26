@echo off
REM Windows 7 安装版打包脚本
cd /d "%~dp0.."

set PYTHON_EXE=C:\Python38\python.exe
set MAIN_PY=src\main.py
set ICON_PATH=assets\PyStart.ico
set OUTPUT_DIR=dist

echo [1/3] 正在开始 PyInstaller 打包...
if exist "%OUTPUT_DIR%" rd /s /q "%OUTPUT_DIR%"
mkdir "%OUTPUT_DIR%"

REM 执行 PyInstaller 打包命令
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --windowed --icon="%ICON_PATH%" --name="PyStart" --add-data="assets;assets" --add-data="src/locale;locale" --add-data="src/LICENSE;." --contents-directory "." "%MAIN_PY%"

if %ERRORLEVEL% neq 0 (
    echo [错误] PyInstaller 打包失败。
    pause
    exit /b %ERRORLEVEL%
)

REM 重命名目录以便于管理
move "dist\PyStart" "dist\app"

echo [2/3] 正在同步资源和运行时目录...

echo 正在同步运行时目录 (runtime)...
if exist "runtime" (
    robocopy "runtime" "dist\app\runtime" /E /MT:8 /R:3 /W:5 /NFL /NDL /NJH /NJS
)

echo 正在同步语言文件目录 (locale)...
if exist "src\locale" (
    robocopy "src\locale" "dist\app\locale" /E /MT:8 /R:3 /W:5 /NFL /NDL /NJH /NJS
)

echo [3/3] 正在开始 Inno Setup 编译...
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% set INNO_SETUP=ISCC.exe

%INNO_SETUP% "packaging\setup_win7.iss"

if %ERRORLEVEL% neq 0 (
    echo [错误] Inno Setup 编译失败。
    pause
    exit /b %ERRORLEVEL%
)

echo [完成] 安装包已生成。
pause
