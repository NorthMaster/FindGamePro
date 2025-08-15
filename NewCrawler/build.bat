@echo off

REM 设置代码页为 UTF-8 以正确显示中文
chcp 65001 >nul

REM 获取当前目录
set CURRENT_DIR=%~dp0

REM 创建并激活虚拟环境（如果尚不存在）
if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖项
pip install pyinstaller pyautogui pyperclip pygetwindow beautifulsoup4

REM 进入脚本文件所在目录
cd /d %CURRENT_DIR%

REM 打包Python脚本到EXE，添加所有依赖
echo 正在将脚本打包为可执行文件...
pyinstaller --onefile --name "AppMagicCrawler" ^
    --add-data "config/urls.txt;config" ^
    --hidden-import pyautogui ^
    --hidden-import pyperclip ^
    --hidden-import pygetwindow ^
    main.py

REM 检查是否成功生成EXE文件
if exist "dist\AppMagicCrawler.exe" (
    echo 成功生成可执行文件：dist\AppMagicCrawler.exe

    REM 创建dist/config目录
    if not exist "dist\config" mkdir "dist\config"
    
    REM 复制配置文件到dist目录
    echo 正在复制配置文件到dist目录...
    copy /y config\urls.txt dist\config\
) else (
    echo 生成可执行文件失败。
    echo.
    echo 检查输出以查看错误。
)

REM 退出虚拟环境
deactivate

REM 暂停查看输出
pause 