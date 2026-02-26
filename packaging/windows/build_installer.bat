@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM =================================================
REM 脚本名称：build_installer.bat
REM 脚本功能：一键完成 Nuitka 打包和 Inno Setup 安装包制作
REM =================================================

REM 切换到项目根目录
cd /d "%~dp0..\.."

echo [信息] 当前工作目录: %CD%

REM 检查版本文件
if not exist "src\VERSION" (
    echo [错误] 找不到 src\VERSION 文件！
    exit /b 1
)

REM 读取版本号
set /p VERSION=<src\VERSION
set VERSION=%VERSION: =%
echo [信息] 版本号: %VERSION%

REM 清理旧目录
if exist "dist" (
    echo [信息] 清理旧构建...
    REM 只清理 app 目录和安装包，保留 main.build 以加速后续打包（如果需要）
    if exist "dist\app" rd /s /q "dist\app"
    del /q "dist\*.exe" 2>nul
) else (
    mkdir "dist"
)

echo [1/3] Nuitka 打包中...

REM 注意：多行命令 ^ 后严禁有空格
call nuitka --mingw64 ^
 --standalone ^
 --show-progress ^
 --show-memory ^
 --windows-disable-console ^
 --plugin-enable=pyqt6 ^
 --include-data-dir=src/locale=src/locale ^
 --include-data-dir=assets=assets ^
 --include-data-files=src\LICENSE=LICENSE ^
 --windows-icon-from-ico=assets\PyStart.ico ^
 --output-dir=dist ^
 --output-filename=PyStart ^
 src\main.py
if %ERRORLEVEL% neq 0 (
    echo [错误] Nuitka 打包失败    
    exit /b %ERRORLEVEL%
)

echo [信息] 正在整理打包产物...
REM 兼容处理：如果生成了 PyStart.dist 或 main.dist，都统一重命名为 app
if exist "dist\PyStart.dist" (
    echo [信息] 找到 dist\PyStart.dist，正在重命名为 app...
    if exist "dist\app" rd /s /q "dist\app"
    move "dist\PyStart.dist" "dist\app"
) else if exist "dist\main.dist" (
    echo [警告] 找到 dist\main.dist - 默认名，正在重命名为 app...
    if exist "dist\app" rd /s /q "dist\app"
    move "dist\main.dist" "dist\app"
)

if not exist "dist\app\PyStart.exe" (
    echo [错误] 未找到 dist\app\PyStart.exe
    dir dist    
    exit /b 1
)

echo [信息] 正在同步 runtime 目录到 app 文件夹...
if exist "runtime" (
    :: 使用 robocopy 同步，并强制设置 ERRORLEVEL 为 0 避免脚本中断
    robocopy "runtime" "dist\app\runtime" /E /MT:8 /R:3 /W:5 /NFL /NDL /NJH /NJS
    if !ERRORLEVEL! LEQ 7 (
        echo [信息] runtime 同步成功。
        set ERRORLEVEL=0
    ) else (
        echo [警告] robocopy 返回异常代码: !ERRORLEVEL!
    )
) else (
    echo [警告] 找不到 runtime 目录，跳过同步。
)

echo [2/3] Inno Setup 编译中...

"D:\Inno Setup 6\ISCC.exe" ^
 /DAppVersion=%VERSION% ^
 /DAppName="PyStart" ^
 /DAppExeName="PyStart.exe" ^
 /DOutputFileName="PyStart_v%VERSION%-x64_Setup" ^
 "packaging\windows\setup.iss"
if %ERRORLEVEL% neq 0 (
    echo [错误] Inno Setup 编译失败
    
    exit /b %ERRORLEVEL%
)

echo [3/3] 全部完成！

echo [信息] 正在清理临时构建目录...
if exist "dist\app" rd /s /q "dist\app"
if exist "dist\main.build" rd /s /q "dist\main.build"

echo [信息] 安装包位置:
dir "dist\PyStart_v%VERSION%-x64_Setup.exe"
