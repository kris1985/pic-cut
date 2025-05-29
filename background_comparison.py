#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景移除方法对比工具

对比当前基础方法和改进方法的效果差异
"""

import os
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def compare_background_removal_results():
    """
    对比不同背景移除方法的效果
    """
    print("=== 背景移除方法对比分析 ===\n")
    
    # 检查生成的结果文件
    files = {
        '原图': './sample_shoe.jpg',
        '基础方法': './bg_removed_basic.jpg',
        '增强方法': './bg_removed_enhanced.jpg', 
        '自适应方法': './bg_removed_adaptive.jpg'
    }
    
    # 1. 文件大小对比
    print("📊 文件信息对比:")
    print("-" * 60)
    
    for name, path in files.items():
        if os.path.exists(path):
            # 获取文件大小
            size_bytes = os.path.getsize(path)
            size_mb = size_bytes / 1024 / 1024
            
            # 获取图像信息
            with Image.open(path) as img:
                width, height = img.size
                pixels = width * height
                
            print(f"{name:8s}: {width:4d}x{height:4d} | {pixels:7,}像素 | {size_mb:5.2f}MB")
        else:
            print(f"{name:8s}: 文件不存在")
    
    print()
    
    # 2. 处理质量分析
    if all(os.path.exists(path) for path in files.values()):
        print("🔍 处理质量分析:")
        print("-" * 60)
        
        # 分析每种方法的特点
        methods_analysis = {
            '基础方法': {
                '优点': ['处理速度快', '内存占用低', '稳定性好'],
                '缺点': ['边缘可能有锯齿', '小噪声点', '背景颜色固定'],
                '适用': '大批量快速处理'
            },
            '增强方法': {
                '优点': ['边缘更平滑', '噪声更少', '可自定义背景'],
                '缺点': ['处理时间稍长', '内存占用稍高'],
                '适用': '质量要求较高的场景'
            },
            '自适应方法': {
                '优点': ['智能选择策略', '兼顾质量和效率', '自动优化'],
                '缺点': ['逻辑稍复杂', '需要特征分析'],
                '适用': '混合场景的智能处理'
            }
        }
        
        for method, analysis in methods_analysis.items():
            print(f"\n{method}:")
            print(f"  ✅ 优点: {', '.join(analysis['优点'])}")
            print(f"  ⚠️  缺点: {', '.join(analysis['缺点'])}")
            print(f"  🎯 适用: {analysis['适用']}")
    
    print()
    
    # 3. 使用建议
    print("💡 使用建议:")
    print("-" * 60)
    print("""
📋 选择指南:

🚀 快速批量处理:
   → 使用基础方法
   → 速度优先，质量可接受
   
🎨 高质量单图处理:
   → 使用增强方法
   → 质量优先，可接受稍慢的速度
   
🧠 智能混合处理:
   → 使用自适应方法  
   → 自动根据图像特征选择最佳策略

⚙️ 参数建议:
   - 电商产品图: 增强方法 + isnet-general-use模型
   - 社交媒体: 基础方法 + u2net模型
   - 大批量处理: 基础方法 + silueta模型
   - 混合场景: 自适应方法 + u2net模型
""")

def create_visual_comparison():
    """
    创建可视化对比图
    """
    files = {
        '原图': './sample_shoe.jpg',
        '基础方法': './bg_removed_basic.jpg',
        '增强方法': './bg_removed_enhanced.jpg',
        '自适应方法': './bg_removed_adaptive.jpg'
    }
    
    # 检查文件是否存在
    existing_files = {name: path for name, path in files.items() if os.path.exists(path)}
    
    if len(existing_files) < 2:
        print("⚠️ 需要至少2个图片文件才能进行对比")
        return
    
    # 创建对比图
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('背景移除方法对比', fontsize=16, fontweight='bold')
    
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    
    for i, (name, path) in enumerate(existing_files.items()):
        if i >= 4:  # 最多显示4张图
            break
            
        row, col = positions[i]
        ax = axes[row, col]
        
        # 加载并显示图像
        img = Image.open(path)
        ax.imshow(img)
        ax.set_title(name, fontsize=12, fontweight='bold')
        ax.axis('off')
        
        # 添加边框
        if name != '原图':
            rect = patches.Rectangle((0, 0), img.width-1, img.height-1, 
                                   linewidth=2, edgecolor='green', facecolor='none')
            ax.add_patch(rect)
    
    # 隐藏多余的子图
    for i in range(len(existing_files), 4):
        row, col = positions[i]
        axes[row, col].axis('off')
    
    plt.tight_layout()
    plt.savefig('background_removal_comparison.png', dpi=150, bbox_inches='tight')
    print("📊 可视化对比图已保存: background_removal_comparison.png")
    
    # 显示图像（如果支持）
    try:
        plt.show()
    except:
        print("💡 提示: 在支持图形界面的环境中可以直接显示对比图")

def analyze_current_method():
    """
    分析当前实现的背景移除方法
    """
    print("🔬 当前方法技术分析:")
    print("-" * 60)
    
    analysis = """
📋 当前实现 (shoe_image_processor.py):

1️⃣ AI模型: rembg库
   • 使用预训练的深度学习模型
   • 支持u2net, silueta, isnet-general-use
   • 输出带alpha通道的RGBA图像

2️⃣ 背景处理:
   • 固定白色背景 (255, 255, 255, 255)
   • 使用PIL的alpha_composite合成
   • 转换为RGB模式输出

3️⃣ 工作流程:
   step1: remove(image, session=self.session)
   step2: Image.new('RGBA', result.size, (255, 255, 255, 255))
   step3: Image.alpha_composite(white_bg, result)
   step4: final_image.convert('RGB')

✅ 优势:
   • 实现简单，代码清晰
   • 处理速度较快
   • 内存占用适中
   • 稳定性良好

❌ 局限:
   • 边缘可能有锯齿
   • 没有噪声后处理
   • 背景颜色固定
   • 缺乏质量评估
   • 无自适应优化

🚀 改进方向:
   • 边缘平滑处理
   • 形态学噪声去除
   • 自定义背景颜色
   • 图像质量评估
   • 自适应处理策略
"""
    
    print(analysis)

if __name__ == "__main__":
    # 运行完整的对比分析
    analyze_current_method()
    print()
    compare_background_removal_results()
    print()
    
    # 创建可视化对比
    try:
        create_visual_comparison()
    except Exception as e:
        print(f"⚠️ 创建可视化对比时出错: {e}")
        print("💡 可能需要安装matplotlib: pip install matplotlib") 