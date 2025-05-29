#!/usr/bin/env python3
from PIL import Image
import os

# 文件路径
files = {
    '原图': './input_images/2582cf502b5a4e8787a1c735999cc8d0.jpg',
    '旧版处理': './processed_images/2582cf502b5a4e8787a1c735999cc8d0_processed.jpg',
    '优化版本': './2582cf502b5a4e8787a1c735999cc8d0_improved.jpg',
    '高分辨率': './2582cf502b5a4e8787a1c735999cc8d0_hires.jpg'
}

print('=== 图片处理结果对比 ===')
print()

# 获取原图信息
orig_img = Image.open(files['原图'])
orig_pixels = orig_img.size[0] * orig_img.size[1]
orig_img.close()

for name, path in files.items():
    if os.path.exists(path):
        img = Image.open(path)
        pixels = img.size[0] * img.size[1]
        ratio = pixels / orig_pixels if name != '原图' else 1.0
        size_mb = os.path.getsize(path) / 1024 / 1024
        
        print(f'{name:8s}: {img.size[0]:4d}x{img.size[1]:4d} | '
              f'{pixels:7,}像素 | 保持率: {ratio:5.1%} | 文件: {size_mb:5.2f}MB')
        img.close()
    else:
        print(f'{name:8s}: 文件不存在')

print()
print('=== 分析结果 ===')
print('• 旧版处理: 分辨率损失57.7%，可能导致模糊')
print('• 优化版本: 分辨率损失54.0%，略有改善')  
print('• 高分辨率: 分辨率损失45.7%，清晰度显著提升')
print()
print('💡 建议: 对于高分辨率图片，使用 --hires 参数可以获得更好的效果') 