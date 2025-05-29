@echo off
chcp 65001 >nul
title 鞋子图片智能裁剪工具 - Windows x64 打包程序

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          鞋子图片智能裁剪工具 - Windows x64 打包程序          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH环境变量
    echo 💡 请先安装Python 3.8+并添加到PATH
    pause
    exit /b 1
)

echo ✅ Python环境正常
echo.

echo 📦 开始打包程序...
python build_simple.py

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                           完成！                             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

if exist "dist\鞋子图片智能裁剪工具_v2.0_x64.exe" (
    echo 🎉 打包成功！
    echo 📁 exe文件位置: dist\鞋子图片智能裁剪工具_v2.0_x64.exe
    echo.
    echo 是否打开dist文件夹？ (Y/N)
    set /p choice=请选择: 
    if /i "%choice%"=="Y" (
        explorer dist
    )
) else (
    echo ❌ 打包失败，请检查错误信息
)

echo.
pause 