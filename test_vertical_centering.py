#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
垂直居中效果测试脚本
分析和验证鞋子在画布中的垂直位置
"""

import os
from PIL import Image
import numpy as np
from shoe_image_processor import ShoeImageProcessor

def analyze_vertical_position(image_path: str, processor: ShoeImageProcessor):
    """
    分析图片的垂直位置情况
    
    Args:
        image_path: 图片路径
        processor: 处理器实例
    
    Returns:
        详细的垂直位置分析结果
    """
    with Image.open(image_path) as image:
        width, height = image.size
        
        # 检测鞋子边界
        left, top, right, bottom = processor.find_object_bounds_on_white_bg(image)
        
        # 计算边距
        left_margin = left / width
        right_margin = (width - right) / width
        top_margin = top / height
        bottom_margin = (height - bottom) / height
        
        # 计算鞋子的位置信息
        shoe_center_y = (top + bottom) / 2
        canvas_center_y = height / 2
        vertical_offset = shoe_center_y - canvas_center_y
        vertical_offset_ratio = vertical_offset / height
        
        # 分析结果
        result = {
            'width': width,
            'height': height,
            'shoe_bounds': (left, top, right, bottom),
            'margins': {
                'left': left_margin,
                'right': right_margin,
                'top': top_margin,
                'bottom': bottom_margin
            },
            'vertical_analysis': {
                'shoe_center_y': shoe_center_y,
                'canvas_center_y': canvas_center_y,
                'offset_pixels': vertical_offset,
                'offset_ratio': vertical_offset_ratio,
                'balance_error': abs(top_margin - bottom_margin)
            }
        }
        
        return result

def print_analysis(result):
    """打印分析结果"""
    print(f"📏 画布尺寸: {result['width']}x{result['height']}")
    print(f"👟 鞋子边界: 左{result['shoe_bounds'][0]}, 上{result['shoe_bounds'][1]}, 右{result['shoe_bounds'][2]}, 下{result['shoe_bounds'][3]}")
    print(f"\n📊 边距分析:")
    print(f"  左边距: {result['margins']['left']:.1%}")
    print(f"  右边距: {result['margins']['right']:.1%}")
    print(f"  上边距: {result['margins']['top']:.1%}")
    print(f"  下边距: {result['margins']['bottom']:.1%}")
    
    print(f"\n🎯 垂直位置分析:")
    print(f"  鞋子中心Y: {result['vertical_analysis']['shoe_center_y']:.0f}")
    print(f"  画布中心Y: {result['vertical_analysis']['canvas_center_y']:.0f}")
    print(f"  垂直偏移: {result['vertical_analysis']['offset_pixels']:.0f} 像素")
    print(f"  偏移比例: {result['vertical_analysis']['offset_ratio']:.1%}")
    print(f"  上下边距差: {result['vertical_analysis']['balance_error']:.1%}")
    
    # 给出评价
    if result['vertical_analysis']['balance_error'] < 0.05:
        print("✅ 垂直居中: 优秀")
    elif result['vertical_analysis']['balance_error'] < 0.08:
        print("✅ 垂直居中: 良好")
    elif result['vertical_analysis']['balance_error'] < 0.12:
        print("⚠️ 垂直居中: 可接受")
    else:
        print("❌ 垂直居中: 需要改进")
    
    # 视觉偏向分析
    if result['vertical_analysis']['offset_ratio'] > 0.02:
        print("📍 视觉位置: 偏下")
    elif result['vertical_analysis']['offset_ratio'] < -0.02:
        print("📍 视觉位置: 偏上")
    else:
        print("📍 视觉位置: 居中")

def main():
    print("🔍 垂直居中效果分析")
    print("=" * 50)
    
    processor = ShoeImageProcessor()
    
    # 测试图片
    test_image = "input_images/0c980089d5034acf84f2d9df071b6269.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ 测试图片不存在: {test_image}")
        return
    
    print(f"📸 分析图片: {test_image}")
    
    # 处理图片
    print("\n🎯 处理图片...")
    processor.process_single_image(
        test_image, 
        "test_fixed_results/vertical_test.jpg",
        use_margin_mode=True
    )
    
    # 分析原图
    print("\n📋 原图分析:")
    original_result = analyze_vertical_position(test_image, processor)
    print_analysis(original_result)
    
    # 分析处理后的图片
    print("\n📋 处理后分析:")
    processed_result = analyze_vertical_position("test_fixed_results/vertical_test.jpg", processor)
    print_analysis(processed_result)
    
    print(f"\n📁 结果已保存: test_fixed_results/vertical_test.jpg")
    print("\n🎉 分析完成！")

if __name__ == "__main__":
    main() 