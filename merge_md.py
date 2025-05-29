import os
import glob

def merge_markdown_files():
    # 获取content目录下所有.md文件
    md_files = glob.glob('content/*.md')
    
    if not md_files:
        print("没有找到.md文件")
        return
        
    # 合并内容
    merged_content = []
    for md_file in sorted(md_files):  # 按文件名排序
        print(f"正在处理: {md_file}")
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            merged_content.append(content)
    
    # 使用5个中划线连接内容
    final_content = '\n\n-----\n\n'.join(merged_content)
    
    # 保存合并后的文件
    output_file = 'content/merged_content.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"\n合并完成! 文件已保存到: {output_file}")

if __name__ == '__main__':
    merge_markdown_files() 