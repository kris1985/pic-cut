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

# Windows编码修复
if platform.system() == 'Windows':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def safe_print(text):
    """安全的打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果遇到编码错误，使用ASCII安全的输出
        print(text.encode('ascii', 'replace').decode('ascii'))

def check_requirements():
    """检查打包环境和依赖"""
    safe_print("Checking build environment...")
    
    # 检查操作系统
    if platform.system() != 'Windows':
        safe_print("Warning: Current system is not Windows, generated exe will only run on current system")
    
    safe_print(f"System info: {platform.system()} {platform.machine()}")
    safe_print(f"Python version: {sys.version}")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        safe_print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        safe_print("PyInstaller not installed, installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        safe_print("PyInstaller installation completed")
    
    # 检查关键依赖
    required_packages = ['cv2', 'numpy', 'PIL', 'tkinter']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
                safe_print(f"OpenCV version: {cv2.__version__}")
            elif package == 'numpy':
                import numpy
                safe_print(f"NumPy version: {numpy.__version__}")
            elif package == 'PIL':
                import PIL
                safe_print(f"Pillow version: {PIL.__version__}")
            elif package == 'tkinter':
                import tkinter
                safe_print("Tkinter available")
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        safe_print(f"Missing packages: {', '.join(missing_packages)}")
        return False
    
    return True

def build_exe():
    """构建Windows 64位exe文件"""
    
    safe_print("Starting Shoe Image Cropper build (cross-platform)...")
    
    # 检查环境
    if not check_requirements():
        safe_print("Environment check failed, cannot proceed with build")
        return False
    
    # 清理之前的构建
    cleanup_dirs = ['build', 'dist', '__pycache__']
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            safe_print(f"Cleaning directory: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 删除旧的spec文件
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        os.remove(spec_file)
        safe_print(f"Cleaning spec file: {spec_file}")
    
    # 优化的构建命令 - 跨平台支持
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # 根据系统确定文件名和后缀
    if system == 'windows':
        app_name = 'ShoeImageCropper_v2.0_x64'  # Windows使用英文名避免编码问题
        expected_ext = '.exe'
    elif system == 'darwin':  # macOS
        app_name = 'ShoeImageCropper_v2.0_macOS'
        expected_ext = '.app'  # PyInstaller在macOS上可能生成.app或无后缀
    else:  # Linux
        app_name = 'ShoeImageCropper_v2.0_linux'
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
        safe_print("Starting PyInstaller build...")
        safe_print("This may take several minutes, please wait...")
        
        # 运行命令
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            safe_print("Build completed!")
            
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
                safe_print(f"File size: {file_size:.1f} MB")
                safe_print(f"File location: {found_file.absolute()}")
                
                # 系统特定提示
                if system == 'windows':
                    safe_print("Windows exe generated, can run on any Windows 64-bit system")
                elif system == 'darwin':
                    safe_print("macOS app generated, can run on macOS systems")
                    safe_print("To generate Windows exe, run this script on Windows system")
                else:
                    safe_print("Linux executable generated")
                    safe_print("To generate Windows exe, run this script on Windows system")
                
                # 创建使用说明和依赖信息
                create_readme(system, app_name)
                create_version_info(system, app_name)
                
                return True
            else:
                safe_print("Executable file not found")
                safe_print(f"Expected filename: {app_name}{expected_ext}")
                return False
        else:
            safe_print("Build failed:")
            safe_print(f"stdout: {result.stdout}")
            safe_print(f"stderr: {result.stderr}")
            return False
            
    except Exception as e:
        safe_print(f"Build failed: {e}")
        return False

def create_readme(system, app_name):
    """创建详细的使用说明文件"""
    readme_content = f"""# Shoe Image Cropper v2.0 ({system.capitalize()})

Intelligent cropping tool designed for shoe product images

## System Requirements
- Windows 7/8/10/11 (64-bit)
- At least 4GB RAM
- At least 100MB available disk space

## Quick Start
1. Run "{app_name}.exe"
2. Select input folder (containing shoe images)
3. Select output folder
4. Adjust processing parameters (optional)
5. Click "Start Cropping"

## Features
- Smart shoe detection and positioning
- Auto-centered cropping
- Support for 4:3 and 3:4 aspect ratio auto-selection
- Intelligent file size control (new feature)
- High image quality preservation
- Batch processing
- Real-time progress display

## Supported Formats
- Input: JPG, JPEG, PNG, BMP, TIFF, WebP
- Output: High-quality JPEG

## Parameters
- **Aspect Ratio**: Auto-select/4:3 landscape/3:4 portrait
- **Image Quality**: High quality (recommended)/Normal quality
- **High Resolution Mode**: For large images, preserves more pixels

## v2.0 New Features
- Smart file size control - prevents oversized output files
- Dynamic quality adjustment - intelligent optimization based on source
- Real-time size monitoring - auto re-optimization for oversized files
- Multi-strategy detection - more accurate shoe recognition

## Usage Tips
1. Input images recommended resolution not less than 800x600
2. Ensure shoes are clearly visible in the image
3. Simpler backgrounds work better for detection
4. For large images, enable "High Resolution Mode"

## Troubleshooting
- If program won't start, check Windows system version is 64-bit
- If processing fails, check if image files are corrupted
- If results are unsatisfactory, try different parameters

## Technical Support
- Version: v2.0
- Architecture: {system.capitalize()} x64
- Technology: Python + OpenCV + AI algorithms
"""
    
    os.makedirs('dist', exist_ok=True)
    with open('dist/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    safe_print("README created")

def create_version_info(system, app_name):
    """创建版本信息文件"""
    import datetime
    
    version_info = f"""# Version Information

Program Name: Shoe Image Cropper
Version: v2.0
Target Platform: {system.capitalize()} x64
Build Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python Version: {sys.version}
System Platform: {platform.platform()}

## Changelog

### v2.0 (Current)
- NEW: Smart file size control system
- NEW: Dynamic quality adjustment algorithm
- NEW: Real-time file size monitoring
- NEW: Multi-strategy object detection
- NEW: High resolution mode optimization
- FIX: File size increase issue
- FIX: Memory usage optimization
- UI: Improved user interface

### v1.0
- Basic smart cropping functionality
- GUI interface
- Batch processing
"""
    
    with open('dist/VERSION.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    safe_print("Version info created")

def main():
    """主函数"""
    system_name = platform.system()
    safe_print("=" * 60)
    safe_print(f"  Shoe Image Cropper - {system_name} Build Tool")
    safe_print("=" * 60)
    
    success = build_exe()
    
    if success:
        safe_print("\n" + "=" * 60)
        safe_print("SUCCESS: Build completed!")
        
        # 根据系统显示不同的成功信息
        if system_name.lower() == 'windows':
            safe_print("File location: dist/ShoeImageCropper_v2.0_x64.exe")
            safe_print("Tips:")
            safe_print("   - Generated exe can run on any Windows 64-bit system")
            safe_print("   - No need to install Python or other dependencies")
        elif system_name.lower() == 'darwin':
            safe_print("App location: dist/ShoeImageCropper_v2.0_macOS.app")
            safe_print("Tips:")
            safe_print("   - Generated app can run on macOS systems")
            safe_print("   - To generate Windows exe, run on Windows system")
            safe_print("   - Or use GitHub Actions for multi-platform builds")
        else:
            safe_print("Executable location: dist/ShoeImageCropper_v2.0_linux")
            safe_print("Tips:")
            safe_print("   - Generated file can run on Linux systems")
            safe_print("   - To generate Windows exe, run on Windows system")
            
        safe_print("README: dist/README.txt")
        safe_print("Version info: dist/VERSION.txt")
        safe_print("=" * 60)
        safe_print("\nCross-platform build tips:")
        safe_print("   - Windows exe: Run this script on Windows")
        safe_print("   - macOS app: Run this script on macOS")  
        safe_print("   - Linux binary: Run this script on Linux")
        safe_print("   - Or use GitHub Actions for all platforms")
    else:
        safe_print("\n" + "=" * 60)
        safe_print("ERROR: Build failed!")
        safe_print("Please check the error messages above")
        safe_print("=" * 60)
    
    try:
        input("\nPress any key to exit...")
    except:
        pass  # 在CI环境中可能没有输入

if __name__ == "__main__":
    main() 