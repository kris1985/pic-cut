#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边距模式演示脚本
展示如何确保鞋子左右边距各占12.5%，必要时扩展白色画布
"""

import os
import sys
from pathlib import Path
from PIL import Image
from shoe_image_processor import ShoeImageProcessor

def demo_margin_mode():
    """演示边距模式功能"""
    print("🎯 边距模式演示")
    print("=" * 60)
    print("功能：确保鞋子居中显示，左右边距各占12.5%")
    print("必要时自动扩展白色画布")
    print()
    
    processor = ShoeImageProcessor()
    
    # 查找示例图片
    test_images = []
    for ext in ['.jpg', '.jpeg', '.png']:
        test_images.extend(Path('.').glob(f"*{ext}"))
    
    test_images = [img for img in test_images if 'test_' not in img.name.lower() 
                   and 'output' not in img.name.lower() 
                   and 'result' not in img.name.lower()
                   and 'traditional' not in img.name.lower()
                   and 'margin' not in img.name.lower()]
    
    if not test_images:
        print("❌ 未找到测试图片")
        return
    
    input_image = test_images[0]
    print(f"📸 使用示例图片: {input_image.name}")
    
    # 创建输出文件名
    output_image = f"demo_result_{input_image.name}"
    
    print(f"📊 处理参数:")
    print(f"  • 左右边距: 12.5%")
    print(f"  • 鞋子居中显示")
    print(f"  • 自动扩展白色画布")
    print(f"  • 目标比例: 自动选择")
    print()
    
    # 处理图片
    print("🔄 正在处理...")
    success = processor.process_single_image(
        str(input_image),
        output_image,
        target_ratio='auto',
        high_quality=True,
        preserve_resolution=False,
        use_margin_mode=True
    )
    
    if success:
        print("✅ 处理完成！")
        print(f"📁 输出文件: {output_image}")
        
        # 显示结果统计
        print("\n📊 处理结果:")
        with Image.open(input_image) as orig, Image.open(output_image) as result:
            print(f"  原图尺寸: {orig.width}x{orig.height}")
            print(f"  结果尺寸: {result.width}x{result.height}")
            print(f"  比例: {result.width/result.height:.2f} ({'4:3' if abs(result.width/result.height - 4/3) < 0.1 else '3:4' if abs(result.width/result.height - 3/4) < 0.1 else '其他'})")
            
        print("\n🎉 演示完成！")
        print("请查看输出文件以验证:")
        print("  ✓ 鞋子是否居中显示")
        print("  ✓ 左右边距是否接近12.5%")
        print("  ✓ 是否正确扩展了白色画布")
        
    else:
        print("❌ 处理失败")

def demo_comparison():
    """对比演示：传统模式 vs 边距模式"""
    print("🔄 对比演示：传统模式 vs 边距模式")
    print("=" * 60)
    
    processor = ShoeImageProcessor()
    
    # 查找示例图片
    test_images = []
    for ext in ['.jpg', '.jpeg', '.png']:
        test_images.extend(Path('.').glob(f"*{ext}"))
    
    test_images = [img for img in test_images if 'test_' not in img.name.lower() 
                   and 'demo_' not in img.name.lower()]
    
    if not test_images:
        print("❌ 未找到测试图片")
        return
    
    input_image = test_images[0]
    print(f"📸 使用示例图片: {input_image.name}")
    
    # 传统模式
    traditional_output = f"demo_traditional_{input_image.name}"
    print("\n📋 传统模式处理...")
    processor.process_single_image(
        str(input_image),
        traditional_output,
        use_margin_mode=False
    )
    
    # 边距模式
    margin_output = f"demo_margin_{input_image.name}"
    print("\n📐 边距模式处理...")
    processor.process_single_image(
        str(input_image),
        margin_output,
        use_margin_mode=True
    )
    
    print("\n✅ 对比演示完成！")
    print(f"📁 传统模式结果: {traditional_output}")
    print(f"📁 边距模式结果: {margin_output}")
    print("\n🔍 对比要点:")
    print("  • 传统模式: 基于现有内容裁剪，边距不固定")
    print("  • 边距模式: 确保12.5%边距，必要时扩展画布")
    print("  • 边距模式更适合商品展示的标准化需求")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        demo_comparison()
    else:
        demo_margin_mode() 