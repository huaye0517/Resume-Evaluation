@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cls

echo ==========================================
echo   简历评估系统 - 一键打包工具
echo ==========================================
echo.
echo 本脚本会生成 zip 压缩包，发给同事解压后双击 start.bat 即可使用。
echo.

set "SOURCE_DIR=%~dp0"
set "PACKAGE_NAME=简历评估系统"
set "PACKAGE_VERSION=v1.2"
set "TEMP_ROOT=%TEMP%\ResumeEvaluation_Package_%RANDOM%"
set "PACKAGE_DIR=%TEMP_ROOT%\%PACKAGE_NAME%"
set "OUTPUT_DIR=%SOURCE_DIR%dist"
set "ZIP_FILE=%OUTPUT_DIR%\%PACKAGE_NAME%_%PACKAGE_VERSION%.zip"

REM ---------- 检查必要文件 ----------
set "MISSING="
if not exist "%SOURCE_DIR%app.py" set "MISSING=!MISSING! app.py"
if not exist "%SOURCE_DIR%start.bat" set "MISSING=!MISSING! start.bat"
if not exist "%SOURCE_DIR%requirements.txt" set "MISSING=!MISSING! requirements.txt"
if not exist "%SOURCE_DIR%templates\index.html" set "MISSING=!MISSING! templates\index.html"
if not exist "%SOURCE_DIR%static\style.css" set "MISSING=!MISSING! static\style.css"

if defined MISSING (
    echo [错误] 缺少必要文件:!MISSING!
    pause
    exit /b 1
)

echo [1/4] 准备打包目录...
if exist "%TEMP_ROOT%" rmdir /s /q "%TEMP_ROOT%"
mkdir "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%\static"
mkdir "%PACKAGE_DIR%\templates"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo [2/4] 复制程序文件...

REM 核心 Python 源码
copy "%SOURCE_DIR%app.py" "%PACKAGE_DIR%\" >nul
copy "%SOURCE_DIR%deepseek_client.py" "%PACKAGE_DIR%\" >nul
copy "%SOURCE_DIR%evaluator.py" "%PACKAGE_DIR%\" >nul
copy "%SOURCE_DIR%resume_parser.py" "%PACKAGE_DIR%\" >nul
copy "%SOURCE_DIR%requirements.txt" "%PACKAGE_DIR%\" >nul

REM 启动与检查脚本（不含 build.bat，避免同事误用）
copy "%SOURCE_DIR%start.bat" "%PACKAGE_DIR%\" >nul
copy "%SOURCE_DIR%环境检查.bat" "%PACKAGE_DIR%\" >nul

REM 静态资源
copy "%SOURCE_DIR%static\style.css" "%PACKAGE_DIR%\static\" >nul
copy "%SOURCE_DIR%templates\index.html" "%PACKAGE_DIR%\templates\" >nul

REM 配置模板与文档
copy "%SOURCE_DIR%.env.example" "%PACKAGE_DIR%\.env.example" >nul
copy "%SOURCE_DIR%部署说明-给同事.md" "%PACKAGE_DIR%\" >nul
copy "%SOURCE_DIR%请先阅读-配置说明.txt" "%PACKAGE_DIR%\" >nul
copy "%SOURCE_DIR%快速上手-README.txt" "%PACKAGE_DIR%\" >nul

echo [3/4] 正在压缩为 zip 包...

if exist "%ZIP_FILE%" del /f /q "%ZIP_FILE%"

powershell -NoProfile -Command ^
    "Compress-Archive -LiteralPath '%PACKAGE_DIR%' -DestinationPath '%ZIP_FILE%' -Force"

if not exist "%ZIP_FILE%" (
    echo.
    echo [错误] 压缩失败！
    echo 临时目录保留在: %PACKAGE_DIR%
    echo 请手动将该文件夹压缩后发给同事。
    pause
    explorer "%PACKAGE_DIR%"
    exit /b 1
)

echo [4/4] 清理临时文件...
rmdir /s /q "%TEMP_ROOT%"

echo.
echo ==========================================
echo   打包成功！
echo ==========================================
echo.
echo 压缩包位置:
echo   %ZIP_FILE%
echo.
echo 发给同事后的使用步骤:
echo   1. 解压 zip，得到 "%PACKAGE_NAME%" 文件夹
echo   2. 按 请先阅读-配置说明.txt 创建并填写 .env
echo   3. 双击 start.bat 启动
echo.
echo 注意: 你的 .env（含 API 密钥）未被打包，密钥需单独提供给同事。
echo ==========================================
echo.
pause
