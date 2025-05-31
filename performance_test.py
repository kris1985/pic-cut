#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
测试快速模式和精确模式的性能差异
"""

import time
from shoe_image_processor import ShoeImageProcessor
from PIL import Image
import numpy as np

def test_performance():
    """测试性能优化效果"""
    print("🚀 图片处理性能测试")
    print("=" * 50)
    
    # 创建一个测试图片
    test_image = Image.fromarray(np.random.randint(0, 255, (1200, 900, 3), dtype=np.uint8))
    
    processor = ShoeImageProcessor()
    
    # 测试背景颜色检测性能
    print("📊 背景颜色检测性能测试:")
    
    # 测试快速模式
    print("   测试快速模式...")
    start_time = time.time()
    bg_color_fast = processor.detect_background_color(test_image, fast_mode=True)
    fast_time = time.time() - start_time
    
    # 测试精确模式
    print("   测试精确模式...")
    start_time = time.time()
    bg_color_precise = processor.detect_background_color(test_image, fast_mode=False)
    precise_time = time.time() - start_time
    
    print(f"   快速模式用时: {fast_time:.3f}秒")
    print(f"   精确模式用时: {precise_time:.3f}秒")
    print(f"   性能提升: {precise_time/fast_time:.1f}倍")
    print(f"   快速模式检测颜色: RGB{bg_color_fast}")
    print(f"   精确模式检测颜色: RGB{bg_color_precise}")
    
    # 测试对象边界检测性能
    print("\n📊 对象边界检测性能测试:")
    
    # 快速模式的find_object_bounds
    print("   测试优化后的边界检测...")
    start_time = time.time()
    bounds_optimized = processor.find_object_bounds(test_image)
    optimized_time = time.time() - start_time
    
    print(f"   优化后检测用时: {optimized_time:.3f}秒")
    print(f"   检测到的边界: {bounds_optimized}")
    
    print("\n✅ 性能测试完成！")
    print(f"💡 背景颜色检测性能提升: {precise_time/fast_time:.1f}倍")
    print("💡 对象检测算法已优化，移除了耗时的颜色聚类步骤")

if __name__ == "__main__":
    test_performance() 