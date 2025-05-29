@echo off
chcp 65001
echo ==========================================
echo 鞋子图片智能裁剪工具 - EXE打包工具
echo ==========================================
echo.

echo 🔧 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ 错误：未找到Python环境，请先安装Python
    pause
    exit /b 1
)

echo.
echo 📦 安装/更新依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 🚀 开始构建EXE文件...
python build_exe.py

echo.
echo ✅ 构建完成！
echo 📂 请查看 dist 文件夹中的exe文件
echo.
pause 