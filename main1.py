import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html2text

class CMSCrawler:
    def __init__(self, target_urls=None, output_dir="content"):
        self.base_url = "https://cms-docs.shengyc.com"
        # 支持多个目标URL
        if target_urls is not None:
            self.target_urls = target_urls
        else:
            self.target_urls = [
                "https://cms-docs.shengyc.com/cms/tutorial/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8/%E8%BD%AF%E4%BB%B6%E5%AE%89%E8%A3%85",
                # 可以在这里添加更多URL
            ]
        self.output_dir = output_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.setup_directories()
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0  # 不限制行宽

    def setup_directories(self):
        """创建必要的目录"""
        os.makedirs(self.output_dir, exist_ok=True)

    def get_page_content(self, url):
        """获取页面内容"""
        try:
            response = requests.get(url, headers=self.headers)
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

    def safe_filename(self, title):
        """将标题转换为安全的文件路径，保留斜杠为子目录，移除非法字符"""
        import re
        # 允许中文、英文、数字、下划线、短横线、斜杠
        safe = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_\-/]', '', title)
        # 合并连续斜杠
        safe = re.sub(r'/+', '/', safe)
        # 去除首尾斜杠
        safe = safe.strip('/')
        # 如果为空则用默认名
        return safe if safe else "未命名文档"

    def process_content(self, html_content, url, index):
        """处理页面内容"""
        if not html_content:
            return

        soup = BeautifulSoup(html_content, 'lxml')
        # 获取标题
        title_tag = soup.find('h1')
        if title_tag:
            title = title_tag.text.strip()
        else:
            title = "未命名文档"
        # 提取核心内容
        core_content = self.extract_core_content(soup)
        # 转换为Markdown
        markdown_content = self.h2t.handle(str(core_content))
        # 添加来源地址
        source_text = f"\n\n---\n\n该文档地址来源：{url}"
        markdown_content += source_text
        # 处理文件名和目录
        safe_title = self.safe_filename(title)
        # 文件路径如 content/1_快速入门/软件安装.md
        parts = safe_title.split('/')
        if len(parts) > 1:
            subdir = os.path.join(self.output_dir, f"{index}_{parts[0]}")
            os.makedirs(subdir, exist_ok=True)
            file_path = os.path.join(subdir, '/'.join(parts[1:]) + ".md")
        else:
            subdir = self.output_dir
            file_path = os.path.join(subdir, f"{index}_{safe_title}.md")
        # 确保父目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"内容保存成功: {file_path}")

    def run(self):
        """运行爬虫，支持多个URL"""
        print("开始批量爬取页面...")
        for idx, url in enumerate(self.target_urls, 1):
            print(f"正在爬取第{idx}个页面: {url}")
            html_content = self.get_page_content(url)
            if html_content:
                self.process_content(html_content, url, idx)
            else:
                print(f"第{idx}个页面爬取失败!")
        print("全部爬取完成!")

if __name__ == "__main__":
    # 可以在这里自定义多个URL
    urls = [
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8/%E8%BD%AF%E4%BB%B6%E5%AE%89%E8%A3%85",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8/%E8%BD%AF%E4%BB%B6%E6%8E%88%E6%9D%83",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8/%E8%BD%AF%E4%BB%B6%E5%9F%BA%E7%A1%80%E6%9E%84%E6%88%90",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8/5%E5%88%86%E9%92%9F%E4%B8%8A%E6%89%8BCMS",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86/%E5%B7%A5%E7%A8%8B%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86/%E5%B7%A5%E7%A8%8B%E4%BD%BF%E7%94%A8/%E5%88%9B%E5%BB%BA%E4%B8%80%E4%B8%AA%E6%96%B0%E5%B7%A5%E7%A8%8B",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86/%E5%B7%A5%E7%A8%8B%E4%BD%BF%E7%94%A8/%E6%89%93%E5%BC%80%E5%B7%B2%E6%9C%89%E5%B7%A5%E7%A8%8B",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86/%E5%B7%A5%E7%A8%8B%E4%BD%BF%E7%94%A8/%E5%B7%A5%E7%A8%8B%E9%85%8D%E7%BD%AE%E7%89%88%E6%9C%AC%E7%BB%B4%E6%8A%A4",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86/%E5%B7%A5%E7%A8%8B%E4%BD%BF%E7%94%A8/%E5%B7%A5%E7%A8%8B%E6%95%B0%E6%8D%AE%E5%A4%87%E4%BB%BD%E8%BF%98%E5%8E%9F",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8F%98%E9%87%8F%E7%AE%A1%E7%90%86/%E5%8F%98%E9%87%8F%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8F%98%E9%87%8F%E7%AE%A1%E7%90%86/IO%E9%80%9A%E9%81%93/%E5%88%9B%E5%BB%BAIO%E5%8F%98%E9%87%8F",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8F%98%E9%87%8F%E7%AE%A1%E7%90%86/%E5%86%85%E9%83%A8%E9%80%9A%E9%81%93/%E5%88%9B%E5%BB%BA%E5%86%85%E9%83%A8%E5%8F%98%E9%87%8F",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8F%98%E9%87%8F%E7%AE%A1%E7%90%86/%E5%86%85%E9%83%A8%E9%80%9A%E9%81%93/%E5%88%9B%E5%BB%BAIO%E6%98%A0%E5%B0%84%E5%8F%98%E9%87%8F",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8F%98%E9%87%8F%E7%AE%A1%E7%90%86/%E5%86%85%E9%83%A8%E9%80%9A%E9%81%93/%E5%88%9B%E5%BB%BA%E9%80%BB%E8%BE%91%E5%8F%98%E9%87%8F",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8F%98%E9%87%8F%E7%AE%A1%E7%90%86/%E5%86%85%E9%83%A8%E9%80%9A%E9%81%93/%E4%BD%BF%E7%94%A8%E7%B3%BB%E7%BB%9F%E5%8F%98%E9%87%8F",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8F%98%E9%87%8F%E7%AE%A1%E7%90%86/%E9%A9%B1%E5%8A%A8%E4%B8%8B%E8%BD%BD",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E5%88%9B%E5%BB%BA%E7%9B%91%E6%8E%A7%E9%A1%B5%E9%9D%A2/%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E5%88%9B%E5%BB%BA%E7%9B%91%E6%8E%A7%E9%A1%B5%E9%9D%A2/%E5%9F%BA%E7%A1%80%E7%BB%84%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E5%88%9B%E5%BB%BA%E7%9B%91%E6%8E%A7%E9%A1%B5%E9%9D%A2/%E8%AF%BB%E5%86%99%E7%BB%84%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E5%88%9B%E5%BB%BA%E7%9B%91%E6%8E%A7%E9%A1%B5%E9%9D%A2/%E8%B7%B3%E8%BD%AC%E7%BB%84%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E5%88%9B%E5%BB%BA%E7%9B%91%E6%8E%A7%E9%A1%B5%E9%9D%A2/%E5%AE%B9%E5%99%A8%E7%BB%84%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E5%88%9B%E5%BB%BA%E7%9B%91%E6%8E%A7%E9%A1%B5%E9%9D%A2/%E5%AA%92%E4%BD%93%E7%BB%84%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%96%B0%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E6%9F%B1%E5%9B%BE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E7%BA%BF%E5%9B%BE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E9%A5%BC%E5%9B%BE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E8%A1%A8%E6%A0%BC",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E6%8C%87%E6%A0%87%E5%8D%A1",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E4%BB%AA%E8%A1%A8%E7%9B%98",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E6%95%B0%E6%8D%AE%E9%85%8D%E7%BD%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E8%B6%8B%E5%8A%BF%E7%9B%91%E6%8E%A7",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E5%BA%94%E7%94%A8%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%84%E4%BB%B6/%E7%BB%84%E5%90%88%E5%9B%BE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E6%97%B6%E9%97%B4%E6%8E%A7%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E4%B8%8B%E6%8B%89%E5%88%97%E8%A1%A8",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E6%96%87%E6%9C%AC%E8%BE%93%E5%85%A5",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E6%95%B0%E5%80%BC%E7%AD%9B%E9%80%89",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E7%AD%9B%E9%80%89%E5%99%A8",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E6%9F%A5%E8%AF%A2%E6%8C%89%E9%92%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E6%90%AD%E5%BB%BA%E5%88%86%E6%9E%90%E7%9C%8B%E6%9D%BF/%E6%B7%BB%E5%8A%A0%E6%8E%A7%E5%88%B6%E7%BB%84%E4%BB%B6/%E5%AF%BC%E5%87%BA%E6%8C%89%E9%92%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E5%88%B6%E4%BD%9C%E5%A4%8D%E6%9D%82%E6%8A%A5%E8%A1%A8/%E5%B1%95%E7%A4%BA%E6%8A%A5%E8%A1%A8",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E4%BD%BF%E7%94%A8%E8%BF%90%E8%A1%8C%E6%A8%A1%E5%9D%97/%E6%9D%83%E9%99%90%E7%AE%A1%E7%90%86",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E4%BD%BF%E7%94%A8%E8%BF%90%E8%A1%8C%E6%A8%A1%E5%9D%97/%E6%97%A5%E5%BF%97%E7%AE%A1%E7%90%86",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E4%BD%BF%E7%94%A8%E8%BF%90%E8%A1%8C%E6%A8%A1%E5%9D%97/%E8%B6%8B%E5%8A%BF%E9%85%8D%E7%BD%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E5%BA%94%E7%94%A8%E6%A1%88%E4%BE%8B",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E5%BF%AB%E6%8D%B7%E6%93%8D%E4%BD%9C",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E9%A1%B5%E9%9D%A2%E5%8F%82%E6%95%B0-%E7%94%BB%E9%9D%A2%E6%A8%A1%E6%9D%BF",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E7%BB%84%E4%BB%B6%E5%8F%82%E6%95%B0-%E7%BB%84%E5%90%88%E6%A8%A1%E6%9D%BF",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E9%85%8D%E7%BD%AE%E8%AF%B4%E6%98%8E/%E4%BA%8B%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E9%85%8D%E7%BD%AE%E8%AF%B4%E6%98%8E/%E6%9D%A1%E4%BB%B6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E9%85%8D%E7%BD%AE%E8%AF%B4%E6%98%8E/%E5%8A%A8%E4%BD%9C",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E5%9C%BA%E6%99%AF%E6%A1%88%E4%BE%8B/%E5%BC%B9%E7%AA%97%E5%BC%BA%E6%8F%90%E9%86%92%E6%8A%A5%E8%AD%A6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E5%9C%BA%E6%99%AF%E6%A1%88%E4%BE%8B/%E6%9F%A5%E7%9C%8B%E4%BA%A7%E5%93%81%E7%A0%81%E8%AF%A6%E6%83%85",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E5%9C%BA%E6%99%AF%E6%A1%88%E4%BE%8B/%E5%AE%9A%E6%97%B6%E5%AF%BC%E5%87%BA%E6%8A%A5%E5%91%8A%E5%BD%92%E6%A1%A3",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E4%BA%8B%E4%BB%B6%E5%8A%A8%E4%BD%9C/%E5%9C%BA%E6%99%AF%E6%A1%88%E4%BE%8B/%E6%89%AB%E7%A0%81%E8%BE%93%E5%85%A5%E5%8F%8A%E6%A0%A1%E9%AA%8C",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E7%B3%BB%E7%BB%9F%E7%BB%84%E4%BB%B6/%E5%A4%9A%E8%AF%AD%E8%A8%80",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E7%B3%BB%E7%BB%9F%E7%BB%84%E4%BB%B6/%E5%85%A8%E5%B1%8F%E5%88%87%E6%8D%A2",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E7%B3%BB%E7%BB%9F%E7%BB%84%E4%BB%B6/%E5%85%B3%E6%9C%BA%E6%8C%89%E9%92%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%A1%B5%E9%9D%A2%E7%AE%A1%E7%90%86/%E9%A1%B5%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6/%E7%B3%BB%E7%BB%9F%E7%BB%84%E4%BB%B6/%E8%99%9A%E6%8B%9F%E9%94%AE%E7%9B%98",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8E%86%E5%8F%B2%E5%BA%93/%E5%8E%86%E5%8F%B2%E5%BA%93%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%8E%86%E5%8F%B2%E5%BA%93/%E5%AD%98%E5%82%A8%E8%AE%BE%E7%BD%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%85%8D%E6%96%B9%E7%AE%A1%E7%90%86/%E9%85%8D%E6%96%B9%E5%8A%9F%E8%83%BD%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%85%8D%E6%96%B9%E7%AE%A1%E7%90%86/%E9%85%8D%E6%96%B9%E9%85%8D%E7%BD%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%85%8D%E6%96%B9%E7%AE%A1%E7%90%86/%E9%85%8D%E6%96%B9%E5%BA%94%E7%94%A8",
        "https://cms-docs.shengyc.com/cms/tutorial/%E8%AE%BE%E5%A4%87%E8%BF%90%E8%A1%8C%E7%BB%9F%E8%AE%A1/%E8%AE%BE%E5%A4%87%E8%BF%90%E8%A1%8C%E7%BB%9F%E8%AE%A1%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86/%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86/%E8%A7%A6%E5%8F%91%E9%85%8D%E7%BD%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86/%E5%AD%97%E6%AE%B5%E9%85%8D%E7%BD%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86/%E8%AE%A1%E7%AE%97%E5%85%AC%E5%BC%8F",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86/%E5%AD%98%E5%82%A8%E8%AE%BE%E7%BD%AE",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86/%E5%9C%BA%E6%99%AF%E7%A4%BA%E4%BE%8B",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%8A%A5%E8%AD%A6%E7%AE%A1%E7%90%86/%E6%8A%A5%E8%AD%A6%E7%AE%A1%E7%90%86%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%8A%A5%E8%AD%A6%E7%AE%A1%E7%90%86/%E6%8A%A5%E8%AD%A6%E8%AE%B0%E5%BD%95%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%8A%A5%E8%AD%A6%E7%AE%A1%E7%90%86/%E5%88%9B%E5%BB%BA%E6%8A%A5%E8%AD%A6",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%8A%A5%E8%AD%A6%E7%AE%A1%E7%90%86/%E6%8A%A5%E8%AD%A6%E5%BA%94%E7%94%A8",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%A4%9A%E8%AF%AD%E8%A8%80/%E5%A4%9A%E8%AF%AD%E8%A8%80%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%A4%9A%E8%AF%AD%E8%A8%80/%E5%A4%9A%E8%AF%AD%E8%A8%80%E7%BF%BB%E8%AF%91",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%A4%96%E8%AE%BE%E7%AE%A1%E7%90%86/%E5%A4%96%E8%AE%BE%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E5%A4%96%E8%AE%BE%E7%AE%A1%E7%90%86/%E8%A7%86%E9%A2%91%E8%AE%BE%E5%A4%87",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92%E4%BD%BF%E7%94%A8/%E8%BF%9E%E6%8E%A5%E6%95%B0%E6%8D%AE%E5%BA%93", 
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92%E4%BD%BF%E7%94%A8/%E6%9F%A5%E8%AF%A2%E5%8A%A8%E4%BD%9C",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92%E4%BD%BF%E7%94%A8/%E6%8F%92%E5%85%A5%E5%8A%A8%E4%BD%9C",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92%E4%BD%BF%E7%94%A8/%E4%BF%AE%E6%94%B9%E5%8A%A8%E4%BD%9C",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92/%E6%95%B0%E6%8D%AE%E5%BA%93%E4%BA%A4%E4%BA%92%E4%BD%BF%E7%94%A8/%E5%88%A0%E9%99%A4%E5%8A%A8%E4%BD%9C",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/MQTT_Client/MQTT_Client%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/MQTT_Client/MQTT_Client%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/MQTT_Client/MQTT_Client%E4%BD%BF%E7%94%A8/SLM%E5%B9%B3%E5%8F%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/MQTT_Client/MQTT_Client%E4%BD%BF%E7%94%A8/%E5%8D%8E%E4%B8%BAMQTT_V5",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/API%E6%8E%A5%E5%8F%A3/API%E6%8E%A5%E5%8F%A3%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%9B%86%E6%88%90%E4%BA%92%E8%81%94/API%E6%8E%A5%E5%8F%A3/API%E6%8E%A5%E5%8F%A3%E4%BD%BF%E7%94%A8",
        "https://cms-docs.shengyc.com/cms/tutorial/%E8%87%AA%E5%8A%A8%E5%8C%96/%E8%87%AA%E5%8A%A8%E5%8C%96%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E8%87%AA%E5%8A%A8%E5%8C%96/%E6%8C%87%E4%BB%A4",
        "https://cms-docs.shengyc.com/cms/tutorial/%E6%8F%92%E4%BB%B6%E7%AE%A1%E7%90%86",
        "https://cms-docs.shengyc.com/cms/tutorial/Vision%E7%AE%A1%E7%90%86%E5%90%8E%E5%8F%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E8%BF%9C%E7%A8%8B%E8%BF%90%E7%BB%B4/%E8%BF%9C%E7%A8%8B%E8%BF%90%E7%BB%B4%E6%A6%82%E8%BF%B0",
        "https://cms-docs.shengyc.com/cms/tutorial/%E8%BF%9C%E7%A8%8B%E8%BF%90%E7%BB%B4/%E5%8F%97%E6%8E%A7%E7%AB%AF",
        "https://cms-docs.shengyc.com/cms/tutorial/%E8%BF%9C%E7%A8%8B%E8%BF%90%E7%BB%B4/%E6%8E%A7%E5%88%B6%E7%AB%AF",
        "https://cms-docs.shengyc.com/cms/tutorial/%E9%99%84%E4%BB%B6/%E8%A1%A8%E8%BE%BE%E5%BC%8F/%E5%B0%8F%E6%8A%80%E5%B7%A7"

        # "https://cms-docs.shengyc.com/cms/tutorial/xxx/yyy", # 更多URL
    ]
    # 这里可以自定义输出目录，比如 output_dir='docs'
   #crawler = CMSCrawler(target_urls=urls, output_dir='docs')
    urls1 = [
        "https://cms-docs.shengyc.com/cms/develop/%E5%9F%BA%E5%BA%A7%E4%BA%8C%E5%BC%80%E8%B5%84%E6%96%99/%E4%BD%BF%E7%94%A8%E6%A8%A1%E6%9D%BF%E8%BF%9B%E8%A1%8C%E5%89%8D%E7%AB%AF%E5%BC%80%E5%8F%91",
        "https://cms-docs.shengyc.com/cms/develop/%E5%9F%BA%E5%BA%A7%E4%BA%8C%E5%BC%80%E8%B5%84%E6%96%99/%E5%90%8E%E7%AB%AF%E5%BC%80%E5%8F%91",
        "https://cms-docs.shengyc.com/cms/develop/%E5%9F%BA%E5%BA%A7%E4%BA%8C%E5%BC%80%E8%B5%84%E6%96%99/%E5%8D%8F%E8%AE%AE%E9%A9%B1%E5%8A%A8%E5%BC%80%E5%8F%91",
        "https://cms-docs.shengyc.com/cms/develop/LMES%E4%BA%8C%E5%BC%80%E8%B5%84%E6%96%99/%E8%B5%84%E6%96%99%E4%B8%8B%E8%BD%BD",
        "https://cms-docs.shengyc.com/cms/download/%E9%A9%B1%E5%8A%A8%E4%B8%8B%E8%BD%BD/%E6%A0%87%E5%87%86%E5%8D%8F%E8%AE%AE",
        "https://cms-docs.shengyc.com/cms/download/%E9%A9%B1%E5%8A%A8%E4%B8%8B%E8%BD%BD/PLC%E5%8D%8F%E8%AE%AE%E9%A9%B1%E5%8A%A8",
        "https://cms-docs.shengyc.com/cms/download/%E9%A9%B1%E5%8A%A8%E4%B8%8B%E8%BD%BD/%E6%99%BA%E8%83%BD%E4%BB%AA%E8%A1%A8",
        "https://cms-docs.shengyc.com/cms/download/%E9%A9%B1%E5%8A%A8%E4%B8%8B%E8%BD%BD/%E6%99%BA%E8%83%BD%E6%A8%A1%E5%9D%97",
        "https://cms-docs.shengyc.com/cms/download/%E8%A1%8C%E4%B8%9A%E7%B4%A0%E6%9D%90%E6%A8%A1%E6%9D%BF/",
        "https://cms-docs.shengyc.com/cms/download/%E8%A1%8C%E4%B8%9A%E7%B4%A0%E6%9D%90%E6%A8%A1%E6%9D%BF/",
        "https://cms-docs.shengyc.com/cms/download/LMES%E4%BA%8C%E5%BC%80%E8%B5%84%E6%96%99/LMES%E4%BA%8C%E5%BC%80%E8%A7%86%E9%A2%91",
        

    ]
    crawler = CMSCrawler(target_urls=urls1, output_dir='docs')
    crawler.run() 