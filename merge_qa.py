import os
import glob
import json

def merge_qa_files():
    # 获取qa目录下所有.json文件
    json_files = glob.glob('qa/*.json')
    
    if not json_files:
        print("没有找到.json文件")
        return
        
    # 合并内容
    all_qa_pairs = []
    for json_file in sorted(json_files):  # 按文件名排序
        print(f"正在处理: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
            all_qa_pairs.extend(qa_pairs)
    
    # 转换为markdown格式
    markdown_content = []
    for qa in all_qa_pairs:
        answer = qa['answer']
        if '--- 文档来源' in answer:
            answer_main, doc_source = answer.split('--- 文档来源', 1)
            answer_main = answer_main.strip()
            doc_source = doc_source.strip()
            qa_content = f"Q: {qa['question']}\nA: {answer_main}\n文档来源: {doc_source}"
        else:
            qa_content = f"Q: {qa['question']}\nA: {answer.strip()}"
        markdown_content.append(qa_content)
    
    # 使用\n\n连接所有QA对
    final_content = '\n\n'.join(markdown_content)
    
    # 保存合并后的文件
    output_file = 'qa/merged_qa.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"\n合并完成! 文件已保存到: {output_file}")

if __name__ == '__main__':
    merge_qa_files() 