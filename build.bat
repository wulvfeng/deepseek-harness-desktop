@echo off
chcp 65001 >nul
echo ========================================
echo   DeepSeek Harness Desktop - 打包工具
echo ========================================
echo.

echo [1/2] 安装/更新 PyInstaller...
.venv\Scripts\pip.exe install pyinstaller -q

echo [2/2] 开始打包...
echo.
echo 注意：首次打包需要 3-10 分钟，产物约 300-500MB
echo.

.venv\Scripts\python.exe -m PyInstaller deepseek-harness-desktop.spec --clean --noconfirm

echo.
if exist "dist\deepseek-harness-desktop\deepseek-harness-desktop.exe" (
    echo ========================================
    echo   打包成功！
    echo   输出目录: dist\deepseek-harness-desktop\
    echo ========================================
    echo.
    echo 启动方式：双击 dist\deepseek-harness-desktop\deepseek-harness-desktop.exe
    echo.
    explorer dist\deepseek-harness-desktop
) else (
    echo ========================================
    echo   打包失败，请查看上方错误信息
    echo ========================================
)
pause
