#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试边距模式功能
确保鞋子左右边距各占12.5%，必要时扩展白色画布
"""

import os
import sys
from pathlib import Path
from PIL import Image
from shoe_image_processor import ShoeImageProcessor

def test_margin_mode():
    """测试边距模式功能"""
    processor = ShoeImageProcessor()
    
    # 创建测试目录
    test_input_dir = Path("test_margin_input")
    test_output_dir = Path("test_margin_output")
    
    test_input_dir.mkdir(exist_ok=True)
    test_output_dir.mkdir(exist_ok=True)
    
    print("🧪 边距模式测试")
    print("=" * 50)
    
    # 查找测试图片
    test_images = []
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        test_images.extend(Path('.').glob(f"*{ext}"))
        test_images.extend(Path('.').glob(f"*{ext.upper()}"))
    
    # 过滤掉一些可能的结果文件
    test_images = [img for img in test_images if 'test_' not in img.name.lower() 
                   and 'output' not in img.name.lower() 
                   and 'result' not in img.name.lower()]
    
    if not test_images:
        print("❌ 未找到测试图片")
        return
    
    # 选择前几张图片进行测试
    test_images = test_images[:3]
    
    print(f"📁 找到 {len(test_images)} 张测试图片")
    
    for i, image_path in enumerate(test_images, 1):
        print(f"\n🖼️  测试图片 {i}: {image_path.name}")
        
        try:
            # 复制到测试输入目录
            test_input_path = test_input_dir / image_path.name
            if not test_input_path.exists():
                import shutil
                shutil.copy2(image_path, test_input_path)
            
            # 处理图片 - 使用边距模式
            output_path = test_output_dir / f"margin_mode_{image_path.name}"
            
            success = processor.process_single_image(
                str(test_input_path), 
                str(output_path), 
                target_ratio='auto',
                high_quality=True,
                preserve_resolution=False,
                use_margin_mode=True
            )
            
            if success:
                print(f"✅ 处理成功: {output_path.name}")
                
                # 验证结果
                with Image.open(output_path) as result_img:
                    # 重新检测鞋子边界来验证边距
                    left, top, right, bottom = processor.find_object_bounds(result_img)
                    
                    canvas_width = result_img.width
                    left_margin_ratio = left / canvas_width
                    right_margin_ratio = (canvas_width - right) / canvas_width
                    
                    print(f"   📏 画布尺寸: {result_img.width}x{result_img.height}")
                    print(f"   📐 鞋子边界: 左{left}, 右{right}")
                    print(f"   📊 左边距: {left_margin_ratio:.1%}, 右边距: {right_margin_ratio:.1%}")
                    print(f"   🎯 目标边距: 12.5%")
                    
                    # 检查边距是否接近目标值
                    target_margin = 0.125
                    left_diff = abs(left_margin_ratio - target_margin)
                    right_diff = abs(right_margin_ratio - target_margin)
                    
                    if left_diff < 0.03 and right_diff < 0.03:  # 允许3%的误差
                        print(f"   ✅ 边距符合要求 (误差 < 3%)")
                    else:
                        print(f"   ⚠️  边距偏差较大: 左{left_diff:.1%}, 右{right_diff:.1%}")
            else:
                print(f"❌ 处理失败: {image_path.name}")
                
        except Exception as e:
            print(f"❌ 处理错误: {e}")
    
    print(f"\n🎉 测试完成!")
    print(f"📁 结果保存在: {test_output_dir}")
    print("\n💡 使用说明:")
    print("1. 检查输出图片是否鞋子居中")
    print("2. 验证左右边距是否接近12.5%")
    print("3. 观察是否正确扩展了白色画布")

def test_comparison():
    """对比测试：边距模式 vs 传统模式"""
    processor = ShoeImageProcessor()
    
    # 查找一张测试图片
    test_images = []
    for ext in ['.jpg', '.jpeg', '.png']:
        test_images.extend(Path('.').glob(f"*{ext}"))
    
    test_images = [img for img in test_images if 'test_' not in img.name.lower()]
    
    if not test_images:
        print("❌ 未找到测试图片")
        return
    
    test_image = test_images[0]
    print(f"🔄 对比测试使用图片: {test_image.name}")
    
    # 传统模式
    traditional_output = f"traditional_mode_{test_image.name}"
    processor.process_single_image(
        str(test_image), 
        traditional_output, 
        use_margin_mode=False
    )
    
    # 边距模式
    margin_output = f"margin_mode_{test_image.name}"
    processor.process_single_image(
        str(test_image), 
        margin_output, 
        use_margin_mode=True
    )
    
    print(f"✅ 对比测试完成!")
    print(f"📁 传统模式结果: {traditional_output}")
    print(f"📁 边距模式结果: {margin_output}")
    print("🔍 请对比两张图片的效果差异")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        test_comparison()
    else:
        test_margin_mode() 