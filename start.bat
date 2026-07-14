@echo off
chcp 65001 >nul
title 简历评估系统
cls

echo ==========================================
echo     简历评估系统 - 一键启动工具
echo ==========================================
echo.

REM 检查 Python 是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/5] 已检测到 Python 版本：
python --version
echo.

REM 首次运行：若缺少 .env，从模板自动创建
if not exist ".env" (
    echo [2/5] 未找到 .env 配置文件，正在从模板创建...
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo       已创建 .env，请用记事本打开并填写 DEEPSEEK_API_KEY 后重新运行。
        echo       说明详见 "请先阅读-配置说明.txt"
        echo.
        pause
        exit /b 1
    ) else (
        echo [错误] 未找到 .env 和 .env.example，请参考配置说明创建 .env
        pause
        exit /b 1
    )
)

REM 检查是否需要安装依赖
if not exist "venv" (
    echo [3/5] 首次运行，正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

echo [4/5] 正在安装/更新依赖（首次运行可能需要几分钟）...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 安装依赖失败，请检查网络连接
    pause
    exit /b 1
)

echo [5/5] 正在启动服务...
echo.
echo ==========================================
echo  服务启动成功！
echo  请在浏览器中访问: http://127.0.0.1:5000
echo  按 Ctrl+C 可以停止服务
echo ==========================================
echo.

REM 自动打开浏览器
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000/

REM 启动 Flask 应用
python app.py

REM 如果服务停止
echo.
echo 服务已停止
echo 按任意键关闭窗口...
pause >nul
