#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轮廓检测精度验证脚本
对比改进前后的边距准确性
"""

import os
from PIL import Image
import numpy as np
from shoe_image_processor import ShoeImageProcessor

def analyze_margin_accuracy(image_path: str, processor: ShoeImageProcessor):
    """
    分析图片边距精确度
    
    Args:
        image_path: 图片路径
        processor: 处理器实例
    
    Returns:
        (left_margin_ratio, right_margin_ratio, accuracy_score)
    """
    with Image.open(image_path) as image:
        width, height = image.size
        
        # 使用改进的轮廓检测
        left, top, right, bottom = processor.find_object_bounds_on_white_bg(image)
        
        # 计算边距比例
        left_margin = left / width
        right_margin = (width - right) / width
        
        # 计算精确度分数（与10%的偏差）
        target_margin = 0.1
        left_error = abs(left_margin - target_margin)
        right_error = abs(right_margin - target_margin)
        balance_error = abs(left_margin - right_margin)
        
        accuracy_score = 1.0 - (left_error + right_error + balance_error)
        
        return left_margin, right_margin, accuracy_score

def main():
    print("🔍 轮廓检测精度验证")
    print("=" * 50)
    
    processor = ShoeImageProcessor()
    
    # 测试图片
    test_image = "input_images/0c980089d5034acf84f2d9df071b6269.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ 测试图片不存在: {test_image}")
        return
    
    print(f"📸 分析图片: {test_image}")
    
    # 处理图片并分析边距
    print("\n🎯 处理并分析边距...")
    processor.process_single_image(
        test_image, 
        "test_fixed_results/precision_test.jpg",
        use_margin_mode=True
    )
    
    # 分析结果
    left_margin, right_margin, accuracy = analyze_margin_accuracy(
        "test_fixed_results/precision_test.jpg", 
        processor
    )
    
    print(f"\n📊 边距分析结果:")
    print(f"  左边距: {left_margin:.1%}")
    print(f"  右边距: {right_margin:.1%}")
    print(f"  目标边距: 10%")
    print(f"  左偏差: {abs(left_margin - 0.1):.1%}")
    print(f"  右偏差: {abs(right_margin - 0.1):.1%}")
    print(f"  左右差异: {abs(left_margin - right_margin):.1%}")
    print(f"  精确度分数: {accuracy:.1%}")
    
    # 判断结果
    if abs(left_margin - 0.1) < 0.02 and abs(right_margin - 0.1) < 0.02:
        print("✅ 边距精确度: 优秀")
    elif abs(left_margin - 0.1) < 0.03 and abs(right_margin - 0.1) < 0.03:
        print("✅ 边距精确度: 良好")
    else:
        print("⚠️ 边距精确度: 需要改进")
    
    if abs(left_margin - right_margin) < 0.02:
        print("✅ 左右均衡: 优秀")
    elif abs(left_margin - right_margin) < 0.03:
        print("✅ 左右均衡: 良好")
    else:
        print("⚠️ 左右均衡: 需要改进")
    
    print(f"\n📁 结果已保存: test_fixed_results/precision_test.jpg")
    print("\n🎉 分析完成！")

if __name__ == "__main__":
    main() 