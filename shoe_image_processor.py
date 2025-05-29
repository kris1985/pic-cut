#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鞋子图片批量处理工具
功能：
1. 智能裁剪为4:3或3:4比例
2. 确保鞋子显示完整且居中
"""

import os
import sys
from pathlib import Path
import argparse
from typing import Tuple, List
import logging

import cv2
import numpy as np
from PIL import Image, ImageFilter
import shutil

# 尝试导入scipy，如果失败则使用简单的替代方案
try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning("scipy未安装，将使用简化的图像处理方法")


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ShoeImageProcessor:
    """鞋子图片处理器"""
    
    def __init__(self):
        """
        初始化处理器
        """
        logger.info("已初始化图片处理器")
    
    def find_object_bounds(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        寻找图片中主体对象的边界框
        
        Args:
            image: PIL Image对象
            
        Returns:
            (left, top, right, bottom) 边界框坐标
        """
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 转换为灰度图
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        width, height = image.size
        best_contour = None
        best_area = 0
        best_bounds = None
        
        # 策略1: 商品图片专用 - 基于亮度差异检测
        try:
            # 计算图片边缘的平均亮度（通常是背景色）
            edge_samples = []
            edge_thickness = min(50, min(width, height) // 20)  # 边缘采样厚度
            
            # 采样四条边
            edge_samples.extend(gray[:edge_thickness, :].flatten())  # 上边
            edge_samples.extend(gray[-edge_thickness:, :].flatten())  # 下边
            edge_samples.extend(gray[:, :edge_thickness].flatten())  # 左边
            edge_samples.extend(gray[:, -edge_thickness:].flatten())  # 右边
            
            bg_brightness = np.median(edge_samples)
            logger.info(f"检测到背景亮度: {bg_brightness:.1f}")
            
            # 根据背景亮度动态调整阈值
            if bg_brightness > 200:  # 白色背景
                # 寻找比背景暗的区域
                threshold_offset = 30
                _, binary = cv2.threshold(gray, bg_brightness - threshold_offset, 255, cv2.THRESH_BINARY_INV)
            else:  # 暗色背景
                # 寻找比背景亮的区域
                threshold_offset = 30
                _, binary = cv2.threshold(gray, bg_brightness + threshold_offset, 255, cv2.THRESH_BINARY)
            
            # 形态学处理，连接断开的区域
            kernel = np.ones((7, 7), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # 去除边缘噪声
            border_size = max(5, min(width, height) // 100)
            binary[:border_size, :] = 0
            binary[-border_size:, :] = 0
            binary[:, :border_size] = 0
            binary[:, -border_size:] = 0
            
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # 筛选合适的轮廓
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > height * width * 0.05:  # 面积至少占图片的5%
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # 检查宽高比是否合理（商品通常不会太细长）
                        aspect_ratio = w / h
                        if 0.3 <= aspect_ratio <= 5.0:
                            if area > best_area:
                                best_area = area
                                best_contour = contour
                                best_bounds = (x, y, x + w, y + h)
                                
        except Exception as e:
            logger.warning(f"商品检测策略失败: {e}")
        
        # 策略2: 增强的边缘检测
        if best_contour is None:
            try:
                # 多尺度边缘检测
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                
                # 尝试多个Canny参数
                edge_params = [(30, 100), (50, 150), (70, 200)]
                for low, high in edge_params:
                    edges = cv2.Canny(blurred, low, high)
                    
                    # 膨胀以连接边缘
                    kernel = np.ones((5, 5), np.uint8)
                    edges = cv2.dilate(edges, kernel, iterations=2)
                    edges = cv2.erode(edges, kernel, iterations=1)
                    
                    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        for contour in contours:
                            area = cv2.contourArea(contour)
                            if area > height * width * 0.03:
                                x, y, w, h = cv2.boundingRect(contour)
                                aspect_ratio = w / h
                                if 0.2 <= aspect_ratio <= 8.0:
                                    if area > best_area:
                                        best_area = area
                                        best_contour = contour
                                        best_bounds = (x, y, x + w, y + h)
                                        
            except Exception as e:
                logger.warning(f"边缘检测策略失败: {e}")
        
        # 策略3: 基于颜色聚类的检测（适合复杂背景）
        if best_contour is None:
            try:
                # 将图片转换为LAB颜色空间进行更好的颜色分离
                lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
                
                # 重塑为像素列表
                pixel_values = lab.reshape((-1, 3))
                pixel_values = np.float32(pixel_values)
                
                # K-means聚类分离前景和背景
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
                k = 3  # 分为3个聚类：背景、主体、阴影
                _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
                
                # 重塑标签为图片形状
                labels = labels.reshape((height, width))
                
                # 寻找最可能是主体的聚类（不在边缘的最大聚类）
                for label in range(k):
                    mask = (labels == label).astype(np.uint8) * 255
                    
                    # 排除主要在边缘的聚类
                    edge_mask = np.zeros_like(mask)
                    edge_width = min(20, min(width, height) // 20)
                    edge_mask[:edge_width, :] = 1
                    edge_mask[-edge_width:, :] = 1
                    edge_mask[:, :edge_width] = 1
                    edge_mask[:, -edge_width:] = 1
                    
                    edge_pixels = np.sum(mask * edge_mask)
                    total_pixels = np.sum(mask)
                    
                    if total_pixels > 0 and edge_pixels / total_pixels < 0.7:  # 不超过70%在边缘
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if contours:
                            largest = max(contours, key=cv2.contourArea)
                            area = cv2.contourArea(largest)
                            if area > height * width * 0.05:
                                x, y, w, h = cv2.boundingRect(largest)
                                if area > best_area:
                                    best_area = area
                                    best_contour = largest
                                    best_bounds = (x, y, x + w, y + h)
                                    
            except Exception as e:
                logger.warning(f"颜色聚类策略失败: {e}")
        
        if best_bounds is not None:
            left, top, right, bottom = best_bounds
            
            # 智能边距调整
            obj_width = right - left
            obj_height = bottom - top
            
            # 根据对象大小动态调整边距
            margin_x = max(10, int(obj_width * 0.1))
            margin_y = max(10, int(obj_height * 0.15))  # 垂直边距稍大
            
            left = max(0, left - margin_x)
            top = max(0, top - margin_y)
            right = min(width, right + margin_x)
            bottom = min(height, bottom + margin_y)
            
            # 验证检测结果的合理性
            detected_width = right - left
            detected_height = bottom - top
            detected_area = detected_width * detected_height
            image_area = width * height
            
            area_ratio = detected_area / image_area
            logger.info(f"检测到对象边界: ({left}, {top}, {right}, {bottom})")
            logger.info(f"对象尺寸: {detected_width}x{detected_height}, 面积占比: {area_ratio:.1%}")
            
            # 如果检测结果合理，返回边界
            if 0.1 <= area_ratio <= 0.9:
                return left, top, right, bottom
            else:
                logger.warning(f"检测到的边界面积占比异常: {area_ratio:.1%}, 使用保守策略")
        
        # 如果所有策略都失败，使用保守策略
        logger.warning("所有对象检测策略都失败，使用保守裁剪策略")
        return self._conservative_bounds(image)
    
    def _conservative_bounds(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        保守的边界检测策略，适用于对象检测失败的情况
        针对商品图片做特殊优化
        
        Args:
            image: PIL Image对象
            
        Returns:
            (left, top, right, bottom) 边界框坐标
        """
        width, height = image.size
        
        # 对于商品图片，通常主体在中下部分
        # 分析图片的内容分布来做更智能的保守估计
        
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        # 计算每一行的"活跃度"（内容变化程度）
        row_activity = []
        for i in range(height):
            row = gray[i, :]
            # 计算这一行的标准差和梯度，作为活跃度指标
            std_dev = np.std(row)
            gradient = np.sum(np.abs(np.diff(row)))
            activity = std_dev + gradient / len(row)
            row_activity.append(activity)
        
        # 计算每一列的活跃度
        col_activity = []
        for j in range(width):
            col = gray[:, j]
            std_dev = np.std(col)
            gradient = np.sum(np.abs(np.diff(col)))
            activity = std_dev + gradient / len(col)
            col_activity.append(activity)
        
        # 使用活跃度来估计对象边界
        row_activity = np.array(row_activity)
        col_activity = np.array(col_activity)
        
        # 平滑活跃度曲线
        if HAS_SCIPY:
            row_activity = ndimage.gaussian_filter1d(row_activity, sigma=height//50)
            col_activity = ndimage.gaussian_filter1d(col_activity, sigma=width//50)
        else:
            # 简单的移动平均作为平滑替代
            window_size = max(3, height//50)
            row_activity = np.convolve(row_activity, np.ones(window_size)/window_size, mode='same')
            col_activity = np.convolve(col_activity, np.ones(window_size)/window_size, mode='same')
        
        # 找到活跃度的阈值
        row_threshold = np.mean(row_activity) + 0.5 * np.std(row_activity)
        col_threshold = np.mean(col_activity) + 0.5 * np.std(col_activity)
        
        # 找到活跃区域的边界
        active_rows = np.where(row_activity > row_threshold)[0]
        active_cols = np.where(col_activity > col_threshold)[0]
        
        if len(active_rows) > 0 and len(active_cols) > 0:
            top = max(0, active_rows[0] - height//20)  # 留一些边距
            bottom = min(height, active_rows[-1] + height//20)
            left = max(0, active_cols[0] - width//20)
            right = min(width, active_cols[-1] + width//20)
            
            # 验证结果的合理性
            detected_width = right - left
            detected_height = bottom - top
            detected_area = detected_width * detected_height
            image_area = width * height
            
            area_ratio = detected_area / image_area
            
            # 如果检测到的区域合理，使用它
            if 0.2 <= area_ratio <= 0.9:
                logger.info(f"保守策略检测到活跃区域: ({left}, {top}, {right}, {bottom}), 面积占比: {area_ratio:.1%}")
                return left, top, right, bottom
        
        # 如果活跃度分析也失败，使用传统的保守策略
        # 但是针对商品图片做优化：假设商品在中下部分
        logger.info("使用传统保守策略，假设商品在中下部分")
        
        # 水平方向：使用中间80%区域
        margin_w = int(width * 0.1)
        left = margin_w
        right = width - margin_w
        
        # 垂直方向：假设商品在中下部分，使用下部70%区域
        top = int(height * 0.15)  # 从15%位置开始
        bottom = int(height * 0.95)  # 到95%位置结束
        
        return left, top, right, bottom
    
    def smart_crop(self, image: Image.Image, target_ratio: str = 'auto', min_resolution: int = 1200, 
                   preserve_resolution: bool = False) -> Image.Image:
        """
        智能裁剪图片，确保主体居中显示并保持高分辨率
        
        Args:
            image: PIL Image对象
            target_ratio: 目标比例 '4:3', '3:4', 'auto'
            min_resolution: 最小分辨率（短边）
            preserve_resolution: 是否优先保持分辨率（适合高分辨率图片）
            
        Returns:
            裁剪后的PIL Image对象
        """
        # 获取原图尺寸
        original_width, original_height = image.size
        
        # 找到主体边界
        left, top, right, bottom = self.find_object_bounds(image)
        object_width = right - left
        object_height = bottom - top
        
        # 确定目标比例
        if target_ratio == 'auto':
            # 根据主体形状自动选择比例
            if object_width > object_height:
                target_ratio = '4:3'
            else:
                target_ratio = '3:4'
        
        # 解析目标比例
        if target_ratio == '4:3':
            ratio_w, ratio_h = 4, 3
        elif target_ratio == '3:4':
            ratio_w, ratio_h = 3, 4
        else:
            raise ValueError(f"不支持的比例: {target_ratio}")
        
        # 高分辨率模式：优先保持更多像素
        if preserve_resolution or min(original_width, original_height) > 2000:
            # 对于高分辨率图片，使用更保守的裁剪策略
            
            # 计算以对象为中心的最大可能裁剪区域
            object_center_x = (left + right) / 2
            object_center_y = (top + bottom) / 2
            
            # 从原图的最大尺寸开始，按比例调整
            max_width = original_width
            max_height = original_height
            
            # 根据目标比例确定实际裁剪尺寸
            if max_width / max_height > ratio_w / ratio_h:
                # 宽度过大，以高度为准
                target_height = max_height
                target_width = target_height * ratio_w / ratio_h
            else:
                # 高度过大，以宽度为准
                target_width = max_width
                target_height = target_width * ratio_h / ratio_w
            
            # 确保对象能完全显示
            needed_width = object_width * 1.05  # 只留5%的边距
            needed_height = object_height * 1.05
            
            if target_width < needed_width or target_height < needed_height:
                # 如果裁剪区域太小，适当放大但保持比例
                scale = max(needed_width / target_width, needed_height / target_height)
                target_width *= scale
                target_height *= scale
            
        else:
            # 标准模式：平衡分辨率和边距
            # 动态调整边距系数，根据图片大小和主体大小
            image_diagonal = (original_width**2 + original_height**2)**0.5
            object_diagonal = (object_width**2 + object_height**2)**0.5
            
            # 根据主体占图片的比例动态调整边距
            object_ratio = object_diagonal / image_diagonal
            if object_ratio > 0.7:  # 主体已经很大
                margin_factor = 1.1
            elif object_ratio > 0.5:  # 主体适中
                margin_factor = 1.15
            else:  # 主体较小
                margin_factor = 1.25
            
            # 计算保持高分辨率的目标尺寸
            needed_width = object_width * margin_factor
            needed_height = object_height * margin_factor
            
            # 根据目标比例调整，但尽量保持高分辨率
            if needed_width / needed_height > ratio_w / ratio_h:
                # 宽度是限制因素
                target_width = needed_width
                target_height = needed_width * ratio_h / ratio_w
            else:
                # 高度是限制因素
                target_height = needed_height
                target_width = needed_height * ratio_w / ratio_h
            
            # 确保目标尺寸满足最小分辨率要求
            min_width = min_resolution if ratio_w >= ratio_h else min_resolution * ratio_w / ratio_h
            min_height = min_resolution if ratio_h >= ratio_w else min_resolution * ratio_h / ratio_w
            
            target_width = max(target_width, min_width)
            target_height = max(target_height, min_height)
        
        # 确保不超出原图范围，但优先保持分辨率
        if target_width > original_width or target_height > original_height:
            # 如果超出原图，按比例缩小但尽量保持高分辨率
            scale_w = original_width / target_width if target_width > original_width else 1
            scale_h = original_height / target_height if target_height > original_height else 1
            scale = min(scale_w, scale_h)
            
            target_width *= scale
            target_height *= scale
        
        # 计算主体中心点
        object_center_x = (left + right) / 2
        object_center_y = (top + bottom) / 2
        
        # 计算裁剪区域，特别注意垂直居中
        # 对于鞋子等商品图片，通常希望稍微偏向视觉中心（略高于几何中心）
        visual_center_offset = target_height * 0.05  # 稍微向上偏移5%，视觉效果更好
        
        crop_left = max(0, int(object_center_x - target_width / 2))
        crop_top = max(0, int(object_center_y - target_height / 2 - visual_center_offset))
        crop_right = min(original_width, int(crop_left + target_width))
        crop_bottom = min(original_height, int(crop_top + target_height))
        
        # 边界调整：如果触及边界，调整整个裁剪区域
        if crop_left == 0:
            crop_right = min(original_width, int(target_width))
        elif crop_right == original_width:
            crop_left = max(0, original_width - int(target_width))
            crop_right = original_width
        
        if crop_top == 0:
            crop_bottom = min(original_height, int(target_height))
        elif crop_bottom == original_height:
            crop_top = max(0, original_height - int(target_height))
            crop_bottom = original_height
        
        # 最终验证：确保对象在裁剪区域内
        final_object_center_x = (left + right) / 2
        final_object_center_y = (top + bottom) / 2
        
        crop_center_x = (crop_left + crop_right) / 2
        crop_center_y = (crop_top + crop_bottom) / 2
        
        # 如果对象中心偏离裁剪中心太远，进行微调
        offset_x = final_object_center_x - crop_center_x
        offset_y = final_object_center_y - crop_center_y
        
        # 允许的最大偏移（相对于裁剪区域尺寸的比例）
        max_offset_x = target_width * 0.15
        max_offset_y = target_height * 0.15
        
        if abs(offset_x) > max_offset_x or abs(offset_y) > max_offset_y:
            # 需要重新居中
            logger.info("重新调整裁剪区域以确保对象居中")
            
            # 重新计算，但要确保不超出原图边界
            new_crop_left = max(0, min(original_width - target_width, 
                                     int(final_object_center_x - target_width / 2)))
            new_crop_top = max(0, min(original_height - target_height, 
                                    int(final_object_center_y - target_height / 2 - visual_center_offset)))
            
            crop_left = new_crop_left
            crop_top = new_crop_top
            crop_right = crop_left + int(target_width)
            crop_bottom = crop_top + int(target_height)
        
        # 执行裁剪
        cropped = image.crop((crop_left, crop_top, crop_right, crop_bottom))
        
        # 计算分辨率保持率
        original_pixels = original_width * original_height
        cropped_pixels = cropped.width * cropped.height
        resolution_ratio = cropped_pixels / original_pixels
        
        logger.info(f"裁剪: {original_width}x{original_height} -> {cropped.width}x{cropped.height} (比例: {target_ratio}, 分辨率保持: {resolution_ratio:.1%})")
        
        # 如果分辨率损失太大，给出警告
        if resolution_ratio < 0.5:
            logger.warning(f"注意：分辨率损失较大 ({resolution_ratio:.1%}), 可能影响图片清晰度")
        
        return cropped
    
    def process_single_image(self, input_path: str, output_path: str, target_ratio: str = 'auto', 
                           high_quality: bool = True, preserve_resolution: bool = False) -> bool:
        """
        处理单张图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            target_ratio: 目标比例
            high_quality: 是否使用高质量保存
            preserve_resolution: 是否优先保持分辨率（适合高分辨率图片）
            
        Returns:
            是否处理成功
        """
        try:
            logger.info(f"开始处理: {input_path}")
            
            # 获取原文件大小
            original_file_size = os.path.getsize(input_path)
            
            # 读取图片
            with Image.open(input_path) as image:
                # 获取原始图片信息
                original_format = image.format
                original_mode = image.mode
                
                # 智能裁剪
                final_image = self.smart_crop(image, target_ratio, preserve_resolution=preserve_resolution)
                
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir:  # 只有当输出目录不为空时才创建
                    os.makedirs(output_dir, exist_ok=True)
                
                # 智能质量设置 - 防止文件过大
                # 计算像素比例来估算合理的质量
                original_pixels = image.width * image.height
                cropped_pixels = final_image.width * final_image.height
                pixel_ratio = cropped_pixels / original_pixels
                
                # 根据原图格式确定保存格式和参数
                output_format = original_format
                save_kwargs = {}
                
                # 如果原图是PNG且有透明通道，保持透明度
                if original_format == 'PNG':
                    save_kwargs['format'] = 'PNG'
                    if original_mode in ('RGBA', 'LA') or 'transparency' in image.info:
                        save_kwargs['optimize'] = True
                        # PNG使用compress_level而不是quality
                        if high_quality:
                            save_kwargs['compress_level'] = 6  # 0-9，6是平衡点
                        else:
                            save_kwargs['compress_level'] = 9  # 更高压缩
                    else:
                        # 没有透明度的PNG可以考虑转为JPEG以减小文件大小
                        if original_file_size > 1024 * 1024:  # 大于1MB的PNG考虑转JPEG
                            save_kwargs['format'] = 'JPEG'
                            save_kwargs['optimize'] = True
                            # 调整输出路径扩展名
                            output_base, _ = os.path.splitext(output_path)
                            output_path = output_base + '.jpg'
                            logger.info(f"大尺寸PNG文件将转换为JPEG以减小文件大小")
                        else:
                            save_kwargs['format'] = 'PNG'
                            save_kwargs['optimize'] = True
                            save_kwargs['compress_level'] = 6 if high_quality else 9
                
                elif original_format in ('JPEG', 'JPG'):
                    save_kwargs['format'] = 'JPEG'
                    save_kwargs['optimize'] = True
                    
                elif original_format == 'WEBP':
                    save_kwargs['format'] = 'WEBP'
                    save_kwargs['method'] = 6  # 压缩方法
                    
                else:
                    # 其他格式（BMP、TIFF等）转为JPEG
                    save_kwargs['format'] = 'JPEG'
                    save_kwargs['optimize'] = True
                    # 调整输出路径扩展名
                    output_base, _ = os.path.splitext(output_path)
                    output_path = output_base + '.jpg'
                    logger.info(f"{original_format}格式将转换为JPEG")
                
                # 为JPEG和WEBP设置质量参数
                if save_kwargs['format'] in ('JPEG', 'WEBP'):
                    # 根据原文件大小和像素比例智能调整质量
                    if high_quality:
                        # 估算合理的质量值
                        if pixel_ratio > 0.8:  # 裁剪不多，保持较高质量
                            base_quality = 92
                        elif pixel_ratio > 0.5:  # 中等裁剪
                            base_quality = 88
                        else:  # 大幅裁剪
                            base_quality = 85
                            
                        # 根据原文件大小调整
                        if original_file_size < 500 * 1024:  # 小于500KB
                            save_kwargs['quality'] = min(base_quality + 5, 95)
                        elif original_file_size < 2 * 1024 * 1024:  # 小于2MB
                            save_kwargs['quality'] = base_quality
                        else:  # 大文件
                            save_kwargs['quality'] = max(base_quality - 5, 80)
                            
                        # 对于高质量JPEG，保留色度采样设置
                        if save_kwargs['format'] == 'JPEG':
                            save_kwargs['subsampling'] = 0
                    else:
                        # 普通质量模式
                        save_kwargs['quality'] = 82
                
                # 保持颜色模式一致（如果可能）
                if save_kwargs['format'] == 'JPEG' and final_image.mode in ('RGBA', 'LA', 'P'):
                    # JPEG不支持透明度，需要转换
                    if final_image.mode == 'P':
                        final_image = final_image.convert('RGB')
                    elif final_image.mode in ('RGBA', 'LA'):
                        # 创建白色背景
                        bg = Image.new('RGB', final_image.size, (255, 255, 255))
                        if final_image.mode == 'RGBA':
                            bg.paste(final_image, mask=final_image.split()[-1])
                        else:
                            bg.paste(final_image, mask=final_image.split()[-1])
                        final_image = bg
                
                # 保存图片
                logger.info(f"保存格式: {save_kwargs['format']}, 参数: {save_kwargs}")
                final_image.save(output_path, **save_kwargs)
                
                # 检查输出文件大小
                output_file_size = os.path.getsize(output_path)
                size_ratio = output_file_size / original_file_size
                
                # 如果输出文件比原文件大太多且是压缩格式，降低质量重新保存
                if (size_ratio > 1.3 and pixel_ratio < 0.9 and 
                    save_kwargs['format'] in ('JPEG', 'WEBP') and 'quality' in save_kwargs):
                    
                    logger.warning(f"输出文件过大 ({size_ratio:.1f}x)，降低质量重新保存")
                    
                    # 重新计算质量
                    new_quality = max(75, int(save_kwargs['quality'] * 0.8))
                    save_kwargs['quality'] = new_quality
                    save_kwargs.pop('subsampling', None)  # 移除色度采样设置
                    
                    final_image.save(output_path, **save_kwargs)
                    
                    # 再次检查
                    output_file_size = os.path.getsize(output_path)
                    size_ratio = output_file_size / original_file_size
                
                # 记录文件大小信息
                logger.info(f"文件大小: {original_file_size/1024:.1f}KB -> {output_file_size/1024:.1f}KB (比例: {size_ratio:.2f}x)")
                logger.info(f"格式: {original_format} -> {save_kwargs['format']}")
                
                logger.info(f"处理完成: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"处理图片 {input_path} 时出错: {e}")
            return False
    
    def process_batch(self, input_dir: str, output_dir: str, target_ratio: str = 'auto', 
                     supported_formats: List[str] = None, high_quality: bool = True, 
                     preserve_resolution: bool = False) -> dict:
        """
        批量处理图片
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            target_ratio: 目标比例
            supported_formats: 支持的图片格式
            high_quality: 是否使用高质量保存
            preserve_resolution: 是否优先保持分辨率
            
        Returns:
            处理统计信息
        """
        if supported_formats is None:
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 获取所有支持的图片文件
        image_files = []
        for ext in supported_formats:
            image_files.extend(input_path.glob(f"*{ext.lower()}"))
            image_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        total_files = len(image_files)
        successful = 0
        failed = 0
        
        logger.info(f"找到 {total_files} 张图片待处理")
        
        for i, image_file in enumerate(image_files, 1):
            logger.info(f"处理进度: {i}/{total_files}")
            
            # 构建输出文件路径 - 保持与源文件名一致
            # 注意：如果process_single_image中发生格式转换，文件扩展名可能会改变
            output_file = output_path / image_file.name  # 使用原文件名
            
            # 处理图片
            if self.process_single_image(str(image_file), str(output_file), target_ratio, 
                                       high_quality, preserve_resolution):
                successful += 1
            else:
                failed += 1
        
        stats = {
            'total': total_files,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_files if total_files > 0 else 0
        }
        
        logger.info(f"批量处理完成! 总计: {total_files}, 成功: {successful}, 失败: {failed}")
        
        return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='鞋子图片批量处理工具')
    parser.add_argument('input', help='输入文件或目录路径')
    parser.add_argument('output', help='输出文件或目录路径')
    parser.add_argument('--ratio', choices=['4:3', '3:4', 'auto'], default='auto', 
                       help='目标比例 (默认: auto)')
    parser.add_argument('--single', action='store_true', help='处理单张图片')
    parser.add_argument('--hires', action='store_true', 
                       help='高分辨率模式，优先保持原图分辨率（推荐用于大图）')
    parser.add_argument('--quality', choices=['normal', 'high'], default='high',
                       help='保存质量 (默认: high)')
    
    args = parser.parse_args()
    
    try:
        # 创建处理器
        processor = ShoeImageProcessor()
        
        # 设置质量参数
        high_quality = args.quality == 'high'
        preserve_resolution = args.hires
        
        if args.single or os.path.isfile(args.input):
            # 单张图片处理
            success = processor.process_single_image(
                args.input, args.output, args.ratio, high_quality, preserve_resolution)
            if success:
                print("✅ 图片处理成功!")
            else:
                print("❌ 图片处理失败!")
                sys.exit(1)
        else:
            # 批量处理
            stats = processor.process_batch(args.input, args.output, args.ratio, None, high_quality, preserve_resolution)
            print(f"✅ 批量处理完成!")
            print(f"📊 统计信息:")
            print(f"   总计: {stats['total']} 张")
            print(f"   成功: {stats['successful']} 张")
            print(f"   失败: {stats['failed']} 张")
            print(f"   成功率: {stats['success_rate']:.1%}")
    
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()