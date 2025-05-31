#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试问题图片的轮廓边距修复
特别针对靴子等贴边的情况
"""

import os
import sys
from PIL import Image
from shoe_image_processor import ShoeImageProcessor

def test_problem_images():
    """测试有问题的图片"""
    print("🧪 问题图片轮廓边距修复测试")
    print("=" * 60)
    
    processor = ShoeImageProcessor()
    
    # 测试图片列表（这些图片之前有边距问题）
    test_images = [
        "input_images/靴子.jpg",
        "input_images/1.webp",
        "input_images/2.jpg",
        "input_images/0c980089d5034acf84f2d9df071b6269.jpg",
        "input_images/2582cf502b5a4e8787a1c735999cc8d0.jpg"
    ]
    
    output_dir = "test_fixed_results"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🎯 目标: 修复鞋子轮廓边距，确保左右各占12.5%")
    print(f"📁 输出目录: {output_dir}")
    print()
    
    successful = 0
    total = 0
    
    for input_image in test_images:
        if not os.path.exists(input_image):
            print(f"⚠️ 跳过不存在的文件: {input_image}")
            continue
            
        total += 1
        filename = os.path.basename(input_image)
        output_image = os.path.join(output_dir, f"fixed_{filename}")
        
        print(f"📸 处理图片 {total}: {filename}")
        
        # 处理图片 - 使用修复后的轮廓边距模式
        success = processor.process_single_image(
            input_image,
            output_image,
            target_ratio='auto',
            high_quality=True,
            preserve_resolution=False,
            use_margin_mode=True
        )
        
        if success:
            successful += 1
            print(f"✅ 处理成功: {output_image}")
            
            # 显示结果统计
            try:
                with Image.open(input_image) as orig, Image.open(output_image) as result:
                    print(f"  原图尺寸: {orig.width}x{orig.height}")
                    print(f"  结果尺寸: {result.width}x{result.height}")
                    
                    # 计算比例
                    ratio = result.width / result.height
                    if abs(ratio - 4/3) < 0.1:
                        ratio_str = "4:3"
                    elif abs(ratio - 3/4) < 0.1:
                        ratio_str = "3:4"
                    else:
                        ratio_str = f"{ratio:.2f}"
                    print(f"  图片比例: {ratio_str}")
            except Exception as e:
                print(f"  ⚠️ 无法读取结果统计: {e}")
                
        else:
            print(f"❌ 处理失败: {filename}")
        
        print()
    
    print("=" * 60)
    print(f"🎉 批量测试完成！")
    print(f"📊 统计结果:")
    print(f"  总计: {total} 张")
    print(f"  成功: {successful} 张")
    print(f"  失败: {total - successful} 张")
    if total > 0:
        print(f"  成功率: {successful/total:.1%}")
    
    print(f"\n🔍 请检查输出目录 {output_dir} 中的结果文件:")
    print("  ✓ 鞋子轮廓是否完整显示")
    print("  ✓ 左右边距是否接近12.5%")
    print("  ✓ 鞋子是否居中显示")
    print("  ✓ 贴边问题是否已修复")

if __name__ == "__main__":
    test_problem_images() 