#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 PNG 图片生成 Windows 图标文件 (.ico)
生成包含多个尺寸的图标文件，适用于不同显示场景
"""

from PIL import Image
import os
from pathlib import Path

def generate_ico_from_png(png_path, ico_path=None, sizes=None):
    """
    从 PNG 图片生成 ICO 文件
    
    Args:
        png_path: PNG 图片路径
        ico_path: 输出的 ICO 文件路径，如果为 None 则自动生成
        sizes: 图标尺寸列表，如果为 None 则使用默认尺寸
    """
    if sizes is None:
        # Windows 推荐的图标尺寸
        sizes = [16, 32, 48, 64, 128, 256]
    
    if ico_path is None:
        # 自动生成输出路径
        png_file = Path(png_path)
        ico_path = png_file.parent / f"{png_file.stem}.ico"
    
    print(f"📖 读取源图片: {png_path}")
    
    # 打开原始图片
    try:
        original_img = Image.open(png_path)
        print(f"✅ 原始图片尺寸: {original_img.size[0]}x{original_img.size[1]}")
    except Exception as e:
        print(f"❌ 无法打开图片: {e}")
        return False
    
    # 如果图片有透明通道，确保使用 RGBA 模式
    if original_img.mode != 'RGBA':
        # 转换为 RGBA 以支持透明背景
        if original_img.mode == 'RGB':
            original_img = original_img.convert('RGBA')
        else:
            original_img = original_img.convert('RGBA')
        print(f"🔄 已转换为 RGBA 模式以支持透明背景")
    
    # 生成不同尺寸的图标
    icon_images = []
    print(f"\n🖼️  生成图标尺寸:")
    
    for size in sizes:
        # 使用高质量重采样算法（LANCZOS）
        resized = original_img.resize((size, size), Image.Resampling.LANCZOS)
        icon_images.append(resized)
        print(f"   ✓ {size}x{size} 像素")
    
    # 保存为 ICO 文件
    print(f"\n💾 保存图标文件: {ico_path}")
    try:
        # 保存所有尺寸到单个 ICO 文件
        original_img.save(
            ico_path,
            format='ICO',
            sizes=[(img.size[0], img.size[1]) for img in icon_images]
        )
        print(f"✅ 图标文件生成成功!")
        
        # 显示文件信息
        file_size = os.path.getsize(ico_path) / 1024  # KB
        print(f"📊 文件大小: {file_size:.2f} KB")
        print(f"📐 包含尺寸: {', '.join([f'{s}x{s}' for s in sizes])}")
        
        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

if __name__ == "__main__":
    # 设置路径
    script_dir = Path(__file__).parent
    logo_path = script_dir / "logo.png"
    icon_path = script_dir / "icon.ico"
    
    if not logo_path.exists():
        print(f"❌ 找不到源图片: {logo_path}")
        print(f"   请确保 logo.png 文件存在于项目根目录")
        exit(1)
    
    print("=" * 60)
    print("🎨 Windows 图标生成工具")
    print("=" * 60)
    print()
    
    success = generate_ico_from_png(str(logo_path), str(icon_path))
    
    print()
    print("=" * 60)
    if success:
        print(f"✨ 完成! 图标文件已保存到: {icon_path}")
        print(f"\n💡 提示:")
        print(f"   - 现在可以在 build_exe.py 中使用 --icon=icon.ico")
        print(f"   - 图标包含多个尺寸，适用于不同显示场景")
    else:
        print("❌ 生成失败，请检查错误信息")
    print("=" * 60)
