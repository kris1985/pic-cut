#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
from pathlib import Path

def merge_md_files(source_dir="content", output_file="merged_content.md"):
    """
    合并指定目录下的所有Markdown文件到一个文件中
    
    Args:
        source_dir: 源目录，包含要合并的.md文件
        output_file: 输出文件名
    """
    
    # 检查源目录是否存在
    if not os.path.exists(source_dir):
        print(f"错误：目录 {source_dir} 不存在")
        return
    
    # 获取所有.md文件并排序
    md_files = glob.glob(os.path.join(source_dir, "*.md"))
    md_files.sort()  # 按文件名排序
    
    if not md_files:
        print(f"在目录 {source_dir} 中没有找到.md文件")
        return
    
    print(f"找到 {len(md_files)} 个Markdown文件")
    print("开始合并...")
    
    merged_content = []
    
    for i, file_path in enumerate(md_files):
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 添加内容到合并列表
            merged_content.append(content)
            
            # 获取文件名用于显示进度
            filename = os.path.basename(file_path)
            print(f"✓ 已读取: {filename}")
            
        except Exception as e:
            print(f"✗ 读取文件 {file_path} 时出错: {e}")
            continue
    
    # 用空行连接所有内容
    final_content = "\n\n".join(merged_content)
    
    # 写入合并后的文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"\n✅ 成功合并 {len(merged_content)} 个文件")
        print(f"📄 合并后的文件: {os.path.abspath(output_file)}")
        print(f"📊 总字符数: {len(final_content)}")
        
    except Exception as e:
        print(f"❌ 写入文件时出错: {e}")

def main():
    print("=== Markdown文件合并工具 ===")
    print("将content目录中的所有.md文件合并为一个文件")
    print("-" * 50)
    
    # 执行合并
    merge_md_files("content", "merged_content.md")

if __name__ == "__main__":
    main() 