#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试边距过大问题的脚本
分析每个步骤的中间结果
"""

import os
from PIL import Image
import numpy as np
from shoe_image_processor import ShoeImageProcessor
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

def debug_margin_calculation():
    """调试边距计算过程"""
    print("🔍 调试边距计算过程")
    print("=" * 60)
    
    processor = ShoeImageProcessor()
    
    # 使用一张测试图片
    test_image = "sample_shoe.jpg"  # 请将你的图片命名为这个文件名
    
    if not os.path.exists(test_image):
        print(f"❌ 测试图片不存在: {test_image}")
        print("请将测试图片重命名为 sample_shoe.jpg")
        return
    
    with Image.open(test_image) as image:
        print(f"📸 原图尺寸: {image.width}x{image.height}")
        
        # 第1步：检测鞋子边界
        left, top, right, bottom = processor.find_object_contour_bounds(image)
        object_width = right - left
        object_height = bottom - top
        
        print(f"\n🎯 第1步：鞋子边界检测")
        print(f"  检测到的边界: 左{left}, 上{top}, 右{right}, 下{bottom}")
        print(f"  鞋子尺寸: {object_width}x{object_height}")
        print(f"  鞋子面积占比: {(object_width * object_height) / (image.width * image.height):.1%}")
        
        # 第2步：计算理想画布尺寸
        left_right_margin_ratio = 0.1  # 10%边距
        ideal_canvas_width = object_width / (1 - 2 * left_right_margin_ratio)  # 鞋子占80%
        
        print(f"\n📐 第2步：理想画布计算")
        print(f"  目标边距比例: {left_right_margin_ratio:.1%} (左右各占)")
        print(f"  鞋子应占画布宽度: {1 - 2 * left_right_margin_ratio:.1%}")
        print(f"  理想画布宽度: {ideal_canvas_width:.1f}px")
        print(f"  放大倍数: {ideal_canvas_width / image.width:.2f}x")
        
        # 第3步：检查是否有最小分辨率限制
        min_resolution = 1200
        if object_width > object_height:
            target_ratio = '4:3'
            ratio_w, ratio_h = 4, 3
        else:
            target_ratio = '3:4'
            ratio_w, ratio_h = 3, 4
            
        ideal_canvas_height = ideal_canvas_width * ratio_h / ratio_w
        
        min_width = min_resolution if ratio_w >= ratio_h else min_resolution * ratio_w / ratio_h
        min_height = min_resolution if ratio_h >= ratio_w else min_resolution * ratio_h / ratio_w
        
        final_canvas_width = max(ideal_canvas_width, min_width)
        final_canvas_height = max(ideal_canvas_height, min_height)
        
        print(f"\n📏 第3步：最终画布尺寸")
        print(f"  目标比例: {target_ratio}")
        print(f"  理想画布: {ideal_canvas_width:.0f}x{ideal_canvas_height:.0f}")
        print(f"  最小分辨率要求: {min_width:.0f}x{min_height:.0f}")
        print(f"  最终画布: {final_canvas_width:.0f}x{final_canvas_height:.0f}")
        
        # 第4步：分析为什么边距变大
        actual_margin_ratio = (final_canvas_width - object_width) / 2 / final_canvas_width
        
        print(f"\n⚠️ 第4步：问题分析")
        print(f"  预期左右边距: {left_right_margin_ratio:.1%}")
        print(f"  实际左右边距: {actual_margin_ratio:.1%}")
        print(f"  边距放大倍数: {actual_margin_ratio / left_right_margin_ratio:.2f}x")
        
        if final_canvas_width > ideal_canvas_width:
            print(f"  🔍 问题原因: 最小分辨率限制导致画布过大")
            print(f"    最小分辨率要求: {min_resolution}px")
            print(f"    实际需要: {ideal_canvas_width:.0f}px")
            print(f"    被强制放大到: {final_canvas_width:.0f}px")
        else:
            print(f"  🔍 画布尺寸正常，可能是检测问题")
        
        # 第5步：提供解决方案
        print(f"\n💡 解决方案建议:")
        
        if final_canvas_width > ideal_canvas_width:
            # 计算合适的最小分辨率
            suitable_min_resolution = int(ideal_canvas_width * 0.9)
            print(f"  1. 降低最小分辨率要求: 从{min_resolution} -> {suitable_min_resolution}")
            print(f"  2. 或者接受较大边距以保证图片清晰度")
            
            # 测试降低最小分辨率的效果
            print(f"\n🧪 测试降低最小分辨率效果:")
            test_min_width = suitable_min_resolution if ratio_w >= ratio_h else suitable_min_resolution * ratio_w / ratio_h
            test_min_height = suitable_min_resolution if ratio_h >= ratio_w else suitable_min_resolution * ratio_h / ratio_w
            
            test_final_width = max(ideal_canvas_width, test_min_width)
            test_final_height = max(ideal_canvas_height, test_min_height)
            test_margin_ratio = (test_final_width - object_width) / 2 / test_final_width
            
            print(f"  测试最小分辨率: {suitable_min_resolution}")
            print(f"  测试画布尺寸: {test_final_width:.0f}x{test_final_height:.0f}")
            print(f"  测试边距比例: {test_margin_ratio:.1%}")
            
        if (object_width * object_height) / (image.width * image.height) < 0.3:
            print(f"  3. 鞋子在原图中可能太小，检查检测算法是否准确")
            print(f"     当前鞋子面积占比仅: {(object_width * object_height) / (image.width * image.height):.1%}")

def test_with_custom_settings():
    """使用自定义设置测试"""
    print("\n🛠️ 测试自定义设置")
    print("=" * 40)
    
    processor = ShoeImageProcessor()
    test_image = "sample_shoe.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ 测试图片不存在: {test_image}")
        return
    
    # 测试不同的最小分辨率设置
    test_resolutions = [800, 1000, 1200, 1400]
    
    for min_res in test_resolutions:
        output_file = f"debug_output_min{min_res}.jpg"
        
        # 临时修改处理器的最小分辨率
        success = processor.process_single_image(
            test_image,
            output_file,
            target_ratio='auto',
            high_quality=True,
            preserve_resolution=False,
            use_margin_mode=True,
            fast_mode=True
        )
        
        if success:
            with Image.open(output_file) as result:
                # 重新检测边距
                left, top, right, bottom = processor.find_object_bounds_on_white_bg(result)
                left_margin = left / result.width
                right_margin = (result.width - right) / result.width
                
                print(f"  最小分辨率{min_res}: {result.width}x{result.height}")
                print(f"    左边距: {left_margin:.1%}, 右边距: {right_margin:.1%}")

if __name__ == "__main__":
    debug_margin_calculation()
    test_with_custom_settings() 