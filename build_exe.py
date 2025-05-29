#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建EXE打包脚本
使用PyInstaller将鞋子图片裁剪工具打包成独立的exe文件
"""

import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

def build_exe():
    """构建exe文件"""
    
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 清理之前的构建
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    print("🚀 开始构建鞋子图片裁剪工具...")
    
    # 简化的PyInstaller参数，减少依赖
    args = [
        'shoe_cropper_gui.py',              # 主程序文件
        '--name=鞋子图片智能裁剪工具',         # 程序名称
        '--onefile',                        # 打包成单个exe文件
        '--windowed',                       # 不显示控制台窗口
        '--noconfirm',                      # 不确认覆盖
        '--clean',                          # 清理临时文件
        '--hidden-import=PIL._tkinter_finder',  # 确保PIL的tkinter支持
        '--hidden-import=cv2',              # 确保cv2被包含
        '--hidden-import=numpy',            # 确保numpy被包含
        '--exclude-module=matplotlib',      # 排除matplotlib
        '--exclude-module=IPython',         # 排除IPython
        '--exclude-module=pytest',          # 排除pytest
        '--exclude-module=sphinx',          # 排除sphinx
        '--exclude-module=pandas.tests',    # 排除pandas测试
        '--exclude-module=scipy.tests',     # 排除scipy测试
        '--distpath=dist',                  # 指定输出目录
        '--workpath=build',                 # 指定工作目录
    ]
    
    # 如果有图标文件，添加到参数中
    if os.path.exists('icon.ico'):
        args.append('--icon=icon.ico')
    
    try:
        # 运行PyInstaller
        PyInstaller.__main__.run(args)
        
        print("✅ 构建完成!")
        print(f"📂 exe文件位置: {os.path.abspath('dist')}")
        
        # 检查生成的文件
        exe_path = Path('dist') / '鞋子图片智能裁剪工具.exe'
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📦 文件大小: {file_size:.1f} MB")
        
        # 创建使用说明
        create_readme()
        
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        return False
    
    return True

def create_readme():
    """创建使用说明文件"""
    readme_content = """# 鞋子图片智能裁剪工具

## 📋 使用说明

### 🚀 快速开始
1. 双击运行 `鞋子图片智能裁剪工具.exe`
2. 点击"浏览"按钮选择包含鞋子图片的文件夹
3. 选择输出文件夹（处理后的图片保存位置）
4. 设置裁剪参数（推荐使用默认设置）
5. 点击"开始裁剪"按钮开始处理

### ⚙️ 参数说明

#### 裁剪比例
- **自动选择**: 根据鞋子形状自动选择最佳比例
- **4:3 (横向)**: 适合横向展示的商品图
- **3:4 (竖向)**: 适合竖向展示的商品图

#### 图片质量
- **高质量**: 保存质量98%，文件较大但画质最佳
- **普通质量**: 保存质量95%，文件适中

#### 高分辨率模式
- 适用于高分辨率原图（>2000px）
- 优先保持更多像素，减少分辨率损失

### 📸 支持格式
- JPG / JPEG
- PNG
- BMP
- TIFF
- WebP

### ✨ 核心功能
- 🎯 智能检测鞋子位置，自动居中裁剪
- 🎨 支持各种背景色（白色、灰色等）
- 👟 适应不同颜色的鞋子（黑色、红色、白色等）
- 📐 精确的比例控制（4:3 或 3:4）
- 🔍 保持高分辨率和图片质量
- ⚡ 批量处理，提高工作效率

### 🛠️ 处理流程
1. **智能检测**: 使用多策略算法检测鞋子边界
2. **自动居中**: 确保鞋子在裁剪区域中心显示
3. **比例调整**: 按指定比例精确裁剪
4. **质量保持**: 使用高质量保存设置

### 📊 处理结果
- 实时显示处理进度
- 详细的处理日志
- 统计信息（总计、成功、失败、成功率）
- 一键打开输出目录

### ❗ 注意事项
- 确保输入目录包含有效的图片文件
- 输出目录会自动创建，无需预先建立
- 处理过程中可以随时点击"停止"按钮终止
- 大批量处理时建议关闭其他占用内存的程序

### 🐛 常见问题

**Q: 处理失败怎么办？**
A: 查看日志区域的错误信息，通常是图片格式不支持或文件损坏

**Q: 裁剪位置不准确？**
A: 尝试不同的裁剪比例设置，或检查原图背景是否过于复杂

**Q: 处理速度慢？**
A: 关闭高分辨率模式，选择普通质量设置

**Q: exe文件无法运行？**
A: 确保Windows系统版本兼容，如有问题请联系技术支持

---

© 2024 鞋子图片智能裁剪工具 v2.0
技术支持: AI智能图像处理算法
"""
    
    os.makedirs('dist', exist_ok=True)
    with open('dist/使用说明.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📝 使用说明已创建: dist/使用说明.txt")

if __name__ == "__main__":
    success = build_exe()
    if success:
        input("\n按任意键退出...")
    else:
        input("\n构建失败，按任意键退出...")