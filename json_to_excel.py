import pandas as pd
import json

# 读取JSON文件
with open('qa/软件基础构成_qa.json', 'r', encoding='utf-8') as f:
    qa_pairs = json.load(f)

# 创建新的DataFrame
excel_path = '/Users/taohuang/Desktop/问答对格式知识文档模板.xlsx'
df_new = pd.DataFrame(columns=['问题', '答案', '相似问法'])

# 添加填写须知行
df_new.loc[0] = ['填写须知', '填写须知', '填写须知']

# 映射数据到对应列
for i, qa in enumerate(qa_pairs, start=1):
    df_new.loc[i, '问题'] = qa['question']
    df_new.loc[i, '答案'] = qa['answer']
    df_new.loc[i, '相似问法'] = ''

# 写入Excel文件
df_new.to_excel(excel_path, index=False, engine='openpyxl')

print(f"Excel文件已保存到: {excel_path}") 