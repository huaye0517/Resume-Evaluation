@echo off
chcp 65001 >nul
cls

echo ==========================================
echo   简历评估系统 - 环境检查工具
echo ==========================================
echo.
echo 本工具用于检查您的电脑是否满足运行条件
echo.

set "ALL_OK=true"

REM 检查 Python
echo [检查 1/4] Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo   状态: 未安装 Python
    echo   建议: 请访问 https://www.python.org/downloads/ 下载安装
    echo          安装时务必勾选 "Add Python.exe to PATH"
    set "ALL_OK=false"
) else (
    for /f "tokens=*" %%a in ('python --version') do echo   状态: 已安装 (%%a)
    echo   结果: 通过
)
echo.

REM 检查 pip
echo [检查 2/4] pip 包管理器...
pip --version >nul 2>&1
if errorlevel 1 (
    echo   状态: 未检测到 pip
    echo   建议: 重新安装 Python，确保安装完整
    set "ALL_OK=false"
) else (
    for /f "tokens=*" %%a in ('pip --version') do echo   状态: 已安装 (%%a)
    echo   结果: 通过
)
echo.

REM 检查 .env 文件
echo [检查 3/4] 配置文件 (.env)...
if exist ".env" (
    echo   状态: 已找到 .env 文件
    
    REM 检查是否配置了 API Key
    findstr /C:"DEEPSEEK_API_KEY=" .env >nul 2>&1
    if errorlevel 1 (
        echo   警告: .env 文件中未找到 DEEPSEEK_API_KEY 配置
        echo   建议: 请检查 .env 文件是否正确配置
        set "ALL_OK=false"
    ) else (
        findstr /C:"DEEPSEEK_API_KEY=your_api_key_here" .env >nul 2>&1
        if errorlevel 1 (
            echo   状态: API 密钥已配置
            echo   结果: 通过
        ) else (
            echo   警告: API 密钥是默认值 "your_api_key_here"
            echo   建议: 请将 .env 文件中的 API 密钥替换为真实密钥
            set "ALL_OK=false"
        )
    )
) else (
    echo   状态: 未找到 .env 文件
    echo   建议: 复制 "请先阅读-配置说明.txt"，重命名为 ".env"
    echo          然后填入你的 DeepSeek API 密钥
    set "ALL_OK=false"
)
echo.

REM 检查必要文件
echo [检查 4/4] 程序文件完整性...
set "FILES_OK=true"
if not exist "app.py" (
    echo   缺失: app.py
    set "FILES_OK=false"
)
if not exist "start.bat" (
    echo   缺失: start.bat
    set "FILES_OK=false"
)
if not exist "requirements.txt" (
    echo   缺失: requirements.txt
    set "FILES_OK=false"
)
if not exist "templates\index.html" (
    echo   缺失: templates/index.html
    set "FILES_OK=false"
)
if not exist "static\style.css" (
    echo   缺失: static/style.css
    set "FILES_OK=false"
)

if "%FILES_OK%"=="true" (
    echo   状态: 所有必要文件齐全
    echo   结果: 通过
) else (
    echo   建议: 请确保所有程序文件都已正确解压
    set "ALL_OK=false"
)
echo.

REM 总结
echo ==========================================
if "%ALL_OK%"=="true" (
    echo   环境检查通过！
    echo.
    echo   可以正常使用系统了：
    echo   双击 "start.bat" 启动服务
echo.
    echo   服务启动后访问: http://127.0.0.1:5000
    echo ==========================================
    echo.
    choice /C YN /N /M "是否立即启动服务？(Y/N)"
    if errorlevel 2 exit /b 0
    if errorlevel 1 (
        echo.
        start.bat
    )
) else (
    echo   环境检查未通过，请根据上方提示修复问题
echo.
    echo   详细说明请参考 "部署说明-给同事.md"
    echo ==========================================
    pause
)
