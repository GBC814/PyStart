@echo off
chcp 65001 >nul
set BASEDIR=%~dp0
cd /d "%BASEDIR%..\.."

set VERSION=1.0.0
set PYTHON_EXE=D:\Python310\python.exe
set MAIN_PY=src\main.py
set ICON_PATH=assets\PyStart.ico
set OUTPUT_DIR=dist
set SIGNTOOL="D:\Windows Kits\10\bin\10.0.17763.0\x64\signtool.exe"
set CERT_PATH="D:\PyStart\MyLocalCert.pfx"
set CERT_PASSWORD="123456"

echo 开始 Nuitka 构建...

:: 清理旧的构建目录
if exist "%OUTPUT_DIR%" rd /s /q "%OUTPUT_DIR%"

"%PYTHON_EXE%" -m nuitka ^
    --standalone ^
    --mingw64 ^
    --lto=yes ^
    --show-progress ^
    --show-memory ^
    --plugin-enable=pyqt6 ^
    --windows-disable-console ^
    --windows-icon-from-ico="%ICON_PATH%" ^
    --windows-company-name="PyStart" ^
    --windows-product-name="PyStart" ^
    --windows-file-version="%VERSION%" ^
    --windows-product-version="%VERSION%" ^
    --windows-file-description="Python Environment Manager" ^
    --copyright="Copyright © 2026 PyStart" ^
    --output-dir="%OUTPUT_DIR%" ^
    --output-filename=PyStart ^
    --include-data-dir=assets=assets ^
    --include-data-dir=src/locale=src/locale ^
    --include-data-files=src/LICENSE=LICENSE ^
    --assume-yes-for-downloads ^
    "%MAIN_PY%"

if %ERRORLEVEL% neq 0 (
    echo 错误：Nuitka 构建失败，错误代码 %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo 构建完成！

:: 同步运行时目录
echo 正在同步 runtime 目录...
set TARGET_DIST=
if exist "dist\PyStart.dist" set TARGET_DIST=dist\PyStart.dist
if exist "dist\main.dist" set TARGET_DIST=dist\main.dist

if "%TARGET_DIST%"=="" goto :skip_sync

if exist "runtime" (
    robocopy "runtime" "%TARGET_DIST%\runtime" /E /MT:8 /R:3 /W:5 /NFL /NDL /NJH /NJS
    echo runtime 目录同步成功。
) else (
    echo 警告：未找到源 runtime 目录。
)

:skip_sync

echo 正在签署可执行文件...
if exist %CERT_PATH% (
    if exist "%OUTPUT_DIR%\PyStart.dist\PyStart.exe" (
        %SIGNTOOL% sign /f %CERT_PATH% /p %CERT_PASSWORD% /tr http://timestamp.digicert.com /td sha256 /fd sha256 "%OUTPUT_DIR%\PyStart.dist\PyStart.exe"
    ) else (
        if exist "%OUTPUT_DIR%\main.dist\PyStart.exe" (
            %SIGNTOOL% sign /f %CERT_PATH% /p %CERT_PASSWORD% /tr http://timestamp.digicert.com /td sha256 /fd sha256 "%OUTPUT_DIR%\main.dist\PyStart.exe"
        ) else (
            echo 错误：在 dist 中未找到用于签名的可执行文件。
        )
    )
) else (
    echo 未找到证书，跳过签名。
)

echo ............. 正在创建 ZIP 压缩包 .......................
SET PATH=%PATH%;D:\7-Zip
set ZIP_NAME=PyStart-v%VERSION%-windows-portable.zip

if exist "%ZIP_NAME%" del "%ZIP_NAME%"
if exist ".\%ZIP_NAME%" del "dist\%ZIP_NAME%"

set TARGET_DIST=
if exist "dist\PyStart.dist" set TARGET_DIST=dist\PyStart.dist
if exist "dist\main.dist" set TARGET_DIST=dist\main.dist

if "%TARGET_DIST%"=="" goto :dist_not_found

echo 正在从 %TARGET_DIST% 打包...
cd /d "%TARGET_DIST%"
7z a -tzip "..\%ZIP_NAME%" *
cd /d "..\.."

echo.
echo [信息] 便携版位置:
dir "dist\%ZIP_NAME%"

:: 清理临时构建目录
echo 正在清理 %OUTPUT_DIR% 中的临时构建目录...
for /d %%i in ("%OUTPUT_DIR%\*.build") do rd /s /q "%%i"
for /d %%i in ("%OUTPUT_DIR%\*.dist") do rd /s /q "%%i"

goto :end

:dist_not_found
echo 错误：未找到构建输出目录！
exit /b 1

:end
exit /b 0
