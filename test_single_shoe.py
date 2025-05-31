#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单张问题图片的轮廓边距修复
"""

import os
import sys
from PIL import Image
from shoe_image_processor import ShoeImageProcessor

def test_single_shoe():
    """测试单张有问题的鞋子图片"""
    print("🧪 单张问题图片轮廓边距修复测试")
    print("=" * 50)
    
    processor = ShoeImageProcessor()
    
    # 测试有问题的图片
    input_image = "input_images/0c980089d5034acf84f2d9df071b6269.jpg"
    output_image = "test_fixed_results/improved_fixed_0c980089d5034acf84f2d9df071b6269.jpg"
    
    # 确保输出目录存在
    os.makedirs("test_fixed_results", exist_ok=True)
    
    if not os.path.exists(input_image):
        print(f"❌ 输入图片不存在: {input_image}")
        return
    
    print(f"📸 处理图片: {input_image}")
    print(f"🎯 目标: 使用改进的轮廓检测，确保鞋子轮廓左右边距精确为10%")
    print()
    
    # 显示原图信息
    with Image.open(input_image) as orig:
        print(f"📊 原图信息:")
        print(f"  尺寸: {orig.width}x{orig.height}")
        print()
    
    # 处理图片 - 使用改进后的轮廓边距模式
    success = processor.process_single_image(
        input_image,
        output_image,
        target_ratio='auto',
        high_quality=True,
        preserve_resolution=False,
        use_margin_mode=True
    )
    
    if success:
        print("✅ 处理成功！")
        print(f"📁 输出文件: {output_image}")
        
        # 显示结果统计
        with Image.open(output_image) as result:
            print(f"\n📊 处理结果:")
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
            
        print(f"\n🎉 测试完成！")
        print("请对比查看:")
        print(f"  原图: {input_image}")
        print(f"  改进结果: {output_image}")
        print("验证:")
        print("  ✓ 鞋子轮廓是否更精确")
        print("  ✓ 左右边距是否更接近10%")
        print("  ✓ 是否去除了多余的白色边距")
        
    else:
        print("❌ 处理失败")

if __name__ == "__main__":
    test_single_shoe() 