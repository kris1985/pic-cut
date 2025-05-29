#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景移除逻辑详解和改进方案

当前工具使用的背景移除逻辑解析：
1. 基于AI模型的深度学习方法
2. 支持多种模型选择
3. 自动化前景提取和背景替换
"""

import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session
import cv2
import logging

class BackgroundRemovalExplained:
    """
    背景移除逻辑详解类
    """
    
    def __init__(self, model_name='u2net'):
        """
        初始化背景移除器
        
        支持的模型:
        - u2net: U²-Net 模型，平衡速度和效果
        - silueta: 轮廓检测模型，速度最快
        - isnet-general-use: IS-Net 模型，效果最好
        """
        self.session = new_session(model_name)
        self.model_name = model_name
        print(f"已加载模型: {model_name}")
    
    def remove_background_basic(self, image: Image.Image) -> Image.Image:
        """
        基础背景移除方法（当前使用的方法）
        
        步骤说明：
        1. 使用rembg库的AI模型识别前景对象
        2. 生成alpha通道蒙版
        3. 创建白色背景
        4. 合成最终图像
        
        Args:
            image: 输入的PIL图像
            
        Returns:
            移除背景后的图像
        """
        print("\n=== 基础背景移除流程 ===")
        
        # 步骤1: 使用AI模型移除背景
        print("1. 使用AI模型进行前景分割...")
        result = remove(image, session=self.session)
        print(f"   原图模式: {image.mode}, 结果模式: {result.mode}")
        
        # 步骤2: 创建白色背景
        print("2. 创建白色背景...")
        white_bg = Image.new('RGBA', result.size, (255, 255, 255, 255))
        
        # 步骤3: 合成图像
        print("3. 合成前景和背景...")
        final_image = Image.alpha_composite(white_bg, result)
        
        # 步骤4: 转换为RGB
        print("4. 转换为RGB模式")
        return final_image.convert('RGB')
    
    def remove_background_enhanced(self, image: Image.Image, 
                                 background_color=(255, 255, 255),
                                 edge_smoothing=True,
                                 noise_reduction=True) -> Image.Image:
        """
        增强版背景移除方法
        
        新增功能：
        1. 自定义背景颜色
        2. 边缘平滑处理
        3. 噪声减少
        4. 更好的透明度处理
        
        Args:
            image: 输入图像
            background_color: 背景颜色 (R, G, B)
            edge_smoothing: 是否进行边缘平滑
            noise_reduction: 是否进行噪声减少
            
        Returns:
            处理后的图像
        """
        print("\n=== 增强版背景移除流程 ===")
        
        # 步骤1: AI模型分割
        print("1. 执行AI前景分割...")
        result = remove(image, session=self.session)
        
        if edge_smoothing:
            print("2. 边缘平滑处理...")
            result = self._smooth_edges(result)
        
        if noise_reduction:
            print("3. 噪声减少...")
            result = self._reduce_noise(result)
        
        # 步骤4: 创建自定义背景
        print(f"4. 创建背景颜色: RGB{background_color}")
        bg_color = background_color + (255,)  # 添加alpha通道
        custom_bg = Image.new('RGBA', result.size, bg_color)
        
        # 步骤5: 高质量合成
        print("5. 高质量图像合成...")
        final_image = Image.alpha_composite(custom_bg, result)
        
        return final_image.convert('RGB')
    
    def _smooth_edges(self, image: Image.Image) -> Image.Image:
        """
        边缘平滑处理
        
        使用高斯模糊对alpha通道进行轻微平滑，
        减少锯齿效果，让边缘更自然
        """
        if image.mode != 'RGBA':
            return image
            
        # 分离通道
        r, g, b, a = image.split()
        
        # 对alpha通道进行轻微模糊
        a_smooth = a.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # 重新合成
        return Image.merge('RGBA', (r, g, b, a_smooth))
    
    def _reduce_noise(self, image: Image.Image) -> Image.Image:
        """
        噪声减少处理
        
        使用形态学操作清理alpha通道中的小噪声点
        """
        if image.mode != 'RGBA':
            return image
            
        # 转换为numpy数组处理alpha通道
        img_array = np.array(image)
        alpha_channel = img_array[:, :, 3]
        
        # 形态学操作去除噪声
        kernel = np.ones((3, 3), np.uint8)
        
        # 开运算去除小噪声
        alpha_clean = cv2.morphologyEx(alpha_channel, cv2.MORPH_OPEN, kernel)
        
        # 闭运算填补小孔洞
        alpha_clean = cv2.morphologyEx(alpha_clean, cv2.MORPH_CLOSE, kernel)
        
        # 更新alpha通道
        img_array[:, :, 3] = alpha_clean
        
        return Image.fromarray(img_array, 'RGBA')
    
    def remove_background_adaptive(self, image: Image.Image) -> Image.Image:
        """
        自适应背景移除
        
        根据图像特征自动选择最佳处理策略：
        1. 检测图像复杂度
        2. 自动调整处理参数
        3. 针对不同类型图像优化
        """
        print("\n=== 自适应背景移除流程 ===")
        
        # 步骤1: 分析图像特征
        print("1. 分析图像特征...")
        complexity = self._analyze_image_complexity(image)
        print(f"   图像复杂度: {complexity}")
        
        # 步骤2: 选择处理策略
        if complexity == "simple":
            print("2. 使用快速处理模式...")
            return self.remove_background_basic(image)
        elif complexity == "complex":
            print("2. 使用增强处理模式...")
            return self.remove_background_enhanced(
                image, 
                edge_smoothing=True, 
                noise_reduction=True
            )
        else:  # medium
            print("2. 使用平衡处理模式...")
            return self.remove_background_enhanced(
                image, 
                edge_smoothing=True, 
                noise_reduction=False
            )
    
    def _analyze_image_complexity(self, image: Image.Image) -> str:
        """
        分析图像复杂度
        
        基于以下因素判断：
        1. 边缘密度
        2. 颜色变化
        3. 纹理复杂度
        
        Returns:
            "simple", "medium", "complex"
        """
        # 转换为灰度图进行分析
        gray = image.convert('L')
        img_array = np.array(gray)
        
        # 计算梯度强度（边缘密度）
        grad_x = cv2.Sobel(img_array, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(img_array, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        edge_density = np.mean(gradient_magnitude)
        
        # 计算直方图熵（颜色变化）
        hist = cv2.calcHist([img_array], [0], None, [256], [0, 256])
        hist_norm = hist.flatten() / hist.sum()
        hist_norm = hist_norm[hist_norm > 0]  # 避免log(0)
        entropy = -np.sum(hist_norm * np.log2(hist_norm))
        
        print(f"   边缘密度: {edge_density:.2f}")
        print(f"   信息熵: {entropy:.2f}")
        
        # 简单的阈值判断
        if edge_density < 10 and entropy < 6:
            return "simple"
        elif edge_density > 20 or entropy > 7:
            return "complex"
        else:
            return "medium"
    
    def compare_methods(self, image_path: str, output_dir: str = "./"):
        """
        对比不同背景移除方法的效果
        
        Args:
            image_path: 输入图像路径
            output_dir: 输出目录
        """
        print(f"\n=== 对比不同背景移除方法 ===")
        print(f"输入图像: {image_path}")
        
        # 加载图像
        image = Image.open(image_path)
        print(f"图像尺寸: {image.size}")
        
        # 方法1: 基础方法
        print("\n--- 测试基础方法 ---")
        result1 = self.remove_background_basic(image)
        result1.save(f"{output_dir}/bg_removed_basic.jpg", quality=95)
        
        # 方法2: 增强方法
        print("\n--- 测试增强方法 ---")
        result2 = self.remove_background_enhanced(image)
        result2.save(f"{output_dir}/bg_removed_enhanced.jpg", quality=95)
        
        # 方法3: 自适应方法
        print("\n--- 测试自适应方法 ---")
        result3 = self.remove_background_adaptive(image)
        result3.save(f"{output_dir}/bg_removed_adaptive.jpg", quality=95)
        
        print(f"\n结果已保存到: {output_dir}")
        print("文件:")
        print("- bg_removed_basic.jpg (基础方法)")
        print("- bg_removed_enhanced.jpg (增强方法)")
        print("- bg_removed_adaptive.jpg (自适应方法)")


# 使用示例
def demo_background_removal():
    """
    背景移除演示
    """
    print("=== 背景移除逻辑演示 ===")
    
    # 初始化
    remover = BackgroundRemovalExplained('u2net')
    
    # 如果有测试图片，可以运行对比
    test_image = "./sample_shoe.jpg"
    if os.path.exists(test_image):
        remover.compare_methods(test_image)
    else:
        print("没有找到测试图片，请确保 sample_shoe.jpg 存在")


if __name__ == "__main__":
    import os
    demo_background_removal() 