#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Docker在macOS上构建Windows exe文件
注意：这是实验性方案，可能存在兼容性问题
"""

import os
import subprocess
import platform

def build_windows_in_docker():
    """使用Docker构建Windows exe"""
    
    print("🐳 使用Docker构建Windows版本...")
    print("⚠️  注意：这是实验性方案，推荐使用GitHub Actions")
    
    # 检查Docker是否安装
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker未安装或无法访问")
            return False
        print(f"✅ Docker版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Docker未安装")
        return False
    
    # 创建Dockerfile
    dockerfile_content = """
FROM python:3.9-windowsservercore

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller

# 复制源代码
COPY . .

# 构建exe
RUN python build_simple.py

# 输出目录
VOLUME ["/app/dist"]
"""
    
    with open('Dockerfile.windows', 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)
    
    print("📝 已创建Dockerfile.windows")
    
    # 构建Docker镜像
    print("🏗️  构建Docker镜像...")
    cmd_build = [
        'docker', 'build', 
        '-f', 'Dockerfile.windows',
        '-t', 'shoe-cropper-windows', 
        '.'
    ]
    
    try:
        result = subprocess.run(cmd_build, check=True)
        print("✅ Docker镜像构建成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker镜像构建失败: {e}")
        return False
    
    # 运行容器构建exe
    print("🚀 运行容器构建exe...")
    output_dir = os.path.abspath('dist_windows')
    os.makedirs(output_dir, exist_ok=True)
    
    cmd_run = [
        'docker', 'run', '--rm',
        '-v', f'{output_dir}:/app/dist',
        'shoe-cropper-windows'
    ]
    
    try:
        result = subprocess.run(cmd_run, check=True)
        print("✅ Windows exe构建完成")
        print(f"📁 输出目录: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ exe构建失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🐳 Docker Windows构建工具")
    print("=" * 60)
    
    if platform.system() != 'Darwin':
        print("⚠️  此脚本专为macOS设计")
    
    print("💡 推荐方案:")
    print("   1. 使用GitHub Actions (自动化，支持所有平台)")
    print("   2. 使用Windows系统/虚拟机")
    print("   3. 使用云服务器")
    print("   4. Docker方案 (实验性)")
    
    choice = input("\n是否尝试Docker方案? (y/N): ").lower()
    
    if choice == 'y':
        success = build_windows_in_docker()
        if success:
            print("\n🎉 构建成功!")
        else:
            print("\n❌ 构建失败")
    else:
        print("已取消")

if __name__ == "__main__":
    main() 