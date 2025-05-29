#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 64位 EXE打包脚本 - 鞋子图片智能裁剪工具
支持完整的依赖打包和优化
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def check_requirements():
    """检查打包环境和依赖"""
    print("🔍 检查打包环境...")
    
    # 检查操作系统
    if platform.system() != 'Windows':
        print("⚠️  警告: 当前系统不是Windows，生成的exe仅可在当前系统运行")
    
    print(f"📊 系统信息: {platform.system()} {platform.machine()}")
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller未安装，正在安装...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("✅ PyInstaller安装完成")
    
    # 检查关键依赖
    required_packages = ['cv2', 'numpy', 'PIL', 'tkinter']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
                print(f"✅ OpenCV版本: {cv2.__version__}")
            elif package == 'numpy':
                import numpy
                print(f"✅ NumPy版本: {numpy.__version__}")
            elif package == 'PIL':
                import PIL
                print(f"✅ Pillow版本: {PIL.__version__}")
            elif package == 'tkinter':
                import tkinter
                print("✅ Tkinter可用")
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        return False
    
    return True

def build_exe():
    """构建Windows 64位exe文件"""
    
    print("🚀 开始构建鞋子图片智能裁剪工具 (Windows x64)...")
    
    # 检查环境
    if not check_requirements():
        print("❌ 环境检查失败，无法继续打包")
        return False
    
    # 清理之前的构建
    cleanup_dirs = ['build', 'dist', '__pycache__']
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            print(f"🧹 清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 删除旧的spec文件
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        os.remove(spec_file)
        print(f"🧹 清理spec文件: {spec_file}")
    
    # 优化的构建命令 - 跨平台支持
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # 根据系统确定文件名和后缀
    if system == 'windows':
        app_name = '鞋子图片智能裁剪工具_v2.0_x64'
        expected_ext = '.exe'
    elif system == 'darwin':  # macOS
        app_name = '鞋子图片智能裁剪工具_v2.0_macOS'
        expected_ext = '.app'  # PyInstaller在macOS上可能生成.app或无后缀
    else:  # Linux
        app_name = '鞋子图片智能裁剪工具_v2.0_linux'
        expected_ext = ''  # Linux通常无后缀
    
    cmd = [
        'pyinstaller',
        '--onefile',                    # 单文件模式
        '--windowed',                   # 无控制台窗口
        f'--name={app_name}',
        
        # 显式包含依赖
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageTk',
        '--hidden-import=PIL.ImageFilter',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=pathlib',
        '--hidden-import=queue',
        '--hidden-import=threading',
        '--hidden-import=logging',
        
        # 排除不需要的模块以减小文件大小
        '--exclude-module=matplotlib',
        '--exclude-module=IPython',
        '--exclude-module=pytest',
        '--exclude-module=pandas',
        '--exclude-module=scipy.tests',
        '--exclude-module=numpy.tests',
        '--exclude-module=PIL.tests',
        '--exclude-module=setuptools',
        '--exclude-module=distutils',
        
        # 优化选项
        '--strip',                      # 去除符号信息
        '--noupx',                      # 不使用UPX压缩（避免兼容性问题）
        '--noconfirm',                  # 不确认覆盖
        '--clean',                      # 清理临时文件
        
        # 主文件
        'shoe_cropper_gui.py'
    ]
    
    try:
        print("📦 开始PyInstaller打包...")
        print("⏰ 这可能需要几分钟时间，请耐心等待...")
        
        # 运行命令
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 构建完成!")
            
            # 检查生成的文件 - 跨平台支持
            possible_files = [
                Path('dist') / f'{app_name}{expected_ext}',
                Path('dist') / f'{app_name}',  # 无后缀版本
                Path('dist') / f'{app_name}.app',  # macOS应用包
            ]
            
            found_file = None
            for file_path in possible_files:
                if file_path.exists():
                    found_file = file_path
                    break
            
            if found_file:
                file_size = found_file.stat().st_size / (1024 * 1024)  # MB
                print(f"📦 文件大小: {file_size:.1f} MB")
                print(f"📂 文件位置: {found_file.absolute()}")
                
                # 系统特定提示
                if system == 'windows':
                    print("🎯 Windows exe文件已生成，可在任何Windows 64位系统运行")
                elif system == 'darwin':
                    print("🍎 macOS应用已生成，可在macOS系统运行")
                    print("💡 如需Windows exe文件，请在Windows系统上运行此脚本")
                else:
                    print("🐧 Linux可执行文件已生成")
                    print("💡 如需Windows exe文件，请在Windows系统上运行此脚本")
                
                # 创建使用说明和依赖信息
                create_readme(system, app_name)
                create_version_info(system, app_name)
                
                return True
            else:
                print("❌ 可执行文件未找到")
                print(f"💡 预期文件名: {app_name}{expected_ext}")
                return False
        else:
            print("❌ 构建失败:")
            print("标准输出:", result.stdout)
            print("错误输出:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        return False

def create_readme(system, app_name):
    """创建详细的使用说明文件"""
    readme_content = f"""# 鞋子图片智能裁剪工具 v2.0 ({system.capitalize()})

🎯 专为鞋子商品图片设计的智能裁剪工具

## 💻 系统要求
- Windows 7/8/10/11 (64位)
- 至少 4GB 内存
- 至少 100MB 可用磁盘空间

## 🚀 快速使用
1. 双击运行 "{app_name}.exe"
2. 选择输入文件夹（包含鞋子图片）
3. 选择输出文件夹
4. 调整处理参数（可选）
5. 点击"开始裁剪"

## ✨ 功能特点
✨ 智能检测鞋子位置
✨ 自动居中裁剪
✨ 支持4:3和3:4比例自动选择
✨ 智能文件大小控制（新功能）
✨ 高图片质量保持
✨ 批量处理
✨ 实时处理进度显示

## 📸 支持格式
- 输入: JPG, JPEG, PNG, BMP, TIFF, WebP
- 输出: 高质量 JPEG

## 🔧 处理参数说明
- **裁剪比例**: 自动选择/4:3横向/3:4竖向
- **图片质量**: 高质量(推荐)/普通质量
- **高分辨率模式**: 适用于大图片，保持更多像素

## 📊 新版本特性 (v2.0)
🔥 智能文件大小控制 - 防止输出文件过大
🔥 动态质量调整 - 根据原图智能优化
🔥 实时大小监控 - 自动重新优化超标文件
🔥 多策略检测 - 更准确的鞋子识别

## 🔍 使用提示
1. 输入图片建议分辨率不低于800x600
2. 确保鞋子在图片中清晰可见
3. 背景越简单，检测效果越好
4. 大图片建议开启"高分辨率模式"

## 🆘 故障排除
- 如果程序无法启动，请检查Windows系统版本是否为64位
- 如果处理失败，请检查图片文件是否损坏
- 如果结果不理想，可以尝试不同的处理参数

## 📞 技术支持
- 版本: v2.0
- 架构: {system.capitalize()} x64
- 开发语言: Python + OpenCV + AI算法
"""
    
    os.makedirs('dist', exist_ok=True)
    with open('dist/使用说明.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📝 使用说明已创建")

def create_version_info(system, app_name):
    """创建版本信息文件"""
    import datetime
    
    version_info = f"""# 版本信息

程序名称: 鞋子图片智能裁剪工具
版本号: v2.0
目标平台: {system.capitalize()} x64
构建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python版本: {sys.version}
系统平台: {platform.platform()}

## 更新日志

### v2.0 (当前版本)
- ✨ 新增智能文件大小控制系统
- ✨ 动态质量调整算法
- ✨ 实时文件大小监控
- ✨ 多策略对象检测
- ✨ 高分辨率模式优化
- 🐛 修复文件变大问题
- 🐛 优化内存使用
- 🎨 改进用户界面

### v1.0
- 基础智能裁剪功能
- GUI界面
- 批量处理
"""
    
    with open('dist/版本信息.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("📋 版本信息已创建")

def main():
    """主函数"""
    system_name = platform.system()
    print("=" * 60)
    print(f"  鞋子图片智能裁剪工具 - {system_name} 打包程序")
    print("=" * 60)
    
    success = build_exe()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 打包成功！")
        
        # 根据系统显示不同的成功信息
        if system_name.lower() == 'windows':
            print("📁 exe文件位置: dist/鞋子图片智能裁剪工具_v2.0_x64.exe")
            print("💡 提示:")
            print("   - 生成的exe文件可以在任何Windows 64位系统上运行")
            print("   - 不需要安装Python或其他依赖")
        elif system_name.lower() == 'darwin':
            print("📁 应用位置: dist/鞋子图片智能裁剪工具_v2.0_macOS.app")
            print("💡 提示:")
            print("   - 生成的app文件可以在macOS系统上运行")
            print("   - 要生成Windows exe文件，需要在Windows系统上运行")
            print("   - 或使用GitHub Actions自动化构建多平台版本")
        else:
            print("📁 可执行文件位置: dist/鞋子图片智能裁剪工具_v2.0_linux")
            print("💡 提示:")
            print("   - 生成的文件可以在Linux系统上运行")
            print("   - 要生成Windows exe文件，需要在Windows系统上运行")
            
        print("📖 使用说明: dist/使用说明.txt")
        print("📋 版本信息: dist/版本信息.txt")
        print("=" * 60)
        print("\n🌟 跨平台打包提示:")
        print("   - Windows exe: 在Windows系统运行此脚本")
        print("   - macOS app: 在macOS系统运行此脚本")  
        print("   - Linux binary: 在Linux系统运行此脚本")
        print("   - 或使用GitHub Actions同时构建所有平台版本")
    else:
        print("\n" + "=" * 60)
        print("❌ 打包失败！")
        print("💡 请检查上面的错误信息并重试")
        print("=" * 60)
    
    input("\n按任意键退出...")

if __name__ == "__main__":
    main() 