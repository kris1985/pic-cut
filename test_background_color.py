#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景颜色检测和智能填充测试脚本
验证扩展画布时使用相同背景颜色的效果
"""

import os
from PIL import Image, ImageDraw
import numpy as np
from shoe_image_processor import ShoeImageProcessor

def create_test_image_with_background(bg_color: tuple, save_path: str):
    """
    创建一个有特定背景颜色的测试图片
    
    Args:
        bg_color: 背景颜色 (R, G, B)
        save_path: 保存路径
    """
    # 创建一个800x600的测试图片
    width, height = 800, 600
    image = Image.new('RGB', (width, height), bg_color)
    
    # 画一个简单的鞋子形状（椭圆）在右下角（模拟贴边情况）
    draw = ImageDraw.Draw(image)
    
    # 鞋子颜色（与背景对比明显）
    if sum(bg_color) > 400:  # 浅色背景用深色鞋子
        shoe_color = (50, 50, 50)
    else:  # 深色背景用浅色鞋子
        shoe_color = (200, 200, 200)
    
    # 画鞋子（故意贴近右边和下边）
    shoe_left = width - 250
    shoe_top = height - 180
    shoe_right = width - 20  # 距离右边很近
    shoe_bottom = height - 20  # 距离下边很近
    
    draw.ellipse([shoe_left, shoe_top, shoe_right, shoe_bottom], fill=shoe_color)
    
    # 保存图片
    image.save(save_path, 'JPEG', quality=95)
    print(f"已创建测试图片: {save_path}")
    print(f"  背景颜色: RGB{bg_color}")
    print(f"  鞋子颜色: RGB{shoe_color}")
    print(f"  鞋子位置: 右下角贴边")

def test_background_detection(image_path: str, processor: ShoeImageProcessor):
    """
    测试背景颜色检测
    
    Args:
        image_path: 图片路径
        processor: 处理器实例
    
    Returns:
        检测到的背景颜色
    """
    with Image.open(image_path) as image:
        detected_color = processor.detect_background_color(image)
        print(f"检测结果: RGB{detected_color}")
        return detected_color

def main():
    print("🎨 背景颜色检测和智能填充测试")
    print("=" * 60)
    
    processor = ShoeImageProcessor()
    
    # 创建测试目录
    os.makedirs("test_fixed_results", exist_ok=True)
    
    # 测试不同的背景颜色
    test_cases = [
        ((255, 255, 255), "白色背景"),
        ((240, 240, 240), "浅灰背景"),
        ((200, 200, 200), "中灰背景"),
        ((100, 100, 100), "深灰背景"),
        ((0, 0, 0), "黑色背景"),
        ((255, 240, 230), "米色背景"),
        ((230, 255, 230), "浅绿背景"),
        ((230, 230, 255), "浅蓝背景"),
    ]
    
    for i, (bg_color, description) in enumerate(test_cases, 1):
        print(f"\n🧪 测试案例 {i}: {description}")
        print("-" * 40)
        
        # 创建测试图片
        test_image_path = f"test_fixed_results/test_bg_{i}_{bg_color[0]}_{bg_color[1]}_{bg_color[2]}.jpg"
        create_test_image_with_background(bg_color, test_image_path)
        
        # 测试背景颜色检测
        print(f"\n🔍 背景颜色检测:")
        print(f"  原始颜色: RGB{bg_color}")
        detected_color = test_background_detection(test_image_path, processor)
        
        # 计算检测误差
        error = sum(abs(d - o) for d, o in zip(detected_color, bg_color)) / 3
        print(f"  平均误差: {error:.1f}")
        
        if error < 5:
            print("  ✅ 检测精度: 优秀")
        elif error < 10:
            print("  ✅ 检测精度: 良好")
        elif error < 20:
            print("  ⚠️ 检测精度: 可接受")
        else:
            print("  ❌ 检测精度: 需改进")
        
        # 处理图片（测试智能填充）
        output_path = f"test_fixed_results/processed_bg_{i}_{bg_color[0]}_{bg_color[1]}_{bg_color[2]}.jpg"
        print(f"\n🎯 处理图片并测试智能填充:")
        
        success = processor.process_single_image(
            test_image_path,
            output_path,
            use_margin_mode=True
        )
        
        if success:
            print(f"  ✅ 处理成功: {output_path}")
            
            # 检查处理后的图片是否使用了正确的背景颜色
            with Image.open(output_path) as processed_img:
                # 检查四个角落的颜色（应该是扩展的背景色）
                corner_colors = []
                corner_colors.append(processed_img.getpixel((10, 10)))  # 左上
                corner_colors.append(processed_img.getpixel((processed_img.width-10, 10)))  # 右上
                corner_colors.append(processed_img.getpixel((10, processed_img.height-10)))  # 左下
                corner_colors.append(processed_img.getpixel((processed_img.width-10, processed_img.height-10)))  # 右下
                
                # 计算平均角落颜色
                avg_corner_color = tuple(int(sum(c[i] for c in corner_colors) / len(corner_colors)) for i in range(3))
                print(f"  扩展区域颜色: RGB{avg_corner_color}")
                
                # 检查是否与检测到的背景颜色一致
                fill_error = sum(abs(a - d) for a, d in zip(avg_corner_color, detected_color)) / 3
                print(f"  填充误差: {fill_error:.1f}")
                
                if fill_error < 5:
                    print("  ✅ 智能填充: 优秀")
                elif fill_error < 10:
                    print("  ✅ 智能填充: 良好")
                else:
                    print("  ⚠️ 智能填充: 需改进")
        else:
            print(f"  ❌ 处理失败")
    
    print(f"\n🎉 测试完成！")
    print(f"📁 所有测试文件保存在: test_fixed_results/")
    print(f"💡 提示: 对比原始测试图片和处理后图片，验证背景颜色填充效果")

if __name__ == "__main__":
    main() 