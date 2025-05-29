# 鞋子图片处理工具 - 快速开始

## 🚀 快速安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建目录结构
mkdir -p input_images processed_images
```

## ⚡ 快速使用

### 方法1: 一键批量处理（推荐）

```bash
# 1. 将鞋子图片放入 input_images 文件夹
# 2. 运行处理脚本
python example_usage.py
# 3. 选择选项 1（批量处理）
# 4. 处理完成的图片将保存在 processed_images 文件夹
```

### 方法2: 命令行工具

```bash
# 批量处理整个目录
python shoe_image_processor.py input_images processed_images

# 处理单张图片
python shoe_image_processor.py shoe.jpg processed_shoe.jpg --single

# 🔥 高分辨率图片处理（推荐！）
python shoe_image_processor.py large_shoe.jpg processed_shoe.jpg --single --hires

# 指定比例（横图4:3）
python shoe_image_processor.py input_images output_images --ratio 4:3

# 指定比例（竖图3:4）
python shoe_image_processor.py input_images output_images --ratio 3:4

# 使用更快的模型
python shoe_image_processor.py input_images output_images --model silueta

# 高质量处理（推荐）
python shoe_image_processor.py input_images output_images --quality high
```

## 🎯 处理效果

- ✅ **自动去背景**: 移除复杂背景，替换为纯白色
- ✅ **智能裁剪**: 自动检测鞋子位置，确保居中显示
- ✅ **标准比例**: 自动选择4:3（横图）或3:4（竖图）
- ✅ **保持完整**: 确保鞋子不被截断
- ✅ **高分辨率**: 减少大图片的分辨率损失，避免模糊

## 📋 支持格式

- JPG/JPEG
- PNG
- BMP  
- TIFF
- WEBP

## ⚙️ 模型选择

| 模型 | 速度 | 效果 | 推荐场景 |
|------|------|------|----------|
| `u2net` | 中等 | 很好 | 日常使用（默认）|
| `silueta` | 最快 | 良好 | 大批量处理 |
| `isnet-general-use` | 较慢 | 最佳 | 高质量要求 |

## 🔥 避免图片模糊的重要提示

### 什么情况下图片会变模糊？
- 原图分辨率 > 2000x2000 像素
- 使用默认模式处理大图片
- 分辨率损失超过50%

### 解决方案：
```bash
# 1. 使用高分辨率模式
python shoe_image_processor.py large_image.jpg output.jpg --single --hires

# 2. 结合高质量保存
python shoe_image_processor.py large_image.jpg output.jpg --single --hires --quality high

# 3. 批量处理大图片
python shoe_image_processor.py input_dir output_dir --hires --quality high
```

### 效果对比：
- **默认模式**: 分辨率保持 ~42%，可能模糊
- **高分辨率模式**: 分辨率保持 ~54%，清晰度显著提升

## 🛠️ 故障排除

**问题**: 模块导入错误
```bash
# 解决方案
pip install -r requirements.txt
```

**问题**: 处理速度慢
```bash
# 使用更快的模型
python shoe_image_processor.py input_dir output_dir --model silueta
```

**🔥 问题**: 图片变模糊
```bash
# 解决方案：使用高分辨率模式
python shoe_image_processor.py input.jpg output.jpg --single --hires --quality high
```

## 📞 技术支持

详细文档请参考: [IMAGE_PROCESSING_README.md](IMAGE_PROCESSING_README.md) 