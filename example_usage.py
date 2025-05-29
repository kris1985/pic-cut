#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鞋子图片处理工具使用示例
"""

from shoe_image_processor import ShoeImageProcessor
import os

def simple_batch_process():
    """简单的批量处理示例"""
    
    # 设置输入和输出目录
    input_directory = "input_images"  # 放置原始鞋子图片的目录
    output_directory = "processed_images"  # 处理后图片保存的目录
    
    # 创建输入目录（如果不存在）
    os.makedirs(input_directory, exist_ok=True)
    
    print("🏃‍♂️ 鞋子图片批量处理工具")
    print("=" * 50)
    print(f"📁 输入目录: {input_directory}")
    print(f"📁 输出目录: {output_directory}")
    print()
    
    # 检查输入目录是否有图片
    if not os.listdir(input_directory):
        print(f"⚠️  输入目录 '{input_directory}' 为空")
        print("请将需要处理的鞋子图片放入该目录中，支持的格式:")
        print("   - JPG/JPEG")
        print("   - PNG")
        print("   - BMP")
        print("   - TIFF")
        print("   - WEBP")
        return
    
    try:
        # 创建处理器
        print("🔧 初始化图片处理器...")
        processor = ShoeImageProcessor(model_name='u2net')
        
        # 批量处理
        print("🚀 开始批量处理...")
        stats = processor.process_batch(
            input_dir=input_directory,
            output_dir=output_directory,
            target_ratio='auto'  # 自动选择最适合的比例
        )
        
        # 显示结果
        print("\n" + "=" * 50)
        print("✅ 批量处理完成!")
        print(f"📊 处理统计:")
        print(f"   🔢 总计: {stats['total']} 张")
        print(f"   ✅ 成功: {stats['successful']} 张")
        print(f"   ❌ 失败: {stats['failed']} 张")
        print(f"   📈 成功率: {stats['success_rate']:.1%}")
        print(f"📁 处理后的图片保存在: {output_directory}")
        
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")


def process_single_image_example():
    """单张图片处理示例"""
    
    input_file = "sample_shoe.jpg"  # 输入图片路径
    output_file = "processed_shoe.jpg"  # 输出图片路径
    
    if not os.path.exists(input_file):
        print(f"⚠️  找不到图片文件: {input_file}")
        return
    
    try:
        print("🔧 初始化图片处理器...")
        processor = ShoeImageProcessor()
        
        print(f"🚀 处理图片: {input_file}")
        success = processor.process_single_image(
            input_path=input_file,
            output_path=output_file,
            target_ratio='4:3'  # 指定横图比例
        )
        
        if success:
            print(f"✅ 图片处理成功! 保存为: {output_file}")
        else:
            print("❌ 图片处理失败!")
            
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")


if __name__ == "__main__":
    print("选择处理模式:")
    print("1. 批量处理目录中的所有图片")
    print("2. 处理单张图片")
    
    choice = input("请输入选项 (1 或 2): ").strip()
    
    if choice == "1":
        simple_batch_process()
    elif choice == "2":
        process_single_image_example()
    else:
        print("无效选项，默认使用批量处理模式")
        simple_batch_process() 