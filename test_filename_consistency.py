#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件名一致性功能
验证输出文件名与源文件名保持一致
"""

import os
import tempfile
import shutil
from pathlib import Path
from shoe_image_processor import ShoeImageProcessor

def test_filename_consistency():
    """测试文件名保持一致性"""
    print("🧪 测试文件名一致性功能...")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        output_dir = temp_path / "output"
        
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 使用测试图片
        test_image = "sample_shoe.jpg"
        if os.path.exists(test_image):
            # 复制测试图片到输入目录，使用不同的文件名
            test_files = [
                "红色运动鞋.jpg",
                "黑色皮鞋.jpg", 
                "白色帆布鞋.jpg",
                "测试图片_001.jpg"
            ]
            
            print(f"📁 准备测试文件...")
            for filename in test_files:
                shutil.copy2(test_image, input_dir / filename)
                print(f"   ✅ 创建: {filename}")
            
            # 执行批量处理
            print(f"\n🔄 执行批量处理...")
            processor = ShoeImageProcessor()
            stats = processor.process_batch(
                str(input_dir), 
                str(output_dir), 
                target_ratio='auto',
                high_quality=True
            )
            
            # 验证文件名一致性
            print(f"\n✅ 验证文件名一致性...")
            all_consistent = True
            
            for input_file in input_dir.iterdir():
                if input_file.is_file() and input_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    expected_output = output_dir / input_file.name
                    
                    # 考虑可能的格式转换
                    possible_outputs = [
                        output_dir / input_file.name,  # 原名
                        output_dir / (input_file.stem + '.jpg'),  # 转为JPEG
                        output_dir / (input_file.stem + '.jpeg'), # 转为JPEG
                    ]
                    
                    found_output = None
                    for possible_output in possible_outputs:
                        if possible_output.exists():
                            found_output = possible_output
                            break
                    
                    if found_output:
                        # 检查文件名是否一致（忽略可能的格式转换）
                        input_stem = input_file.stem
                        output_stem = found_output.stem
                        
                        if input_stem == output_stem:
                            print(f"   ✅ {input_file.name} -> {found_output.name} (文件名保持一致)")
                        else:
                            print(f"   ❌ {input_file.name} -> {found_output.name} (文件名不一致)")
                            all_consistent = False
                    else:
                        print(f"   ❌ {input_file.name} -> 未找到输出文件")
                        all_consistent = False
            
            # 输出测试结果
            print(f"\n📊 测试统计:")
            print(f"   总计处理: {stats['total']} 个文件")
            print(f"   成功处理: {stats['successful']} 个文件")
            print(f"   失败处理: {stats['failed']} 个文件")
            print(f"   成功率: {stats['success_rate']:.1%}")
            
            if all_consistent and stats['successful'] == stats['total']:
                print(f"\n🎉 测试通过！所有文件名保持一致且处理成功")
                return True
            else:
                print(f"\n❌ 测试失败！")
                if not all_consistent:
                    print("   - 存在文件名不一致的情况")
                if stats['failed'] > 0:
                    print(f"   - 有 {stats['failed']} 个文件处理失败")
                return False
        else:
            print(f"❌ 测试图片 '{test_image}' 不存在，无法进行测试")
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("  文件名一致性测试")
    print("=" * 60)
    
    success = test_filename_consistency()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！文件名一致性功能正常工作")
    else:
        print("❌ 测试失败！请检查代码")
    print("=" * 60)

if __name__ == "__main__":
    main() 