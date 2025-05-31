#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试边距修复效果
"""

import os
from PIL import Image
from shoe_image_processor import ShoeImageProcessor

def test_margin_fix():
    """测试边距修复效果"""
    print("🧪 测试边距修复效果")
    print("=" * 50)
    
    processor = ShoeImageProcessor()
    
    # 查找测试图片
    test_images = ["sample_shoe.jpg", "green_shoe_original.jpg"]
    for img in test_images:
        if os.path.exists(img):
            test_image = img
            break
    else:
        print("❌ 未找到测试图片")
        print("请确保有以下任一文件:")
        for img in test_images:
            print(f"  - {img}")
        return
    
    print(f"📸 使用测试图片: {test_image}")
    
    # 测试不同的最小分辨率设置
    test_configs = [
        {"min_res": 800, "desc": "低分辨率(800)"},
        {"min_res": 1000, "desc": "中分辨率(1000)"},
        {"min_res": 1200, "desc": "高分辨率(1200)"},
    ]
    
    original_width, original_height = 0, 0
    with Image.open(test_image) as orig:
        original_width, original_height = orig.size
        print(f"原图尺寸: {original_width}x{original_height}")
    
    print("\n🔧 测试不同分辨率设置:")
    
    for config in test_configs:
        output_file = f"test_margin_fix_{config['min_res']}.jpg"
        
        # 临时修改智能裁剪方法的最小分辨率
        with Image.open(test_image) as image:
            result = processor.smart_crop_with_margins(
                image, 
                left_right_margin_ratio=0.1,
                target_ratio='auto',
                min_resolution=config['min_res'],
                fast_mode=True
            )
            result.save(output_file, quality=90)
        
        # 分析结果
        with Image.open(output_file) as result:
            # 检测最终的鞋子边界
            left, top, right, bottom = processor.find_object_bounds_on_white_bg(result)
            
            left_margin = left / result.width
            right_margin = (result.width - right) / result.width
            avg_margin = (left_margin + right_margin) / 2
            margin_diff = abs(left_margin - right_margin)
            
            scale_factor = result.width / original_width
            
            print(f"  {config['desc']}:")
            print(f"    输出尺寸: {result.width}x{result.height}")
            print(f"    放大倍数: {scale_factor:.2f}x")
            print(f"    左边距: {left_margin:.1%}, 右边距: {right_margin:.1%}")
            print(f"    平均边距: {avg_margin:.1%} (目标: 10.0%)")
            print(f"    边距差异: {margin_diff:.1%}")
            
            # 评分
            if abs(avg_margin - 0.1) < 0.02 and margin_diff < 0.02:
                print(f"    评价: ✅ 优秀")
            elif abs(avg_margin - 0.1) < 0.03 and margin_diff < 0.03:
                print(f"    评价: ✅ 良好")
            else:
                print(f"    评价: ⚠️ 需改进")
            print()
    
    print("🎉 测试完成！请查看生成的测试文件对比效果")

if __name__ == "__main__":
    test_margin_fix() 