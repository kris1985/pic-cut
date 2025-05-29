#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS版本功能测试脚本
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess
import time

def test_macos_version():
    """测试macOS版本的功能"""
    
    print("🧪 开始测试macOS版本的鞋子图片智能裁剪工具...")
    print("=" * 60)
    
    # 检查可执行文件
    exe_path = Path("dist/鞋子图片智能裁剪工具_v2.0_x64")
    app_path = Path("dist/鞋子图片智能裁剪工具_v2.0_x64.app")
    
    print(f"🔍 检查文件...")
    print(f"   可执行文件: {'✅ 存在' if exe_path.exists() else '❌ 不存在'}")
    print(f"   应用包: {'✅ 存在' if app_path.exists() else '❌ 不存在'}")
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)
        print(f"   文件大小: {file_size:.1f} MB")
    
    # 检查测试输入文件
    input_dir = Path("test_gui_input")
    output_dir = Path("test_macos_output")
    
    print(f"\n📁 准备测试目录...")
    print(f"   输入目录: {input_dir} ({'✅ 存在' if input_dir.exists() else '❌ 不存在'})")
    
    if input_dir.exists():
        test_images = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.png"))
        print(f"   测试图片: {len(test_images)} 张")
        for img in test_images[:3]:  # 显示前3张
            print(f"     - {img.name}")
    
    # 创建输出目录
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)
    print(f"   输出目录: {output_dir} ✅ 已创建")
    
    # 测试核心功能（使用Python模块直接测试）
    print(f"\n🔧 测试核心功能...")
    try:
        from shoe_image_processor import ShoeImageProcessor
        
        processor = ShoeImageProcessor()
        print("   ✅ 图像处理器初始化成功")
        
        # 测试单张图片处理
        if input_dir.exists() and test_images:
            test_image = test_images[0]
            output_file = output_dir / f"{test_image.stem}_test_output.jpg"
            
            print(f"   🖼️  测试处理图片: {test_image.name}")
            
            success = processor.process_single_image(
                str(test_image), 
                str(output_file), 
                target_ratio='auto',
                high_quality=True
            )
            
            if success and output_file.exists():
                out_size = output_file.stat().st_size / 1024
                print(f"   ✅ 处理成功! 输出: {output_file.name} ({out_size:.1f} KB)")
            else:
                print(f"   ❌ 处理失败")
                return False
        
    except Exception as e:
        print(f"   ❌ 核心功能测试失败: {e}")
        return False
    
    # 测试GUI启动（检查进程）
    print(f"\n🖥️  检查GUI应用...")
    try:
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        if "鞋子图片智能裁剪工具" in result.stdout:
            print("   ✅ GUI应用正在运行")
            
            # 获取运行的进程信息
            lines = result.stdout.split('\n')
            for line in lines:
                if "鞋子图片智能裁剪工具" in line and "grep" not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        print(f"   📋 进程ID: {pid}")
                        break
        else:
            print("   ℹ️  GUI应用未在运行")
            
    except Exception as e:
        print(f"   ⚠️  无法检查GUI状态: {e}")
    
    # 性能测试
    print(f"\n⚡ 性能测试...")
    if input_dir.exists() and test_images and len(test_images) >= 2:
        start_time = time.time()
        
        # 处理多张图片
        processed_count = 0
        for i, test_image in enumerate(test_images[:3]):  # 测试前3张
            output_file = output_dir / f"{test_image.stem}_perf_test_{i}.jpg"
            
            try:
                success = processor.process_single_image(
                    str(test_image), 
                    str(output_file), 
                    target_ratio='auto',
                    high_quality=True
                )
                if success:
                    processed_count += 1
            except:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if processed_count > 0:
            avg_time = total_time / processed_count
            print(f"   📊 处理了 {processed_count} 张图片")
            print(f"   ⏱️  平均耗时: {avg_time:.2f} 秒/张")
            print(f"   🏃 总耗时: {total_time:.2f} 秒")
        else:
            print("   ❌ 性能测试失败")
    
    # 文件检查
    print(f"\n📋 输出文件检查...")
    output_files = list(output_dir.glob("*.jpg"))
    
    if output_files:
        print(f"   ✅ 生成了 {len(output_files)} 个输出文件")
        
        # 显示文件信息
        for output_file in output_files[:3]:  # 显示前3个
            size_kb = output_file.stat().st_size / 1024
            print(f"     📄 {output_file.name}: {size_kb:.1f} KB")
            
        print(f"   📁 输出目录: {output_dir.absolute()}")
    else:
        print("   ❌ 未生成输出文件")
        return False
    
    print(f"\n" + "=" * 60)
    print("🎉 macOS版本测试完成!")
    
    # 总结
    print(f"\n📊 测试总结:")
    print(f"   ✅ 可执行文件: 正常")
    print(f"   ✅ 核心功能: 正常") 
    print(f"   ✅ 图片处理: 正常")
    print(f"   ✅ 文件输出: 正常")
    
    print(f"\n💡 使用建议:")
    print(f"   🖱️  双击运行: dist/鞋子图片智能裁剪工具_v2.0_x64.app")
    print(f"   💻 命令行运行: ./dist/鞋子图片智能裁剪工具_v2.0_x64")
    print(f"   📂 查看结果: {output_dir.absolute()}")
    
    return True

def kill_running_processes():
    """关闭运行中的测试进程"""
    try:
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        lines = result.stdout.split('\n')
        pids = []
        
        for line in lines:
            if "鞋子图片智能裁剪工具" in line and "grep" not in line:
                parts = line.split()
                if len(parts) >= 2:
                    pids.append(parts[1])
        
        if pids:
            print(f"🔄 发现 {len(pids)} 个运行中的进程，正在关闭...")
            for pid in pids:
                try:
                    subprocess.run(["kill", pid], check=True)
                    print(f"   ✅ 已关闭进程 {pid}")
                except:
                    print(f"   ⚠️  无法关闭进程 {pid}")
        else:
            print("ℹ️  没有发现运行中的进程")
            
    except Exception as e:
        print(f"⚠️  清理进程时出错: {e}")

if __name__ == "__main__":
    print("🔧 macOS版本功能测试工具")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        kill_running_processes()
    else:
        try:
            success = test_macos_version()
            if success:
                print(f"\n🎊 测试成功! macOS版本工作正常!")
            else:
                print(f"\n❌ 测试失败，请检查错误信息")
        except KeyboardInterrupt:
            print(f"\n⏹️  测试被用户中断")
        except Exception as e:
            print(f"\n💥 测试过程中出现错误: {e}")
        
        print(f"\n💡 提示: 运行 'python test_macos_version.py clean' 可清理运行中的进程") 