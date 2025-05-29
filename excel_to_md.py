#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import re
from pathlib import Path

def clean_filename(filename):
    """清理文件名，移除不合法的字符"""
    # 移除或替换不合法的文件名字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除多余的空格
    filename = re.sub(r'\s+', ' ', filename).strip()
    # 限制文件名长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def excel_to_md(excel_path, output_dir="content"):
    """
    读取Excel文件并生成Markdown文件
    
    Args:
        excel_path: Excel文件路径
        output_dir: 输出目录
    """
    
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # 读取Excel文件
        print(f"正在读取Excel文件: {excel_path}")
        df = pd.read_excel(excel_path)
        
        # 打印列名以便调试
        print(f"Excel文件列名: {list(df.columns)}")
        print(f"共有 {len(df)} 行数据")
        
        # 假设列名分别是：视频标题、关键词、B站链接、官方视频号链接
        # 根据实际情况可能需要调整列名
        title_col = df.columns[2]  # 第三列：视频标题/内容
        keywords_col = df.columns[3]  # 第四列：关键词
        weixin_link_col = df.columns[4]  # 第五列：视频号链接
        bilibili_link_col = df.columns[5]  # 第六列：B站链接
        
        success_count = 0
        
        # 遍历每一行数据
        for index, row in df.iterrows():
            try:
                # 获取数据
                title = str(row[title_col]).strip() if pd.notna(row[title_col]) else f"视频{index+1}"
                keywords = str(row[keywords_col]).strip() if pd.notna(row[keywords_col]) else ""
                bilibili_link = str(row[bilibili_link_col]).strip() if pd.notna(row[bilibili_link_col]) else ""
                weixin_link = str(row[weixin_link_col]).strip() if weixin_link_col and pd.notna(row[weixin_link_col]) else ""
                
                # 跳过空行
                if title == "nan" or title == "":
                    continue
                
                # 生成文件名 - 从1005开始编号
                file_number = 1005 + index
                clean_title = clean_filename(title)
                filename = f"{file_number}-{clean_title}.md"
                filepath = os.path.join(output_dir, filename)
                
                # 生成Markdown内容
                md_content = f"""视频标题：{title}
关键字：{keywords}
B站链接：{bilibili_link}"""
                
                # 如果有微信视频号链接，则添加
                if weixin_link and weixin_link != "nan":
                    md_content += f"\n官方视频号链接（仅支持手机端打开）：{weixin_link}"
                
                # 写入文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                print(f"✓ 已生成: {filename}")
                success_count += 1
                
            except Exception as e:
                print(f"✗ 处理第 {index+1} 行时出错: {e}")
                continue
        
        print(f"\n完成！成功生成 {success_count} 个Markdown文件")
        print(f"文件保存在: {os.path.abspath(output_dir)}")
        
    except FileNotFoundError:
        print(f"错误：找不到Excel文件 {excel_path}")
    except Exception as e:
        print(f"错误：{e}")

def main():
    # Excel文件路径
    excel_path = "/Users/taohuang/Desktop/1产品教程+案例视频清单的副本.xlsx"
    
    # 输出目录
    output_dir = "content"
    
    print("=== Excel转Markdown工具 ===")
    print(f"Excel文件: {excel_path}")
    print(f"输出目录: {output_dir}")
    print("-" * 50)
    
    # 执行转换
    excel_to_md(excel_path, output_dir)

if __name__ == "__main__":
    main() 