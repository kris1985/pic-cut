import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html2text
import json

class CMSCrawler:
    def __init__(self):
        self.base_url = "https://cms-docs.shengyc.com"
        self.target_url = "https://cms-docs.shengyc.com/cms/tutorial/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8/%E8%BD%AF%E4%BB%B6%E5%9F%BA%E7%A1%80%E6%9E%84%E6%88%90"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.setup_directories()
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0  # 不限制行宽
        
        # API配置
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.api_key = "8c6363ef-d7c7-40ff-9216-f6c7df02cf33"
        self.model = "doubao-1-5-pro-256k-250115"

    def setup_directories(self):
        """创建必要的目录"""
        os.makedirs("content", exist_ok=True)
        os.makedirs("qa", exist_ok=True)

    def get_page_content(self):
        """获取页面内容"""
        try:
            response = requests.get(self.target_url, headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"获取页面失败: {e}")
            return None

    def clean_content(self, soup):
        """清理内容,移除不需要的元素"""
        # 移除导航栏
        for nav in soup.find_all('nav'):
            nav.decompose()
            
        # 移除页脚
        for footer in soup.find_all('footer'):
            footer.decompose()
            
        # 移除目录
        for toc in soup.find_all('div', class_='tableOfContents'):
            toc.decompose()
            
        # 移除编辑按钮
        for edit in soup.find_all('a', class_='theme-edit-this-page'):
            edit.decompose()
            
        # 移除面包屑导航
        for breadcrumb in soup.find_all('nav', class_='theme-doc-breadcrumbs'):
            breadcrumb.decompose()
            
        # 移除版本标签
        for badge in soup.find_all('span', class_='theme-doc-version-badge'):
            badge.decompose()
            
        # 移除分页导航
        for pagination in soup.find_all('nav', class_='pagination-nav'):
            pagination.decompose()
            
        # 移除所有图片
        for img in soup.find_all('img'):
            img.decompose()
            
        return soup

    def extract_core_content(self, soup):
        """提取核心内容"""
        # 创建一个新的BeautifulSoup对象来存储核心内容
        core_content = BeautifulSoup('', 'lxml')
        
        # 添加标题
        title = soup.find('h1')
        if title:
            core_content.append(title)
        
        # 查找主要内容区域
        main_content = soup.find('div', class_='theme-doc-markdown')
        if main_content:
            # 清理内容
            main_content = self.clean_content(main_content)
            # 复制主要内容
            core_content.append(main_content)
        
        return core_content

    def generate_qa_pairs(self, content):
        """使用大模型生成QA对"""
        try:
            prompt = f"""请根据以下文档内容生成10个问答对。要求：
1. 问题要具体且有针对性
2. 答案要准确、完整
3. 问答对要覆盖文档的主要内容
4. 格式为JSON数组，每个元素包含question和answer字段
5. 在每个answer的最后添加文档来源URL: {self.target_url}
6. 使用"---"作为answer内容和URL的分隔符
7. URL格式为: "文档来源: [URL]"
8. answer和URL之间只用一个空格分隔

文档内容：
{content}

请生成问答对："""

            # 打印API配置信息
            print("\n=== API配置 ===")
            print(f"API地址: {self.api_url}")
            print(f"API密钥: {self.api_key}")
            print(f"模型名称: {self.model}")
            
            # 准备请求参数
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的文档问答对生成助手。"},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # 打印请求参数
            print("\n=== 请求参数 ===")
            print(json.dumps(data, ensure_ascii=False, indent=2))

            # 调用API
            print("\n=== 开始调用API ===")
            response = requests.post(self.api_url, headers=headers, json=data)
            
            # 打印响应信息
            print("\n=== API响应 ===")
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            # 检查响应状态
            if response.status_code == 200:
                response_data = response.json()
                # 解析返回的JSON字符串
                qa_pairs = json.loads(response_data["choices"][0]["message"]["content"])
                
                # 确保每个answer都包含URL
                for qa in qa_pairs:
                    if "---" not in qa["answer"]:
                        qa["answer"] = f"{qa['answer']} --- 文档来源: {self.target_url}"
                    else:
                        # 如果已经有URL,但格式不对,则修改格式
                        answer, url = qa["answer"].split("---")
                        # 清理URL中的重复文本
                        url = url.replace("文档来源:", "").strip()
                        url = url.replace("[", "").replace("]", "").strip()
                        qa["answer"] = f"{answer.strip()} --- 文档来源: {url}"
                
                return qa_pairs
            else:
                print(f"API调用失败,状态码: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"\n=== API调用失败 ===")
            print(f"错误信息: {e}")
            return []

    def process_content(self, html_content):
        """处理页面内容"""
        if not html_content:
            return

        soup = BeautifulSoup(html_content, 'lxml')
        
        # 获取标题
        title = soup.find('h1')
        if title:
            title = title.text.strip()
        else:
            title = "未命名文档"

        # 提取核心内容
        core_content = self.extract_core_content(soup)

        # 转换为Markdown
        markdown_content = self.h2t.handle(str(core_content))

        # 添加来源地址
        source_text = f"\n\n---\n\n该文档地址来源：{self.target_url}"
        markdown_content += source_text

        # 保存处理后的Markdown内容
        content_path = os.path.join("content", f"{title}.md")
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"内容保存成功: {content_path}")

        # 生成QA对
        print("正在生成QA对...")
        qa_pairs = self.generate_qa_pairs(markdown_content)
        
        # 保存QA对
        qa_path = os.path.join("qa", f"{title}_qa.json")
        with open(qa_path, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        print(f"QA对保存成功: {qa_path}")

    def run(self):
        """运行爬虫"""
        print("开始爬取页面...")
        html_content = self.get_page_content()
        if html_content:
            self.process_content(html_content)
            print("爬取完成!")
        else:
            print("爬取失败!")

if __name__ == "__main__":
    crawler = CMSCrawler()
    crawler.run() 