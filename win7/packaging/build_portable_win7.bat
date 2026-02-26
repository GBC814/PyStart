@echo off
REM Windows 7 便携版打包脚本
REM 使用手动安装的 PyInstaller
cd /d "%~dp0.."

set PYTHON_EXE=C:\Python38\python.exe
set MAIN_PY=src\main.py
set ICON_PATH=assets\PyStart.ico
set OUTPUT_DIR=dist

echo [1/2] 正在开始 PyInstaller 打包...
if exist "%OUTPUT_DIR%" rd /s /q "%OUTPUT_DIR%"
mkdir "%OUTPUT_DIR%"

REM 执行 PyInstaller 打包命令
REM 使用 --contents-directory . 强制所有文件解压到根目录，这有助于 Windows 识别图标
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --windowed --icon="%ICON_PATH%" --name="PyStart" --add-data="assets;assets" --add-data="src/locale;locale" --add-data="src/LICENSE;." --contents-directory "." "%MAIN_PY%"

if %ERRORLEVEL% neq 0 (
    echo [错误] PyInstaller 打包失败。
    pause
    exit /b %ERRORLEVEL%
)

REM 重命名目录以便于管理
move "dist\PyStart" "dist\app"

echo [2/2] 正在同步资源和运行时目录...

echo 正在同步运行时目录 (runtime)...
if exist "runtime" (
    robocopy "runtime" "dist\app\runtime" /E /MT:8 /R:3 /W:5 /NFL /NDL /NJH /NJS
)

echo 正在同步语言文件目录 (locale)...
if exist "src\locale" (
    robocopy "src\locale" "dist\app\locale" /E /MT:8 /R:3 /W:5 /NFL /NDL /NJH /NJS
)

echo 正在创建 ZIP 压缩包...
set SEVEN_ZIP="C:\7-Zip\7z.exe"
if not exist %SEVEN_ZIP% set SEVEN_ZIP=7z.exe

set ZIP_NAME=PyStart-win7-portable.zip
if exist "dist\%ZIP_NAME%" del "dist\%ZIP_NAME%"

cd /d "dist\app"
%SEVEN_ZIP% a -tzip "..\%ZIP_NAME%" *
cd /d "..\.."

echo [完成] 打包文件位置：
dir "dist\%ZIP_NAME%"
pause
