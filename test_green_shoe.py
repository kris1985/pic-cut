#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试绿色鞋子轮廓边距模式
"""

import os
import sys
from PIL import Image
from shoe_image_processor import ShoeImageProcessor

def test_green_shoe():
    """测试绿色鞋子的轮廓边距功能"""
    print("🧪 绿色鞋子轮廓边距测试")
    print("=" * 50)
    
    processor = ShoeImageProcessor()
    
    # 创建测试图片文件名（假设用户上传的图片已保存）
    input_image = "green_shoe_original.jpg"  # 用户需要将图片保存为这个名字
    output_image = "green_shoe_result_contour.jpg"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_image):
        print(f"❌ 输入图片 {input_image} 不存在")
        print("请将绿色鞋子图片保存为 green_shoe_original.jpg")
        return
    
    print(f"📸 处理图片: {input_image}")
    print(f"🎯 目标: 鞋子轮廓左右边距各占12.5%")
    print()
    
    # 处理图片 - 使用新的轮廓边距模式
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
        with Image.open(input_image) as orig, Image.open(output_image) as result:
            print(f"\n📊 处理结果:")
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
            
        print(f"\n🎉 测试完成！")
        print("请查看输出文件验证:")
        print("  ✓ 鞋子轮廓是否完整显示")
        print("  ✓ 左右边距是否接近12.5%")
        print("  ✓ 鞋子是否居中显示")
        print("  ✓ 是否正确扩展了白色画布")
        
    else:
        print("❌ 处理失败")

if __name__ == "__main__":
    test_green_shoe() 