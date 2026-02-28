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
        寻找图片中主体对象的边界框（优化性能版本）
        
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
        
        # 策略1: 商品图片专用 - 基于亮度差异检测（最高效的方法）
        try:
            # 计算图片边缘的平均亮度（通常是背景色）
            edge_samples = []
            edge_thickness = min(40, min(width, height) // 20)  # 减少边缘采样厚度
            
            # 采样四条边 - 使用跳步采样减少计算量
            step = max(1, min(width, height) // 200)  # 跳步采样
            edge_samples.extend(gray[:edge_thickness, ::step].flatten())  # 上边
            edge_samples.extend(gray[-edge_thickness:, ::step].flatten())  # 下边
            edge_samples.extend(gray[::step, :edge_thickness].flatten())  # 左边
            edge_samples.extend(gray[::step, -edge_thickness:].flatten())  # 右边
            
            bg_brightness = np.median(edge_samples)
            logger.info(f"检测到背景亮度: {bg_brightness:.1f}")
            
            # 根据背景亮度动态调整阈值
            if bg_brightness > 200:  # 白色背景
                # 寻找比背景暗的区域
                threshold_offset = 25  # 降低阈值偏移以提高检测速度
                _, binary = cv2.threshold(gray, bg_brightness - threshold_offset, 255, cv2.THRESH_BINARY_INV)
            else:  # 暗色背景
                # 寻找比背景亮的区域
                threshold_offset = 25
                _, binary = cv2.threshold(gray, bg_brightness + threshold_offset, 255, cv2.THRESH_BINARY)
            
            # 简化形态学处理
            kernel = np.ones((5, 5), np.uint8)  # 减小核大小
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)  # 减少迭代次数
            
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
            logger.warning(f"亮度差异检测失败: {e}")
        
        # 策略2: 边缘检测（只在第一种方法失败时使用）
        if best_contour is None:
            try:
                # 简化的边缘检测
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                edges = cv2.Canny(blurred, 50, 150)  # 使用中等参数，只检测一次
                
                # 膨胀以连接边缘
                kernel = np.ones((3, 3), np.uint8)  # 减小核大小
                edges = cv2.dilate(edges, kernel, iterations=1)  # 减少迭代
                
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
                logger.warning(f"边缘检测失败: {e}")
        
        # 移除了复杂的颜色聚类策略以提升性能
        
        if best_bounds is not None:
            left, top, right, bottom = best_bounds
            
            # 智能边距调整
            obj_width = right - left
            obj_height = bottom - top
            
            # 根据对象大小动态调整边距
            margin_x = max(10, int(obj_width * 0.08))  # 减少边距系数
            margin_y = max(10, int(obj_height * 0.12))  # 减少边距系数
            
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
        logger.warning("对象检测失败，使用保守裁剪策略")
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
    
    def _filter_shadow_from_contour(self, contour, gray, bg_brightness):
        """
        从轮廓中过滤掉阴影部分
        
        Args:
            contour: 检测到的轮廓
            gray: 灰度图像
            bg_brightness: 背景亮度值
            
        Returns:
            过滤后的轮廓
        """
        try:
            # 创建轮廓mask
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            
            # 获取轮廓内的所有像素
            contour_pixels = gray[mask > 0]
            
            if len(contour_pixels) == 0:
                return contour
            
            # 分析轮廓内像素的亮度分布
            # 主体的典型亮度应该比背景暗，但不会太暗（阴影会更暗）
            # 对于白色背景，主体通常在 50-200 之间，阴影通常在 0-100 之间
            
            # 计算亮度分位数
            p10 = np.percentile(contour_pixels, 10)  # 10%分位数（最暗的10%）
            p25 = np.percentile(contour_pixels, 25)  # 25%分位数
            p50 = np.percentile(contour_pixels, 50)  # 中位数
            p75 = np.percentile(contour_pixels, 75)  # 75%分位数
            p90 = np.percentile(contour_pixels, 90)  # 90%分位数（最亮的10%）
            
            # 计算亮度标准差，用于判断亮度分布是否分散
            brightness_std = np.std(contour_pixels)
            
            # 识别主体亮度范围：使用中位数到75%分位数作为主体典型亮度
            # 阴影通常比主体暗很多
            if bg_brightness > 200:  # 白色背景
                # 主体亮度范围：中位数附近
                subject_brightness_min = max(0, p50 - 30)
                
                # 改进的阴影阈值计算：
                # 1. 使用10%分位数（更暗的像素更可能是阴影）
                # 2. 考虑亮度分布：如果分布分散，说明可能有阴影
                # 3. 使用更严格的阈值：中位数减去更大的偏移量
                if brightness_std > 30:  # 亮度分布分散，可能有阴影
                    # 使用更严格的阈值
                    shadow_threshold = min(p10, p25, p50 - 50)
                else:
                    # 亮度分布集中，使用较宽松的阈值
                    shadow_threshold = min(p25, p50 - 40)
                
                # 额外检查：如果最暗的10%明显比主体暗，很可能是阴影
                if p10 < p50 - 60:  # 最暗部分比中位数暗60以上
                    shadow_threshold = min(shadow_threshold, p10 + 20)  # 更严格
            else:  # 暗色背景
                # 对于暗色背景，主体应该比背景亮
                subject_brightness_min = max(bg_brightness + 20, p50 - 30)
                if brightness_std > 30:
                    shadow_threshold = min(p10, p25, p50 - 50)
                else:
                    shadow_threshold = min(p25, p50 - 40)
            
            logger.info(f"轮廓亮度分析: 10%={p10:.1f}, 25%={p25:.1f}, 50%={p50:.1f}, 75%={p75:.1f}, 90%={p90:.1f}, 标准差={brightness_std:.1f}")
            logger.info(f"阴影阈值={shadow_threshold:.1f}")
            
            # 创建过滤后的mask：移除阴影部分
            filtered_mask = mask.copy()
            
            # 获取轮廓的边界框
            x, y, w, h = cv2.boundingRect(contour)
            height, width = gray.shape
            
            # 方法1: 基于亮度的阴影检测（全方位，不限制位置）
            shadow_mask_by_brightness = (gray < shadow_threshold) & (mask > 0)
            
            # 方法2: 使用更智能的阈值，识别浅色阴影
            # 降低标准差阈值，更敏感地检测浅色阴影
            if brightness_std > 20:  # 降低阈值从25到20，更敏感
                # 使用更宽松的阈值来捕获浅色阴影
                light_shadow_threshold = min(p25 + 15, p50 - 25)  # 更宽松的阈值
                # 但只对明显比主体暗的区域应用（降低要求从20到15）
                light_shadow_mask = (gray < light_shadow_threshold) & (gray < p50 - 15) & (mask > 0)
                logger.info(f"浅色阴影检测: 阈值={light_shadow_threshold:.1f}, 标准差={brightness_std:.1f}")
            else:
                light_shadow_mask = np.zeros_like(mask, dtype=bool)
            
            # 方法3: 边缘区域直接检测 - 专门检测轮廓边缘附近的暗色区域
            # 获取轮廓的边界框
            x, y, w, h = cv2.boundingRect(contour)
            contour_left = x
            contour_right = x + w
            contour_top = y
            contour_bottom = y + h
            
            # 定义边缘区域（上下左右各50%的范围）
            edge_margin = min(w, h) * 0.5
            left_edge = (contour_left, contour_left + edge_margin)
            right_edge = (contour_right - edge_margin, contour_right)
            top_edge = (contour_top, contour_top + edge_margin)
            bottom_edge = (contour_bottom - edge_margin, contour_bottom)
            
            # 创建边缘区域mask
            height, width = gray.shape
            y_coords, x_coords = np.ogrid[:height, :width]
            
            is_in_left_edge = (x_coords >= left_edge[0]) & (x_coords <= left_edge[1])
            is_in_right_edge = (x_coords >= right_edge[0]) & (x_coords <= right_edge[1])
            is_in_top_edge = (y_coords >= top_edge[0]) & (y_coords <= top_edge[1])
            is_in_bottom_edge = (y_coords >= bottom_edge[0]) & (y_coords <= bottom_edge[1])
            
            is_in_edge_region = (is_in_left_edge | is_in_right_edge | is_in_top_edge | is_in_bottom_edge) & (mask > 0)
            
            # 在边缘区域使用更宽松的阈值
            edge_shadow_threshold = min(p25 + 20, p50 - 20)  # 更宽松的阈值
            edge_shadow_mask = (gray < edge_shadow_threshold) & (gray < p50 - 10) & is_in_edge_region
            
            logger.info(f"边缘阴影检测: 阈值={edge_shadow_threshold:.1f}, 检测到{np.sum(edge_shadow_mask)}个像素")
            
            # 方法4: 连通性分析 - 识别独立的暗色区域（可能是阴影）
            # 创建二值图像，标记所有暗像素
            dark_pixels = (gray < shadow_threshold) & (mask > 0)
            dark_binary = dark_pixels.astype(np.uint8) * 255
            
            # 查找连通区域
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dark_binary, connectivity=8)
            
            # 分析每个连通区域，判断是否是阴影
            shadow_regions = np.zeros_like(mask, dtype=bool)
            
            if num_labels > 1:  # 有连通区域（除了背景）
                # 计算主体区域的典型亮度（排除最暗和最亮的10%）
                subject_pixels = contour_pixels[(contour_pixels >= p10) & (contour_pixels <= p90)]
                subject_mean_brightness = np.mean(subject_pixels) if len(subject_pixels) > 0 else p50
                
                for label_id in range(1, num_labels):  # 跳过背景（label=0）
                    # 获取该连通区域的统计信息
                    area = stats[label_id, cv2.CC_STAT_AREA]
                    left = stats[label_id, cv2.CC_STAT_LEFT]
                    top = stats[label_id, cv2.CC_STAT_TOP]
                    region_width = stats[label_id, cv2.CC_STAT_WIDTH]
                    region_height = stats[label_id, cv2.CC_STAT_HEIGHT]
                    
                    # 只处理足够大的区域（避免噪声）
                    if area < 50:  # 太小可能是噪声
                        continue
                    
                    # 提取该区域的像素亮度
                    region_mask = (labels == label_id)
                    region_pixels = gray[region_mask]
                    region_mean_brightness = np.mean(region_pixels)
                    
                    # 判断是否是阴影：
                    # 1. 平均亮度明显比主体暗（降低要求，从30降到20）
                    # 2. 区域面积不超过轮廓的40%（放宽要求，从30%到40%）
                    # 3. 区域位置在轮廓边缘附近（扩大范围，从30%到50%）
                    
                    # 计算亮度差异
                    brightness_diff = subject_mean_brightness - region_mean_brightness
                    
                    # 放宽条件：暗20以上即可（原来是30）
                    is_dark_enough = brightness_diff >= 20
                    
                    # 放宽面积限制：允许更大的阴影区域（从30%到40%）
                    area_ratio = area / cv2.contourArea(contour)
                    is_not_too_large = area_ratio < 0.4
                    
                    # 检查是否在边缘附近（扩大范围，从30%到50%）
                    contour_left = x
                    contour_right = x + w
                    contour_top = y
                    contour_bottom = y + h
                    
                    region_center_x = left + region_width / 2
                    region_center_y = top + region_height / 2
                    
                    # 扩大边缘检测范围到50%
                    edge_margin = min(w, h) * 0.5
                    is_near_edge = (
                        region_center_x < contour_left + edge_margin or  # 左边缘
                        region_center_x > contour_right - edge_margin or  # 右边缘
                        region_center_y < contour_top + edge_margin or  # 上边缘
                        region_center_y > contour_bottom - edge_margin  # 下边缘
                    )
                    
                    # 额外检查：如果区域明显比主体暗，即使不在边缘也可能认为是阴影
                    # 但要求亮度差异更大（暗40以上）
                    is_very_dark = brightness_diff >= 40
                    
                    # 如果满足阴影条件，标记为阴影
                    # 条件1: 暗20以上 + 面积合理 + 在边缘附近
                    # 条件2: 暗40以上 + 面积合理（不要求边缘）
                    if (is_dark_enough and is_not_too_large and is_near_edge) or (is_very_dark and is_not_too_large):
                        shadow_regions[region_mask] = True
                        edge_info = "边缘" if is_near_edge else "内部"
                        logger.info(f"识别到阴影区域: 位置({left:.0f},{top:.0f}), 大小{area}px, 平均亮度{region_mean_brightness:.1f}, "
                                  f"主体亮度{subject_mean_brightness:.1f}, 亮度差{brightness_diff:.1f}, "
                                  f"面积占比{area_ratio:.1%}, 位置={edge_info}")
            
            # 合并所有阴影检测结果
            shadow_mask = shadow_mask_by_brightness | light_shadow_mask | edge_shadow_mask | shadow_regions
            
            filtered_mask[shadow_mask] = 0
            
            # 统计移除的像素数量
            removed_pixels = np.sum(shadow_mask)
            total_pixels = np.sum(mask > 0)
            removal_ratio = removed_pixels / total_pixels if total_pixels > 0 else 0
            
            # 分别统计不同方法检测到的阴影
            brightness_removed = np.sum(shadow_mask_by_brightness)
            light_shadow_removed = np.sum(light_shadow_mask)
            edge_shadow_removed = np.sum(edge_shadow_mask)
            region_shadow_removed = np.sum(shadow_regions)
            
            logger.info(f"阴影检测统计: 总像素={total_pixels}, 移除={removed_pixels} ({removal_ratio:.1%})")
            logger.info(f"  亮度检测阴影: {brightness_removed} 像素")
            if light_shadow_removed > 0:
                logger.info(f"  浅色阴影检测: {light_shadow_removed} 像素")
            if edge_shadow_removed > 0:
                logger.info(f"  边缘区域阴影: {edge_shadow_removed} 像素")
            if region_shadow_removed > 0:
                logger.info(f"  连通区域阴影: {region_shadow_removed} 像素")
            
            if removal_ratio > 0.02:  # 降低阈值到2%，让小的阴影也能被识别
                logger.info(f"检测到阴影并移除: 移除了 {removed_pixels} 个像素 ({removal_ratio:.1%})")
                
                # 从过滤后的mask中重新提取轮廓
                contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    # 找到最大的轮廓（应该是主体）
                    filtered_contour = max(contours, key=cv2.contourArea)
                    filtered_area = cv2.contourArea(filtered_contour)
                    original_area = cv2.contourArea(contour)
                    
                    # 验证过滤后的轮廓是否合理（面积不应该太小）
                    if filtered_area > original_area * 0.3:  # 至少保留30%的面积
                        logger.info(f"阴影过滤成功: 原始面积 {original_area:.0f} -> 过滤后 {filtered_area:.0f} ({filtered_area/original_area:.1%})")
                        return filtered_contour
                    else:
                        logger.warning(f"过滤后轮廓面积过小 ({filtered_area/original_area:.1%})，保留原始轮廓")
                        return contour
                else:
                    logger.warning("过滤后未找到轮廓，保留原始轮廓")
                    return contour
            else:
                logger.info("未检测到明显的阴影，保留原始轮廓")
                return contour
                
        except Exception as e:
            logger.warning(f"阴影过滤失败: {e}，保留原始轮廓")
            return contour
    
    def find_object_bounds_on_white_bg(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        在白色背景上寻找对象轮廓边界（专用于最终验证）
        使用更严格的检测确保找到真实的鞋子轮廓
        
        Args:
            image: PIL Image对象（白色背景）
            
        Returns:
            (left, top, right, bottom) 轮廓边界坐标
        """
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 转换为灰度图
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        width, height = image.size
        
        # 使用多种方法找到最准确的轮廓
        best_contour = None
        best_area = 0
        best_bounds = None
        
        # 方法1: 非常严格的阈值检测
        try:
            # 使用更严格的阈值序列，确保只检测到真正的非白色区域
            strict_thresholds = [254, 252, 250, 248, 245]  # 从最严格开始
            
            for white_threshold in strict_thresholds:
                # 创建二值图像
                _, binary = cv2.threshold(gray, white_threshold, 255, cv2.THRESH_BINARY_INV)
                
                # 去除边缘噪声
                border_size = max(3, min(width, height) // 200)
                binary[:border_size, :] = 0
                binary[-border_size:, :] = 0
                binary[:, :border_size] = 0
                binary[:, -border_size:] = 0
                
                # 形态学操作 - 先开运算去除小噪点
                kernel_small = np.ones((2, 2), np.uint8)
                kernel_medium = np.ones((3, 3), np.uint8)
                
                binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small, iterations=1)
                binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
                
                # 查找轮廓
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if not contours:
                    continue
                
                # 找到最大的轮廓
                largest_contour = max(contours, key=cv2.contourArea)
                largest_area = cv2.contourArea(largest_contour)
                
                # 验证面积和形状
                image_area = width * height
                area_ratio = largest_area / image_area
                
                if 0.15 <= area_ratio <= 0.60:
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    aspect_ratio = w / h
                    
                    if 0.5 <= aspect_ratio <= 3.0:
                        bbox_area = w * h
                        fill_ratio = largest_area / bbox_area
                        
                        if 0.40 <= fill_ratio <= 0.85:
                            if largest_area > best_area:
                                best_area = largest_area
                                best_contour = largest_contour
                                logger.info(f"严格检测找到轮廓 (阈值{white_threshold}): 面积{area_ratio:.1%}, 宽高比{aspect_ratio:.2f}, 填充{fill_ratio:.1%}")
                                break
                                
        except Exception as e:
            logger.warning(f"严格阈值检测失败: {e}")
        
        # 方法2: 基于边缘的精确检测（如果严格阈值失败）
        if best_contour is None:
            try:
                logger.info("尝试基于边缘的精确检测")
                
                # 使用Canny边缘检测
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                edges = cv2.Canny(blurred, 30, 100)
                
                # 膨胀边缘以连接断开的部分
                kernel = np.ones((3, 3), np.uint8)
                edges = cv2.dilate(edges, kernel, iterations=1)
                
                # 查找轮廓
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    for contour in contours:
                        area = cv2.contourArea(contour)
                        if area > width * height * 0.1:  # 至少10%面积
                            x, y, w, h = cv2.boundingRect(contour)
                            aspect_ratio = w / h
                            if 0.5 <= aspect_ratio <= 3.0:
                                if area > best_area:
                                    best_area = area
                                    best_contour = contour
                                    logger.info(f"边缘检测找到轮廓: 面积{area/(width*height):.1%}")
                                    
            except Exception as e:
                logger.warning(f"边缘检测失败: {e}")
        
        if best_contour is not None:
            # 从轮廓中获取极值点，并进行额外的精确化处理
            contour_points = best_contour.reshape(-1, 2)
            
            # 基础边界
            left = np.min(contour_points[:, 0])
            right = np.max(contour_points[:, 0])
            top = np.min(contour_points[:, 1])
            bottom = np.max(contour_points[:, 1])
            
            # 精确化边界检测：在边界附近寻找真正的非白色像素
            # 这可以避免轮廓检测时包含过多白色区域
            
            # 左边界精确化：从left开始向右扫描，找到第一个明显非白色的列
            for x in range(max(0, left), min(width, left + 50)):
                col = gray[:, x]
                non_white_pixels = np.sum(col < 245)  # 非白色像素数量
                if non_white_pixels > height * 0.1:  # 至少10%的列是非白色
                    left = x
                    break
            
            # 右边界精确化：从right开始向左扫描
            for x in range(min(width - 1, right), max(0, right - 50), -1):
                col = gray[:, x]
                non_white_pixels = np.sum(col < 245)
                if non_white_pixels > height * 0.1:
                    right = x
                    break
            
            # 上边界精确化：从top开始向下扫描
            for y in range(max(0, top), min(height, top + 30)):
                row = gray[y, :]
                non_white_pixels = np.sum(row < 245)
                if non_white_pixels > width * 0.1:
                    top = y
                    break
            
            # 下边界精确化：从bottom开始向上扫描
            for y in range(min(height - 1, bottom), max(0, bottom - 30), -1):
                row = gray[y, :]
                non_white_pixels = np.sum(row < 245)
                if non_white_pixels > width * 0.1:
                    bottom = y
                    break
            
            # 验证精确化结果
            refined_width = right - left
            refined_height = bottom - top
            
            if refined_width >= 100 and refined_height >= 100:
                logger.info(f"精确轮廓边界: 左{left}, 上{top}, 右{right}, 下{bottom}")
                logger.info(f"精确轮廓尺寸: {refined_width}x{refined_height}")
                return left, top, right, bottom
            else:
                logger.warning(f"精确化后轮廓太小: {refined_width}x{refined_height}")
        
        # 如果所有方法都失败，使用像素级分析
        logger.warning("轮廓检测失败，使用像素级精确分析")
        
        # 使用最严格的阈值找到所有明显非白色的像素
        _, ultra_strict = cv2.threshold(gray, 252, 255, cv2.THRESH_BINARY_INV)
        
        # 找到所有非白色像素的坐标
        nonzero_coords = np.where(ultra_strict > 0)
        
        if len(nonzero_coords[0]) > 0:
            top = np.min(nonzero_coords[0])
            bottom = np.max(nonzero_coords[0])
            left = np.min(nonzero_coords[1])
            right = np.max(nonzero_coords[1])
            
            # 应用小幅收缩，确保不包含边缘白色像素
            margin = 2
            left = min(width - 50, left + margin)
            right = max(50, right - margin)
            top = min(height - 50, top + margin)
            bottom = max(50, bottom - margin)
            
            logger.info(f"像素级边界: 左{left}, 上{top}, 右{right}, 下{bottom}")
            return left, top, right, bottom
        
        # 最后的保守估计
        logger.warning("所有检测方法都失败，返回保守估计")
        margin_w = int(width * 0.25)
        margin_h = int(height * 0.25)
        return margin_w, margin_h, width - margin_w, height - margin_h
    
    def find_object_contour_bounds(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        寻找图片中主体对象的实际轮廓边界（非矩形边界框）
        返回轮廓上最左、最右、最上、最下的像素点坐标
        
        Args:
            image: PIL Image对象
            
        Returns:
            (left, top, right, bottom) 轮廓边界坐标
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
        
        # 策略1: 基于亮度差异检测（适合商品图片）
        try:
            # 计算图片边缘的平均亮度（通常是背景色）
            edge_samples = []
            edge_thickness = min(50, min(width, height) // 20)
            
            # 采样四条边
            edge_samples.extend(gray[:edge_thickness, :].flatten())
            edge_samples.extend(gray[-edge_thickness:, :].flatten())
            edge_samples.extend(gray[:, :edge_thickness].flatten())
            edge_samples.extend(gray[:, -edge_thickness:].flatten())
            
            bg_brightness = np.median(edge_samples)
            logger.info(f"检测到背景亮度: {bg_brightness:.1f}")
            
            # 根据背景亮度动态调整阈值
            if bg_brightness > 200:  # 白色背景
                threshold_offset = 25
                _, binary = cv2.threshold(gray, bg_brightness - threshold_offset, 255, cv2.THRESH_BINARY_INV)
            else:  # 暗色背景
                threshold_offset = 25
                _, binary = cv2.threshold(gray, bg_brightness + threshold_offset, 255, cv2.THRESH_BINARY)
            
            # 形态学处理
            kernel = np.ones((5, 5), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # 去除边缘噪声
            border_size = max(3, min(width, height) // 150)
            binary[:border_size, :] = 0
            binary[-border_size:, :] = 0
            binary[:, :border_size] = 0
            binary[:, -border_size:] = 0
            
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > height * width * 0.05:  # 面积至少占图片的5%
                        if area > best_area:
                            best_area = area
                            best_contour = contour
                            
        except Exception as e:
            logger.warning(f"轮廓检测策略失败: {e}")
        
        if best_contour is not None:
            # 尝试过滤阴影部分
            # 需要先获取bg_brightness，如果try块失败则使用默认值
            try:
                edge_samples = []
                edge_thickness = min(50, min(width, height) // 20)
                edge_samples.extend(gray[:edge_thickness, :].flatten())
                edge_samples.extend(gray[-edge_thickness:, :].flatten())
                edge_samples.extend(gray[:, :edge_thickness].flatten())
                edge_samples.extend(gray[:, -edge_thickness:].flatten())
                bg_brightness = np.median(edge_samples)
            except:
                bg_brightness = 255  # 默认白色背景
            
            best_contour = self._filter_shadow_from_contour(best_contour, gray, bg_brightness)
            
            # 从轮廓中找到极值点
            contour_points = best_contour.reshape(-1, 2)
            
            left = np.min(contour_points[:, 0])    # 最左边的x坐标
            right = np.max(contour_points[:, 0])   # 最右边的x坐标
            top = np.min(contour_points[:, 1])     # 最上边的y坐标
            bottom = np.max(contour_points[:, 1])  # 最下边的y坐标
            
            # 验证检测结果的合理性
            contour_width = right - left
            contour_height = bottom - top
            contour_area = cv2.contourArea(best_contour)
            image_area = width * height
            
            area_ratio = contour_area / image_area
            logger.info(f"检测到轮廓边界（已过滤阴影）: 左{left}, 上{top}, 右{right}, 下{bottom}")
            logger.info(f"轮廓尺寸: {contour_width}x{contour_height}, 轮廓面积占比: {area_ratio:.1%}")
            
            # 如果检测结果合理，返回轮廓边界
            if 0.05 <= area_ratio <= 0.9:
                return left, top, right, bottom
            else:
                logger.warning(f"检测到的轮廓面积占比异常: {area_ratio:.1%}, 使用保守策略")
        
        # 如果轮廓检测失败，回退到矩形边界框检测
        logger.warning("轮廓检测失败，使用矩形边界框作为替代")
        return self.find_object_bounds(image)
    
    def smart_crop_with_margins(self, image: Image.Image, left_right_margin_ratio: float = 0.1, 
                               top_bottom_margin_ratio: float = 0.15, target_ratio: str = 'auto',
                               min_resolution: int = 800, fast_mode: bool = True) -> Image.Image:
        """
        智能裁剪/扩展图片，确保鞋子居中显示且左右边距各占指定比例
        
        Args:
            image: PIL Image对象
            left_right_margin_ratio: 左右边距各占图片宽度的比例 (默认10%)
            top_bottom_margin_ratio: 上下最小边距比例 (默认15%)
            target_ratio: 目标比例 '4:3', '3:4', 'auto'
            min_resolution: 最小分辨率（短边）
            fast_mode: 是否使用快速模式（默认True，大幅提升性能）
            
        Returns:
            处理后的PIL Image对象
        """
        # 先找到鞋子边界 - 使用轮廓检测
        left, top, right, bottom = self.find_object_contour_bounds(image)
        object_width = right - left
        object_height = bottom - top
        
        logger.info(f"检测到鞋子轮廓边界: 左{left}, 上{top}, 右{right}, 下{bottom}")
        logger.info(f"鞋子轮廓尺寸: {object_width}x{object_height}")
        
        # 检查鞋子轮廓是否太靠近原图边界，如果是则需要扩展画布
        original_width, original_height = image.size
        
        # 检查鞋子是否贴边
        margin_threshold = 50  # 如果鞋子距离边界小于50像素，认为是贴边
        is_touching_left = left < margin_threshold
        is_touching_right = (original_width - right) < margin_threshold
        is_touching_top = top < margin_threshold
        is_touching_bottom = (original_height - bottom) < margin_threshold
        
        if is_touching_left or is_touching_right or is_touching_top or is_touching_bottom:
            logger.info(f"检测到鞋子贴边: 左{is_touching_left}, 右{is_touching_right}, 上{is_touching_top}, 下{is_touching_bottom}")
            logger.info("将扩展原图画布以确保完整的鞋子轮廓边距")
            
            # 检测原图的背景颜色 - 传递快速模式参数
            background_color = self.detect_background_color(image, fast_mode=fast_mode)
            logger.info(f"将使用背景颜色 RGB{background_color} 填充扩展区域")
            
            # 计算需要扩展的边距
            # 基于鞋子尺寸计算合理的边距
            min_margin_x = max(object_width * 0.2, 100)  # 至少是鞋子宽度的20%或100像素
            min_margin_y = max(object_height * 0.2, 100)  # 至少是鞋子高度的20%或100像素
            
            # 计算新的画布尺寸
            expand_left = max(0, min_margin_x - left) if is_touching_left else 0
            expand_right = max(0, min_margin_x - (original_width - right)) if is_touching_right else 0
            expand_top = max(0, min_margin_y - top) if is_touching_top else 0
            expand_bottom = max(0, min_margin_y - (original_height - bottom)) if is_touching_bottom else 0
            
            new_canvas_width = int(original_width + expand_left + expand_right)
            new_canvas_height = int(original_height + expand_top + expand_bottom)
            
            logger.info(f"扩展画布: {original_width}x{original_height} -> {new_canvas_width}x{new_canvas_height}")
            logger.info(f"扩展边距: 左{expand_left}, 右{expand_right}, 上{expand_top}, 下{expand_bottom}")
            
            # 创建扩展的背景色画布
            expanded_canvas = Image.new('RGB', (new_canvas_width, new_canvas_height), background_color)
            
            # 将原图粘贴到扩展画布上
            paste_x = int(expand_left)
            paste_y = int(expand_top)
            expanded_canvas.paste(image, (paste_x, paste_y))
            
            # 更新鞋子在新画布中的坐标
            left += expand_left
            right += expand_left
            top += expand_top
            bottom += expand_top
            object_width = right - left  # 宽度不变
            object_height = bottom - top  # 高度不变
            
            # 使用扩展后的画布作为输入
            image = expanded_canvas
            logger.info(f"更新后的鞋子坐标: 左{left}, 上{top}, 右{right}, 下{bottom}")
        else:
            # 即使不需要扩展，也检测背景颜色以供后续使用 - 传递快速模式参数
            background_color = self.detect_background_color(image, fast_mode=fast_mode)
            logger.info(f"检测到原图背景颜色: RGB{background_color}")
        
        # 确定目标比例（新的智能选择逻辑）
        # 高宽比 = object_height / object_width
        aspect_ratio = object_height / object_width if object_width > 0 else 1.0
        keep_original_ratio = False  # 是否保持原比例
        
        if target_ratio == 'auto':
            if aspect_ratio < 0.75:
                # 高宽比 < 0.75：很宽的图，使用 4:3 横图比例
                target_ratio = '4:3'
                logger.info(f"检测到宽图（高宽比 {aspect_ratio:.2f} < 0.75），使用 4:3 横图比例")
            elif aspect_ratio >= 0.75 and aspect_ratio < 1.0:
                # 0.75 <= 高宽比 < 1：接近方形，保持原比例加边距
                keep_original_ratio = True
                logger.info(f"检测到接近方形图（高宽比 {aspect_ratio:.2f} 在 0.75-1.0 之间），保持原比例加边距")
            else:
                # 高宽比 >= 1：很高的图，使用 3:4 竖图比例
                target_ratio = '3:4'
                logger.info(f"检测到高图（高宽比 {aspect_ratio:.2f} >= 1.0），使用 3:4 竖图比例")
        else:
            # 用户指定了比例，使用指定比例
            logger.info(f"使用用户指定的比例: {target_ratio}")
        
        # 解析目标比例
        if keep_original_ratio:
            # 保持原比例模式：使用对象的实际宽高比
            object_aspect_ratio = object_height / object_width if object_width > 0 else 1.0
            logger.info(f"保持原比例模式: 宽高比 {object_aspect_ratio:.2f} (约 {object_width/object_height:.2f}:1)")
        elif target_ratio == '4:3':
            ratio_w, ratio_h = 4, 3
        elif target_ratio == '3:4':
            ratio_w, ratio_h = 3, 4
        else:
            raise ValueError(f"不支持的比例: {target_ratio}")
        
        # 计算理想画布尺寸，确保10%边距
        if keep_original_ratio:
            # 保持原比例：直接按轮廓尺寸加边距，保持对象的宽高比
            ideal_canvas_width = object_width / (1 - 2 * left_right_margin_ratio)
            ideal_canvas_height = ideal_canvas_width * object_aspect_ratio  # 保持原宽高比
        else:
            # 固定比例模式：需要同时考虑宽度和高度，确保鞋子完整显示
            # 对于竖图（高宽比 >= 1.0），上下边距应该更小
            is_vertical_image = aspect_ratio >= 1.0
            
            if is_vertical_image:
                # 竖图：上下边距使用更小的比例（3%），左右边距保持10%
                vertical_margin_ratio = left_right_margin_ratio * 0.3  # 上下边距是左右边距的30%（3%）
                horizontal_margin_ratio = left_right_margin_ratio  # 左右边距保持10%
                logger.info(f"竖图模式: 左右边距={horizontal_margin_ratio:.1%}, 上下边距={vertical_margin_ratio:.1%}")
            else:
                # 横图：统一使用左右边距比例
                vertical_margin_ratio = left_right_margin_ratio
                horizontal_margin_ratio = left_right_margin_ratio
                logger.info(f"横图模式: 统一边距={horizontal_margin_ratio:.1%}")
            
            # 方法1：基于宽度计算（确保左右边距）
            ideal_canvas_width_by_width = object_width / (1 - 2 * horizontal_margin_ratio)
            ideal_canvas_height_by_width = ideal_canvas_width_by_width * ratio_h / ratio_w
            
            # 方法2：基于高度计算（确保上下边距，防止鞋子被裁剪）
            # 对于竖图，使用更小的上下边距
            ideal_canvas_height_by_height = object_height / (1 - 2 * vertical_margin_ratio)
            ideal_canvas_width_by_height = ideal_canvas_height_by_height * ratio_w / ratio_h
            
            # 选择能完整容纳鞋子且边距更合理的方案
            # 检查基于宽度计算的方案是否能容纳完整高度（留最小边距）
            # 对于竖图，使用更小的边距要求
            margin_requirement_factor = 0.6 if is_vertical_image else 0.8  # 竖图使用60%的边距要求，横图80%
            min_required_height = object_height * (1 + 2 * vertical_margin_ratio * margin_requirement_factor)
            if ideal_canvas_height_by_width >= min_required_height:
                # 基于宽度的方案足够，使用它（边距更合理）
                ideal_canvas_width = ideal_canvas_width_by_width
                ideal_canvas_height = ideal_canvas_height_by_width
                logger.info(f"基于宽度计算画布: {ideal_canvas_width:.0f}x{ideal_canvas_height:.0f}")
            else:
                # 基于宽度的方案高度不够，使用基于高度的方案
                ideal_canvas_width = ideal_canvas_width_by_height
                ideal_canvas_height = ideal_canvas_height_by_height
                logger.info(f"基于高度计算画布（防止裁剪）: {ideal_canvas_width:.0f}x{ideal_canvas_height:.0f}")
                logger.info(f"  原因: 基于宽度的方案高度 {ideal_canvas_height_by_width:.0f}px 不足以容纳鞋子高度 {object_height}px (需要至少 {min_required_height:.0f}px)")
        
        # 边距合理性检查：防止画布过大导致边距过大
        original_width, original_height = image.size
        
        # 提前定义竖图边距变量，供后续使用
        is_vertical_for_check = aspect_ratio >= 1.0
        if is_vertical_for_check:
            vertical_margin_ratio_for_check = left_right_margin_ratio * 0.3  # 竖图上下边距3%（百分比）
            # 使用最小像素值（至少20像素）和百分比的最大值
            min_margin_pixels_for_check = max(20, int(object_height * 0.02))  # 至少20像素或对象高度的2%
            # 计算实际使用的边距比例（取较大者）
            min_margin_ratio_by_pixels = min_margin_pixels_for_check / object_height if object_height > 0 else vertical_margin_ratio_for_check
            vertical_margin_for_check = max(min_margin_ratio_by_pixels, vertical_margin_ratio_for_check)
        else:
            vertical_margin_ratio_for_check = left_right_margin_ratio  # 横图上下边距10%
            vertical_margin_for_check = left_right_margin_ratio  # 横图上下边距10%
        
        # 如果理想画布比原图大太多，进行调整
        max_scale_factor = 2.0  # 最大允许放大2倍
        if ideal_canvas_width > original_width * max_scale_factor:
            logger.warning(f"理想画布过大 ({ideal_canvas_width:.0f}px > {original_width * max_scale_factor:.0f}px)，进行缩放调整")
            scale_down = original_width * max_scale_factor / ideal_canvas_width
            ideal_canvas_width = original_width * max_scale_factor
            if keep_original_ratio:
                ideal_canvas_height = ideal_canvas_width * object_aspect_ratio
            else:
                ideal_canvas_height = ideal_canvas_width * ratio_h / ratio_w
            
            # 验证缩放后的高度是否还能保证边距（特别是竖图）
            if is_vertical_for_check:
                # 对于竖图，确保缩放后的高度仍能满足3%边距要求
                min_height_with_margin = object_height / (1 - 2 * vertical_margin_for_check)
                if ideal_canvas_height < min_height_with_margin:
                    logger.warning(f"缩放后高度 {ideal_canvas_height:.0f}px 不足以保证3%边距 (需要 {min_height_with_margin:.0f}px)，调整高度")
                    ideal_canvas_height = min_height_with_margin
                    if keep_original_ratio:
                        ideal_canvas_width = ideal_canvas_height / object_aspect_ratio
                    else:
                        ideal_canvas_width = ideal_canvas_height * ratio_w / ratio_h
            
            logger.info(f"调整后理想画布: {ideal_canvas_width:.0f}x{ideal_canvas_height:.0f}")
        
        logger.info(f"理想画布计算: 鞋子{object_width}x{object_height} -> 画布{ideal_canvas_width:.0f}x{ideal_canvas_height:.0f}")
        
        # 检查是否满足最小分辨率要求 - 增加自适应逻辑
        # original_width, original_height 已在上面定义
        original_min_size = min(original_width, original_height)
        
        # 自适应最小分辨率：不应超过原图的80%
        adaptive_min_resolution = min(min_resolution, int(original_min_size * 0.8))
        logger.info(f"最小分辨率: 设定{min_resolution} -> 自适应{adaptive_min_resolution} (原图最小边: {original_min_size})")
        
        if keep_original_ratio:
            # 保持原比例：确保短边满足最小分辨率
            if object_width < object_height:
                # 宽度是短边
                min_width = adaptive_min_resolution
                min_height = min_width * object_aspect_ratio
            else:
                # 高度是短边
                min_height = adaptive_min_resolution
                min_width = min_height / object_aspect_ratio
        else:
            min_width = adaptive_min_resolution if ratio_w >= ratio_h else adaptive_min_resolution * ratio_w / ratio_h
            min_height = adaptive_min_resolution if ratio_h >= ratio_w else adaptive_min_resolution * ratio_h / ratio_w
        
        # 优先使用理想尺寸来确保边距准确
        # 但需要确保画布高度至少能容纳完整的鞋子（加上最小边距）
        # is_vertical_for_check 和 vertical_margin_for_check 已在上面定义
        if is_vertical_for_check:
            # 确保至少有完整的上下边距（使用最小像素值或百分比的最大值）
            min_required_height = object_height / (1 - 2 * vertical_margin_for_check)
            min_required_height_by_pixels = object_height + min_margin_pixels_for_check * 2
            min_required_height = max(min_required_height, min_required_height_by_pixels)
            logger.info(f"竖图边距检查: 最小边距={min_margin_pixels_for_check}px 或 {vertical_margin_ratio_for_check:.1%}，实际使用={vertical_margin_for_check:.1%}，最小高度={min_required_height:.0f}px")
        else:
            margin_requirement_factor = 0.8  # 横图使用80%的边距要求
            min_required_height = object_height * (1 + 2 * vertical_margin_for_check * margin_requirement_factor)
        
        final_canvas_width = max(ideal_canvas_width, min_width)
        if keep_original_ratio:
            final_canvas_height = final_canvas_width * object_aspect_ratio
        else:
            final_canvas_height = final_canvas_width * ratio_h / ratio_w
        
        # 确保高度至少能容纳完整的鞋子
        if final_canvas_height < min_required_height:
            logger.warning(f"画布高度 {final_canvas_height:.0f}px 不足以容纳鞋子高度 {object_height}px，调整为 {min_required_height:.0f}px")
            final_canvas_height = min_required_height
            if keep_original_ratio:
                final_canvas_width = final_canvas_height / object_aspect_ratio
            else:
                final_canvas_width = final_canvas_height * ratio_w / ratio_h
        
        # 如果需要调整到最小分辨率，重新计算以保持比例（但前提是不裁剪鞋子）
        if final_canvas_height < min_height:
            # 检查应用最小分辨率后是否还能容纳鞋子（包括边距）
            test_height = min_height
            if keep_original_ratio:
                test_width = test_height / object_aspect_ratio
            else:
                test_width = test_height * ratio_w / ratio_h
            
            # 对于竖图，需要确保最小分辨率也满足3%边距要求
            if is_vertical_for_check:
                min_height_with_margin = object_height / (1 - 2 * vertical_margin_for_check)
                if test_height < min_height_with_margin:
                    logger.warning(f"最小分辨率 {test_height}px 不足以满足3%边距要求 (需要 {min_height_with_margin:.0f}px)，使用边距要求的高度")
                    test_height = min_height_with_margin
                    if keep_original_ratio:
                        test_width = test_height / object_aspect_ratio
                    else:
                        test_width = test_height * ratio_w / ratio_h
            
            # 如果应用最小分辨率后仍能容纳鞋子，则应用
            if test_height >= min_required_height:
                final_canvas_height = int(test_height)
                if keep_original_ratio:
                    final_canvas_width = int(final_canvas_height / object_aspect_ratio)
                else:
                    final_canvas_width = int(final_canvas_height * ratio_w / ratio_h)
                logger.info(f"应用最小分辨率: 画布尺寸调整为 {final_canvas_width}x{final_canvas_height}")
            else:
                # 如果应用最小分辨率会导致裁剪，保持当前尺寸
                logger.warning(f"应用最小分辨率 {min_height}px 会导致鞋子被裁剪，保持当前尺寸 {final_canvas_height:.0f}px")
        
        final_canvas_width = int(final_canvas_width)
        final_canvas_height = int(final_canvas_height)
        
        logger.info(f"目标画布尺寸: {final_canvas_width}x{final_canvas_height} (比例: {target_ratio})")
        
        # 迭代调整优化：减少不必要的多次调整
        max_iterations = 2  # 减少迭代次数以提升性能（从3改为2）
        best_result = None
        best_margin_error = float('inf')
        
        for iteration in range(max_iterations):
            logger.info(f"第 {iteration + 1} 次调整")
            
            # 计算鞋子在画布中的目标中心位置
            target_shoe_center_x = final_canvas_width / 2
            
            # 对于竖图，确保上下边距均衡且都至少是3%（或最小像素值）
            # 对于横图，使用5.5:4.5的上下比例定位，让鞋子稍微靠下
            if is_vertical_for_check:
                # 竖图：使用百分比和最小像素值的较大者，确保边距足够
                # 统一使用对象高度的2%或画布高度的1.5%，取较大者
                vertical_margin_ratio = left_right_margin_ratio * 0.3  # 1.5%（因为left_right_margin_ratio是5%）
                min_margin_pixels_by_object = max(20, int(object_height * 0.02))  # 至少20像素或对象高度的2%
                min_margin_by_ratio = final_canvas_height * vertical_margin_ratio  # 画布高度的1.5%
                min_margin_required = max(min_margin_pixels_by_object, min_margin_by_ratio)  # 使用较大者
                logger.info(f"竖图边距检查: 最小边距={min_margin_pixels_by_object}px (对象高度2%) 或 {min_margin_by_ratio:.0f}px (画布高度1.5%)，实际使用={min_margin_required:.0f}px ({min_margin_required/final_canvas_height:.1%})")
                
                # 计算理想的总边距
                ideal_total_margin = final_canvas_height - object_height
                
                # 计算需要的最小总边距（上下各需要min_margin_required）
                min_total_margin_required = min_margin_required * 2
                
                # 如果总边距不足，需要扩展画布
                if ideal_total_margin < min_total_margin_required:
                    additional_margin = min_total_margin_required - ideal_total_margin
                    final_canvas_height = int(final_canvas_height + additional_margin)
                    ideal_total_margin = final_canvas_height - object_height
                    logger.warning(f"竖图边距不足，扩展画布高度 {additional_margin:.0f}px 以确保足够边距")
                    logger.info(f"  扩展后画布高度: {final_canvas_height}px, 总边距: {ideal_total_margin:.0f}px")
                
                # 强制使用画布中心，确保上下边距完全均衡（50%:50%）
                ideal_top_margin = ideal_total_margin / 2
                ideal_bottom_margin = ideal_total_margin / 2
                
                # 验证边距是否满足最小要求
                if ideal_top_margin < min_margin_required or ideal_bottom_margin < min_margin_required:
                    # 如果均衡分配后仍不足，再次扩展
                    deficit = max(min_margin_required - ideal_top_margin, min_margin_required - ideal_bottom_margin)
                    if deficit > 0:
                        final_canvas_height = int(final_canvas_height + deficit * 2)
                        ideal_total_margin = final_canvas_height - object_height
                        ideal_top_margin = ideal_total_margin / 2
                        ideal_bottom_margin = ideal_total_margin / 2
                        logger.warning(f"竖图边距仍不足，再次扩展画布 {deficit * 2:.0f}px")
                
                # 使用画布中心作为目标中心位置，确保完全均衡
                target_shoe_center_y = final_canvas_height / 2
                
                # 验证计算是否正确
                calculated_bottom_margin = final_canvas_height - (target_shoe_center_y + object_height / 2)
                calculated_top_margin = target_shoe_center_y - object_height / 2
                margin_diff = abs(calculated_top_margin - calculated_bottom_margin)
                
                logger.info(f"竖图边距计算:")
                logger.info(f"  画布高度: {final_canvas_height}px")
                logger.info(f"  边距标准: 对象高度2%={min_margin_pixels_by_object}px 或 画布高度1.5%={min_margin_by_ratio:.0f}px，实际使用={min_margin_required:.0f}px ({min_margin_required/final_canvas_height:.1%})")
                logger.info(f"  目标中心Y: {target_shoe_center_y:.0f}px (画布中心)")
                logger.info(f"  计算的上边距: {calculated_top_margin:.0f}px ({calculated_top_margin/final_canvas_height:.1%})")
                logger.info(f"  计算的下边距: {calculated_bottom_margin:.0f}px ({calculated_bottom_margin/final_canvas_height:.1%})")
                logger.info(f"  边距差异: {margin_diff:.0f}px ({margin_diff/final_canvas_height:.1%})")
            else:
                # 横图：使用5.5:4.5的上下比例定位，让鞋子稍微靠下
                target_top_ratio = 5.5 / (5.5 + 4.5)  # = 0.55 = 55%
                target_bottom_ratio = 4.5 / (5.5 + 4.5)  # = 0.45 = 45%
                
                # 根据鞋子高度和目标比例计算理想的中心位置
                ideal_total_margin = final_canvas_height - object_height
                ideal_top_margin = ideal_total_margin * target_top_ratio
                target_shoe_center_y = ideal_top_margin + object_height / 2
            
            # 原图中鞋子的中心位置
            original_shoe_center_x = (left + right) / 2
            original_shoe_center_y = (top + bottom) / 2
            
            # 计算粘贴位置，使鞋子中心对齐到画布中心
            paste_x = int(target_shoe_center_x - original_shoe_center_x)
            paste_y = int(target_shoe_center_y - original_shoe_center_y)
            
            # 计算实际的上下边距
            actual_top_margin_calc = target_shoe_center_y - object_height / 2
            actual_bottom_margin_calc = final_canvas_height - (target_shoe_center_y + object_height / 2)
            
            logger.info(f"  鞋子原图中心: ({original_shoe_center_x:.0f}, {original_shoe_center_y:.0f})")
            if is_vertical_for_check:
                logger.info(f"  画布目标中心: ({target_shoe_center_x:.0f}, {target_shoe_center_y:.0f}) [竖图模式: 上下边距各3%]")
                logger.info(f"  预期边距: 上{actual_top_margin_calc:.0f}px ({actual_top_margin_calc/final_canvas_height:.1%}), 下{actual_bottom_margin_calc:.0f}px ({actual_bottom_margin_calc/final_canvas_height:.1%})")
            else:
                logger.info(f"  画布目标中心: ({target_shoe_center_x:.0f}, {target_shoe_center_y:.0f}) [5.5:4.5比例定位]")
            logger.info(f"  粘贴位置: ({paste_x}, {paste_y})")
            
            # 处理原图的粘贴和裁剪
            source_image = image
            source_width, source_height = source_image.size
            
            # 计算需要从原图中提取的区域
            src_left = max(0, -paste_x)
            src_top = max(0, -paste_y)
            src_right = min(source_width, src_left + final_canvas_width - max(0, paste_x))
            src_bottom = min(source_height, src_top + final_canvas_height - max(0, paste_y))
            
            # 计算在新画布上的粘贴位置
            canvas_paste_x = max(0, paste_x)
            canvas_paste_y = max(0, paste_y)
            
            # 处理粘贴位置为负数的情况
            top_extension = 0
            if paste_y < 0:
                if is_vertical_for_check:
                    # 竖图：需要向上扩展画布
                    top_extension = int(-paste_y)
                    # 调整粘贴位置，使其在扩展后的画布上从顶部开始
                    canvas_paste_y = 0
                    logger.info(f"  粘贴位置Y为负数 ({paste_y:.0f}px)，需要扩展画布顶部 {top_extension}px")
                else:
                    # 横图：不扩展画布，保持原来的提取逻辑
                    # 粘贴位置从画布顶部开始，但保持原来的src_top计算（包含鞋子）
                    canvas_paste_y = 0
                    logger.info(f"  粘贴位置Y为负数 ({paste_y:.0f}px)，横图不扩展画布，保持原图提取区域")
            
            # 对于竖图，特别检查：如果原图不够高，需要确保底部边距
            adjusted_canvas_height = final_canvas_height + top_extension
            adjusted_canvas_width = final_canvas_width
            
            # 如果扩展了画布高度，对于竖图（3:4），需要调整宽度以保持比例
            # 横图不需要调整，使用原来的方式
            if top_extension > 0 and is_vertical_for_check and not keep_original_ratio:
                # 竖图3:4比例：宽度 = 高度 * 3 / 4
                ideal_width_for_height = int(adjusted_canvas_height * ratio_w / ratio_h)
                if abs(ideal_width_for_height - adjusted_canvas_width) > 1:
                    adjusted_canvas_width = ideal_width_for_height
                    logger.info(f"  调整画布宽度以保持3:4比例: {final_canvas_width} -> {adjusted_canvas_width} (高度: {adjusted_canvas_height})")
            if is_vertical_for_check:
                # 计算实际能提取的高度
                extracted_height = src_bottom - src_top
                needed_height = final_canvas_height - canvas_paste_y
                
                # 如果提取的高度不够，说明原图不够高，需要调整粘贴位置以确保底部边距
                if extracted_height < needed_height:
                    # 计算缺失的高度
                    height_deficit = needed_height - extracted_height
                    
                    # 如果缺失的高度不大（小于画布高度的10%），可以向上调整粘贴位置
                    # 这样可以保证底部边距，但可能会稍微减少顶部边距
                    if height_deficit < final_canvas_height * 0.1:
                        canvas_paste_y = max(0, canvas_paste_y - height_deficit)
                        logger.info(f"  原图高度不足，向上调整粘贴位置 {height_deficit:.0f}px 以确保底部边距")
                    else:
                        # 如果缺失太多，需要扩展画布高度
                        logger.warning(f"  原图高度严重不足 (缺失 {height_deficit:.0f}px)，扩展画布")
                        # 扩展画布高度
                        adjusted_canvas_height = int(final_canvas_height + height_deficit)
                        # 对于竖图（3:4），调整宽度以保持比例
                        # 横图不需要调整，使用原来的方式
                        if is_vertical_for_check and not keep_original_ratio:
                            ideal_width_for_height = int(adjusted_canvas_height * ratio_w / ratio_h)
                            if abs(ideal_width_for_height - adjusted_canvas_width) > 1:
                                adjusted_canvas_width = ideal_width_for_height
                                logger.info(f"  调整画布宽度以保持3:4比例: {final_canvas_width} -> {adjusted_canvas_width} (高度: {adjusted_canvas_height})")
                        logger.info(f"  扩展画布高度到: {adjusted_canvas_width}x{adjusted_canvas_height}")
            
            # 创建背景色的新画布（使用调整后的高度和宽度，包括顶部扩展）
            new_canvas = Image.new('RGB', (adjusted_canvas_width, adjusted_canvas_height), background_color)
            
            # 提取原图需要的部分
            if src_left < src_right and src_top < src_bottom:
                cropped_source = source_image.crop((src_left, src_top, src_right, src_bottom))
                
                # 确保格式正确
                if cropped_source.mode != 'RGB':
                    if cropped_source.mode in ('RGBA', 'LA'):
                        temp_bg = Image.new('RGB', cropped_source.size, background_color)
                        temp_bg.paste(cropped_source, mask=cropped_source.split()[-1] if cropped_source.mode == 'RGBA' else None)
                        cropped_source = temp_bg
                    else:
                        cropped_source = cropped_source.convert('RGB')
                
                # 如果扩展了顶部，调整粘贴位置（在扩展后的画布上，粘贴位置应该加上顶部扩展的高度）
                actual_paste_y = canvas_paste_y + top_extension
                
                # 粘贴到新画布
                new_canvas.paste(cropped_source, (canvas_paste_x, actual_paste_y))
                
                # 对于竖图，验证上下边距并确保均衡
                if is_vertical_for_check:
                    # 计算粘贴后的实际上下边距（考虑顶部扩展，actual_paste_y已在上面定义）
                    paste_bottom = actual_paste_y + cropped_source.height
                    top_margin_actual = actual_paste_y
                    bottom_margin_actual = adjusted_canvas_height - paste_bottom
                    
                    # 使用最小像素值（至少20像素）和百分比的最大值
                    # 统一使用对象高度的2%或画布高度的1.5%，取较大者（与计算阶段保持一致）
                    min_margin_pixels_by_object = max(20, int(cropped_source.height * 0.02))  # 至少20像素或对象高度的2%
                    target_margin_by_ratio = adjusted_canvas_height * vertical_margin_ratio_for_check  # 画布高度的1.5%
                    target_margin = max(min_margin_pixels_by_object, target_margin_by_ratio)  # 使用较大者
                    
                    # 记录使用的边距标准
                    if target_margin == min_margin_pixels_by_object:
                        margin_source = f"对象高度2% ({min_margin_pixels_by_object}px)"
                    else:
                        margin_source = f"画布高度1.5% ({target_margin_by_ratio:.0f}px)"
                    logger.info(f"  边距标准: {margin_source}，实际使用={target_margin:.0f}px")
                    
                    # 计算上下边距的差异
                    margin_diff = abs(top_margin_actual - bottom_margin_actual)
                    margin_diff_ratio = margin_diff / adjusted_canvas_height if adjusted_canvas_height > 0 else 0
                    
                    # 检查是否需要调整以保持均衡
                    needs_adjustment = False
                    adjustment = 0
                    
                    # 如果上下边距差异超过5像素或1%，需要调整
                    if margin_diff > 5 or margin_diff_ratio > 0.01:
                        # 计算理想的中心位置（使上下边距完全均衡）
                        ideal_center_y = adjusted_canvas_height / 2
                        current_center_y = actual_paste_y + cropped_source.height / 2  # 使用实际粘贴位置
                        ideal_offset = ideal_center_y - current_center_y
                        
                        # 如果偏移超过5像素，直接移动到理想位置（100%移动，确保完全均衡）
                        if abs(ideal_offset) > 5:
                            adjustment = int(ideal_offset)  # 直接移动到理想位置，确保完全均衡
                            needs_adjustment = True
                            logger.info(f"  检测到上下边距不均衡: 上{top_margin_actual:.0f}px ({top_margin_actual/adjusted_canvas_height:.1%}), 下{bottom_margin_actual:.0f}px ({bottom_margin_actual/adjusted_canvas_height:.1%}), 差异{margin_diff:.0f}px，将移动到理想位置")
                    
                    # 如果底部边距不足，也需要调整
                    if bottom_margin_actual < target_margin:
                        bottom_adjustment = target_margin - bottom_margin_actual
                        if not needs_adjustment or abs(bottom_adjustment) > abs(adjustment):
                            adjustment = -int(bottom_adjustment)  # 向上移动
                            needs_adjustment = True
                            logger.warning(f"  粘贴后底部边距不足: {bottom_margin_actual:.0f}px < 目标 {target_margin:.0f}px (最小{min_margin_pixels_by_object}px 或 {vertical_margin_ratio_for_check:.1%})")
                    
                    # 如果顶部边距不足，也需要调整
                    if top_margin_actual < target_margin:
                        top_adjustment = target_margin - top_margin_actual
                        if not needs_adjustment or abs(top_adjustment) > abs(adjustment):
                            adjustment = int(top_adjustment)  # 向下移动
                            needs_adjustment = True
                            logger.warning(f"  粘贴后顶部边距不足: {top_margin_actual:.0f}px < 目标 {target_margin:.0f}px (最小{min_margin_pixels_by_object}px 或 {vertical_margin_ratio_for_check:.1%})")
                    
                    # 执行调整（迭代调整，确保完全均衡）
                    max_adjustment_iterations = 3  # 最多调整3次
                    for iteration in range(max_adjustment_iterations):
                        if not needs_adjustment or adjustment == 0:
                            break
                            
                        new_actual_paste_y = actual_paste_y + adjustment
                        # 检查调整后是否在有效范围内
                        if new_actual_paste_y >= 0 and new_actual_paste_y + cropped_source.height <= adjusted_canvas_height:
                            # 更新实际粘贴位置
                            actual_paste_y = new_actual_paste_y
                            canvas_paste_y = actual_paste_y - top_extension
                            # 重新创建画布并粘贴
                            new_canvas = Image.new('RGB', (adjusted_canvas_width, adjusted_canvas_height), background_color)
                            new_canvas.paste(cropped_source, (canvas_paste_x, actual_paste_y))
                            logger.info(f"  调整粘贴位置 {adjustment:+.0f}px 以均衡上下边距 (迭代 {iteration + 1})")
                            
                            # 重新计算边距，检查是否还需要调整
                            paste_bottom = actual_paste_y + cropped_source.height
                            top_margin_actual = actual_paste_y
                            bottom_margin_actual = adjusted_canvas_height - paste_bottom
                            margin_diff = abs(top_margin_actual - bottom_margin_actual)
                            
                            # 如果边距已经均衡（差异小于2像素），停止调整
                            if margin_diff < 2:
                                break
                            
                            # 继续调整
                            ideal_center_y = adjusted_canvas_height / 2
                            current_center_y = actual_paste_y + cropped_source.height / 2
                            ideal_offset = ideal_center_y - current_center_y
                            adjustment = int(ideal_offset)
                        elif adjustment < 0:
                            # 如果无法向上调整（上边距大、下边距小），扩展画布底部
                            # 计算需要扩展多少，然后重新计算理想位置使上下边距完全均衡
                            # 理想位置：上下边距相等 = (画布高度 - 鞋子高度) / 2
                            # 当前上边距 = actual_paste_y，需要扩展到：2 * actual_paste_y + 鞋子高度
                            ideal_total_height = 2 * actual_paste_y + cropped_source.height
                            additional_bottom = max(int(-adjustment), int(ideal_total_height - adjusted_canvas_height))
                            adjusted_canvas_height = adjusted_canvas_height + additional_bottom
                            
                            # 对于竖图（3:4），调整宽度以保持比例
                            # 横图不需要调整，使用原来的方式
                            if is_vertical_for_check and not keep_original_ratio:
                                ideal_width_for_height = int(adjusted_canvas_height * ratio_w / ratio_h)
                                if abs(ideal_width_for_height - adjusted_canvas_width) > 1:
                                    adjusted_canvas_width = ideal_width_for_height
                                    logger.info(f"  调整画布宽度以保持3:4比例: {final_canvas_width} -> {adjusted_canvas_width} (高度: {adjusted_canvas_height})")
                            
                            # 重新计算理想的粘贴位置，使上下边距完全均衡
                            ideal_paste_y = (adjusted_canvas_height - cropped_source.height) / 2
                            actual_paste_y = int(ideal_paste_y)
                            canvas_paste_y = actual_paste_y - top_extension
                            new_canvas = Image.new('RGB', (adjusted_canvas_width, adjusted_canvas_height), background_color)
                            new_canvas.paste(cropped_source, (canvas_paste_x, actual_paste_y))
                            logger.info(f"  扩展画布底部 {additional_bottom}px 并调整到理想位置以完全均衡上下边距 (迭代 {iteration + 1})")
                            
                            # 重新计算调整量（应该接近0，停止迭代）
                            paste_bottom = actual_paste_y + cropped_source.height
                            top_margin_actual = actual_paste_y
                            bottom_margin_actual = adjusted_canvas_height - paste_bottom
                            ideal_center_y = adjusted_canvas_height / 2
                            current_center_y = actual_paste_y + cropped_source.height / 2
                            ideal_offset = ideal_center_y - current_center_y
                            adjustment = int(ideal_offset)
                            if abs(adjustment) < 2:
                                break  # 已经均衡，停止迭代
                        elif adjustment > 0:
                            # 如果无法向下调整（上边距小、下边距大），扩展画布顶部
                            # 计算需要扩展多少，然后重新计算理想位置使上下边距完全均衡
                            # 当前下边距 = adjusted_canvas_height - (actual_paste_y + cropped_source.height)
                            # 需要扩展到：2 * (actual_paste_y + cropped_source.height) - 鞋子高度
                            ideal_total_height = 2 * (actual_paste_y + cropped_source.height) - cropped_source.height
                            additional_top = max(int(adjustment), int(ideal_total_height - adjusted_canvas_height))
                            top_extension = top_extension + additional_top
                            adjusted_canvas_height = adjusted_canvas_height + additional_top
                            
                            # 对于竖图（3:4），调整宽度以保持比例
                            # 横图不需要调整，使用原来的方式
                            if is_vertical_for_check and not keep_original_ratio:
                                ideal_width_for_height = int(adjusted_canvas_height * ratio_w / ratio_h)
                                if abs(ideal_width_for_height - adjusted_canvas_width) > 1:
                                    adjusted_canvas_width = ideal_width_for_height
                                    logger.info(f"  调整画布宽度以保持3:4比例: {final_canvas_width} -> {adjusted_canvas_width} (高度: {adjusted_canvas_height})")
                            
                            # 重新计算理想的粘贴位置，使上下边距完全均衡
                            ideal_paste_y = (adjusted_canvas_height - cropped_source.height) / 2
                            actual_paste_y = int(ideal_paste_y)
                            canvas_paste_y = actual_paste_y - top_extension
                            new_canvas = Image.new('RGB', (adjusted_canvas_width, adjusted_canvas_height), background_color)
                            new_canvas.paste(cropped_source, (canvas_paste_x, actual_paste_y))
                            logger.info(f"  扩展画布顶部 {additional_top}px 并调整到理想位置以完全均衡上下边距 (迭代 {iteration + 1})")
                            
                            # 重新计算调整量（应该接近0，停止迭代）
                            paste_bottom = actual_paste_y + cropped_source.height
                            top_margin_actual = actual_paste_y
                            bottom_margin_actual = adjusted_canvas_height - paste_bottom
                            ideal_center_y = adjusted_canvas_height / 2
                            current_center_y = actual_paste_y + cropped_source.height / 2
                            ideal_offset = ideal_center_y - current_center_y
                            adjustment = int(ideal_offset)
                            if abs(adjustment) < 2:
                                break  # 已经均衡，停止迭代
                    
                    # 最终验证（使用实际粘贴位置）
                    final_paste_top = actual_paste_y
                    final_paste_bottom = actual_paste_y + cropped_source.height
                    final_top_margin = final_paste_top
                    final_bottom_margin = adjusted_canvas_height - final_paste_bottom
                    final_margin_diff = abs(final_top_margin - final_bottom_margin)
                    logger.info(f"  最终边距: 上{final_top_margin:.0f}px ({final_top_margin/adjusted_canvas_height:.1%}), 下{final_bottom_margin:.0f}px ({final_bottom_margin/adjusted_canvas_height:.1%}), 差异{final_margin_diff:.0f}px ({final_margin_diff/adjusted_canvas_height:.1%})")
                    
                    # 更新最终画布尺寸（如果被扩展了）
                    if adjusted_canvas_height != final_canvas_height or adjusted_canvas_width != final_canvas_width:
                        final_canvas_height = adjusted_canvas_height
                        final_canvas_width = adjusted_canvas_width
                        logger.info(f"  最终画布尺寸: {final_canvas_width}x{final_canvas_height}")
            
            # 重新检测最终图片中的鞋子边界以验证结果
            try:
                # 使用专门的白色背景检测方法
                final_left, final_top, final_right, final_bottom = self.find_object_bounds_on_white_bg(new_canvas)
                
                # 使用调整后的画布尺寸计算实际边距比例
                actual_canvas_width = adjusted_canvas_width
                actual_canvas_height = adjusted_canvas_height
                actual_left_margin = final_left / actual_canvas_width
                actual_right_margin = (actual_canvas_width - final_right) / actual_canvas_width
                actual_top_margin = final_top / actual_canvas_height
                actual_bottom_margin = (actual_canvas_height - final_bottom) / actual_canvas_height
                
                # 检查垂直比例情况
                # 对于竖图，目标是上下边距各至少3%
                # 对于横图，目标是5.5:4.5的上下比例
                if is_vertical_for_check:
                    # 竖图：检查上下边距是否都至少是3%，并且是否均衡
                    target_vertical_margin = left_right_margin_ratio * 0.3  # 3%
                    top_margin_ok = actual_top_margin >= target_vertical_margin * 0.8  # 至少80%的要求
                    bottom_margin_ok = actual_bottom_margin >= target_vertical_margin * 0.8  # 至少80%的要求
                    
                    # 计算上下边距的均衡性（差异应该小于总边距的10%）
                    total_vertical_margin = actual_top_margin + actual_bottom_margin
                    margin_balance_diff = abs(actual_top_margin - actual_bottom_margin)
                    margin_balance_ratio = margin_balance_diff / total_vertical_margin if total_vertical_margin > 0 else 0
                    margin_balanced = margin_balance_ratio < 0.1  # 差异小于10%认为均衡
                    
                    # 计算垂直边距误差（相对于目标3%）
                    top_margin_error = max(0, target_vertical_margin - actual_top_margin)
                    bottom_margin_error = max(0, target_vertical_margin - actual_bottom_margin)
                    vertical_position_error = (top_margin_error + bottom_margin_error) / target_vertical_margin
                    
                    logger.info(f"  最终检测结果 (竖图模式):")
                    logger.info(f"    画布尺寸: {actual_canvas_width}x{actual_canvas_height}")
                    logger.info(f"    鞋子边界: 左{final_left}, 上{final_top}, 右{final_right}, 下{final_bottom}")
                    logger.info(f"    实际边距: 左{actual_left_margin:.1%}, 右{actual_right_margin:.1%}, 上{actual_top_margin:.1%}, 下{actual_bottom_margin:.1%}")
                    logger.info(f"    目标左右边距: {left_right_margin_ratio:.1%}")
                    logger.info(f"    目标上下边距: 各{target_vertical_margin:.1%} (至少，均衡)")
                    logger.info(f"    上下边距检查: 上{'✅' if top_margin_ok else '❌'} ({actual_top_margin:.1%}), 下{'✅' if bottom_margin_ok else '❌'} ({actual_bottom_margin:.1%})")
                    logger.info(f"    边距均衡性: {'✅' if margin_balanced else '❌'} (差异 {margin_balance_ratio:.1%})")
                    logger.info(f"    垂直边距误差: {vertical_position_error:.1%}")
                else:
                    # 横图：检查5.5:4.5的上下比例
                    target_top_ratio = 5.5 / (5.5 + 4.5)  # = 0.55 = 55%
                    target_bottom_ratio = 4.5 / (5.5 + 4.5)  # = 0.45 = 45%
                    
                    # 计算理想的上下边距比例
                    vertical_position_error = abs(actual_top_margin / (actual_top_margin + actual_bottom_margin) - target_top_ratio)
                    
                    logger.info(f"  最终检测结果:")
                    logger.info(f"    画布尺寸: {actual_canvas_width}x{actual_canvas_height}")
                    logger.info(f"    鞋子边界: 左{final_left}, 上{final_top}, 右{final_right}, 下{final_bottom}")
                    logger.info(f"    实际边距: 左{actual_left_margin:.1%}, 右{actual_right_margin:.1%}, 上{actual_top_margin:.1%}, 下{actual_bottom_margin:.1%}")
                    logger.info(f"    目标左右边距: {left_right_margin_ratio:.1%}")
                    logger.info(f"    目标上下比例: {target_top_ratio:.1%}:{target_bottom_ratio:.1%}")
                    logger.info(f"    实际上下比例: {actual_top_margin/(actual_top_margin + actual_bottom_margin):.1%}:{actual_bottom_margin/(actual_top_margin + actual_bottom_margin):.1%}")
                    logger.info(f"    垂直比例误差: {vertical_position_error:.1%}")
                
                # 检查边距是否符合要求
                left_diff = abs(actual_left_margin - left_right_margin_ratio)
                right_diff = abs(actual_right_margin - left_right_margin_ratio)
                margin_error = max(left_diff, right_diff)
                
                # 检查左右是否均衡
                left_right_balance_error = abs(actual_left_margin - actual_right_margin)
                
                # 对于竖图，检查上下边距是否都至少是3%，并且是否均衡
                if is_vertical_for_check:
                    target_vertical_margin = left_right_margin_ratio * 0.3  # 3%
                    top_margin_diff = max(0, target_vertical_margin - actual_top_margin)
                    bottom_margin_diff = max(0, target_vertical_margin - actual_bottom_margin)
                    vertical_margin_error = (top_margin_diff + bottom_margin_diff) / target_vertical_margin
                    
                    # 计算上下边距的均衡性
                    total_vertical_margin = actual_top_margin + actual_bottom_margin
                    margin_balance_diff = abs(actual_top_margin - actual_bottom_margin)
                    margin_balance_ratio = margin_balance_diff / total_vertical_margin if total_vertical_margin > 0 else 0
                else:
                    vertical_margin_error = vertical_position_error
                    margin_balance_ratio = 0
                
                # 保存最佳结果（考虑边距均衡性）
                balance_penalty = margin_balance_ratio * 0.5 if is_vertical_for_check else 0  # 竖图边距不均衡的惩罚
                total_error = margin_error + left_right_balance_error + vertical_margin_error * 2 + balance_penalty
                if total_error < best_margin_error:
                    best_margin_error = total_error
                    best_result = new_canvas.copy()
                
                # 检查是否满足所有要求
                margin_ok = left_diff < 0.02 and right_diff < 0.02  # 边距误差小于2%
                balance_ok = left_right_balance_error < 0.02  # 左右均衡误差小于2%
                
                if is_vertical_for_check:
                    # 竖图：检查上下边距是否都至少是3%（允许20%的误差），并且是否均衡（差异小于10%）
                    margin_amount_ok = top_margin_diff < target_vertical_margin * 0.2 and bottom_margin_diff < target_vertical_margin * 0.2
                    margin_balance_ok = margin_balance_ratio < 0.1  # 差异小于10%认为均衡
                    vertical_ok = margin_amount_ok and margin_balance_ok
                else:
                    # 横图：检查5.5:4.5比例
                    vertical_ok = vertical_position_error < 0.03  # 垂直比例误差小于3%
                
                if margin_ok and balance_ok and vertical_ok:
                    logger.info("✅ 边距、均衡和垂直比例都符合要求！")
                    return new_canvas
                else:
                    issues = []
                    if not margin_ok:
                        issues.append(f"边距偏差(左{left_diff:.1%}, 右{right_diff:.1%})")
                    if not balance_ok:
                        issues.append(f"左右不均衡({left_right_balance_error:.1%})")
                    if not vertical_ok:
                        if is_vertical_for_check:
                            if not margin_amount_ok:
                                issues.append(f"上下边距不足(上{actual_top_margin:.1%}, 下{actual_bottom_margin:.1%}, 目标各{target_vertical_margin:.1%})")
                            if not margin_balance_ok:
                                issues.append(f"上下边距不均衡(差异{margin_balance_ratio:.1%})")
                        else:
                            issues.append(f"垂直比例偏差({vertical_position_error:.1%})")
                    
                    logger.warning(f"⚠️ {', '.join(issues)}")
                    
                    # 如果不是最后一次迭代，尝试调整
                    if iteration < max_iterations - 1:
                        logger.info("  基于检测结果重新计算理想定位...")
                        
                        # 基于实际检测到的鞋子边界，重新计算理想的画布尺寸和定位
                        detected_object_width = final_right - final_left
                        detected_object_height = final_bottom - final_top
                        
                        # 检验检测结果的合理性
                        if (detected_object_width > object_width * 0.7 and 
                            detected_object_width < object_width * 1.5):
                            
                            # 基于检测到的鞋子尺寸重新计算理想画布
                            # 方法1：基于宽度计算
                            new_ideal_width_by_width = detected_object_width / (1 - 2 * left_right_margin_ratio)
                            if keep_original_ratio:
                                # 使用检测到的对象宽高比
                                detected_aspect_ratio = detected_object_height / detected_object_width if detected_object_width > 0 else object_aspect_ratio
                                new_ideal_height_by_width = new_ideal_width_by_width * detected_aspect_ratio
                            else:
                                new_ideal_height_by_width = new_ideal_width_by_width * ratio_h / ratio_w
                            
                            # 方法2：基于高度计算（确保不裁剪）
                            # 对于竖图，使用更小的上下边距
                            detected_aspect_ratio = detected_object_height / detected_object_width if detected_object_width > 0 else aspect_ratio
                            is_vertical_detected = detected_aspect_ratio >= 1.0
                            
                            if is_vertical_detected:
                                # 竖图：上下边距使用更小的比例（3%），确保完整的3%边距
                                vertical_margin_for_detected = left_right_margin_ratio * 0.3
                                # 确保至少有完整的3%上下边距
                                min_required_height_for_detected = detected_object_height / (1 - 2 * vertical_margin_for_detected)
                                logger.info(f"  竖图重新计算: 要求完整3%上下边距，最小高度={min_required_height_for_detected:.0f}px")
                            else:
                                # 横图：统一使用左右边距比例
                                vertical_margin_for_detected = left_right_margin_ratio
                                margin_requirement_factor_detected = 0.8
                                min_required_height_for_detected = detected_object_height * (1 + 2 * vertical_margin_for_detected * margin_requirement_factor_detected)
                            
                            new_ideal_height_by_height = detected_object_height / (1 - 2 * vertical_margin_for_detected)
                            if keep_original_ratio:
                                new_ideal_width_by_height = new_ideal_height_by_height / detected_aspect_ratio
                            else:
                                new_ideal_width_by_height = new_ideal_height_by_height * ratio_w / ratio_h
                            
                            # 选择能完整容纳鞋子的方案
                            if new_ideal_height_by_width >= min_required_height_for_detected:
                                new_ideal_width = new_ideal_width_by_width
                                new_ideal_height = new_ideal_height_by_width
                            else:
                                new_ideal_width = new_ideal_width_by_height
                                new_ideal_height = new_ideal_height_by_height
                                logger.info(f"    基于高度重新计算（防止裁剪）: {new_ideal_width:.0f}x{new_ideal_height:.0f}")
                            
                            # 限制画布尺寸变化幅度，避免过度调整
                            width_change = new_ideal_width - final_canvas_width
                            if abs(width_change) < final_canvas_width * 0.2:  # 限制在20%以内
                                # 确保调整后的高度仍能容纳鞋子
                                if new_ideal_height >= min_required_height_for_detected:
                                    final_canvas_width = int(new_ideal_width)
                                    final_canvas_height = int(new_ideal_height)
                                    logger.info(f"    调整画布尺寸: {final_canvas_width}x{final_canvas_height}")
                                else:
                                    logger.warning(f"    调整后的高度 {new_ideal_height:.0f}px 不足以容纳鞋子，保持当前尺寸")
                            
                            # 重新计算鞋子的理想中心位置
                            # 基于检测到的鞋子中心，而不是原始的left/right
                            detected_center_x = (final_left + final_right) / 2
                            detected_center_y = (final_top + final_bottom) / 2
                            
                            # 计算鞋子在原图中的对应中心（反向推算）
                            # 当前detected_center在画布中，需要映射回原图坐标
                            # 注意：如果paste_y < 0，画布顶部被扩展了top_extension = -paste_y像素
                            # 检测到的detected_center_y是在扩展后的画布中的位置（相对于扩展后的画布顶部）
                            
                            # 计算画布顶部扩展的高度
                            # 只有竖图才会扩展画布顶部，横图不扩展
                            if is_vertical_for_check:
                                current_top_extension = max(0, -paste_y) if paste_y < 0 else 0
                            else:
                                current_top_extension = 0  # 横图不扩展画布
                            
                            # 计算在扩展后的画布上的实际粘贴位置
                            # 如果paste_y < 0：
                            #   - 竖图：canvas_paste_y = 0, actual_paste_y = top_extension
                            #   - 横图：canvas_paste_y = 0, actual_paste_y = 0
                            # 如果paste_y >= 0：canvas_paste_y = paste_y, actual_paste_y = paste_y
                            actual_paste_y_in_canvas = current_top_extension + max(0, paste_y)
                            
                            # 反推原图中的鞋子中心
                            # detected_center是在画布中的位置
                            # 对于竖图：如果画布顶部被扩展了，检测到的坐标需要减去扩展高度
                            # 对于横图：画布没有扩展，直接使用检测到的坐标
                            original_center_x = detected_center_x - max(0, paste_x) + max(0, -paste_x)
                            
                            # 对于Y坐标：
                            # 检测到的位置减去实际粘贴位置，再加上原图中被裁剪的部分
                            # 如果paste_y < 0，原图顶部被裁剪了-paste_y像素，所以需要加上这部分
                            original_center_y = detected_center_y - actual_paste_y_in_canvas + max(0, -paste_y)
                            
                            # 确保坐标在原图范围内（防止超出边界）
                            original_center_x = max(object_width / 2, min(source_width - object_width / 2, original_center_x))
                            original_center_y = max(object_height / 2, min(source_height - object_height / 2, original_center_y))
                            
                            # 如果垂直比例误差太大，特别调整垂直位置
                            if not vertical_ok:
                                if is_vertical_for_check:
                                    # 竖图：均衡调整上下边距，确保都是3%
                                    target_vertical_margin = left_right_margin_ratio * 0.3  # 3%
                                    
                                    # 计算当前上下边距的差异
                                    top_margin_actual_px = actual_top_margin * final_canvas_height
                                    bottom_margin_actual_px = actual_bottom_margin * final_canvas_height
                                    target_margin_px = target_vertical_margin * final_canvas_height
                                    
                                    # 计算需要调整的量，使上下边距均衡
                                    margin_diff = top_margin_actual_px - bottom_margin_actual_px
                                    
                                    # 如果上下边距差异较大，调整位置使它们更均衡
                                    if abs(margin_diff) > final_canvas_height * 0.01:  # 差异超过1%
                                        # 计算理想的中心位置（使上下边距均衡）
                                        ideal_center_y = final_canvas_height / 2
                                        current_center_y = original_center_y
                                        
                                        # 计算需要移动的距离（向理想中心移动50%的距离）
                                        correction_offset = (ideal_center_y - current_center_y) * 0.5
                                        original_center_y += correction_offset
                                        
                                        logger.info(f"    竖图边距均衡调整 (第{iteration+1}次): 移动 {correction_offset:.0f} 像素")
                                        logger.info(f"      调整前: 上{top_margin_actual_px:.0f}px ({actual_top_margin:.1%}), 下{bottom_margin_actual_px:.0f}px ({actual_bottom_margin:.1%}), 差异{margin_diff:.0f}px")
                                    elif actual_bottom_margin < target_vertical_margin * 0.8:
                                        # 如果差异不大但底部边距不足，向上移动
                                        bottom_margin_deficit = target_margin_px - bottom_margin_actual_px
                                        correction_offset = -bottom_margin_deficit * 0.5
                                        original_center_y += correction_offset
                                        logger.info(f"    竖图底部边距修正 (第{iteration+1}次): 向上移动 {abs(correction_offset):.0f} 像素")
                                    elif actual_top_margin < target_vertical_margin * 0.8:
                                        # 如果差异不大但顶部边距不足，向下移动
                                        top_margin_deficit = target_margin_px - top_margin_actual_px
                                        correction_offset = top_margin_deficit * 0.5
                                        original_center_y += correction_offset
                                        logger.info(f"    竖图顶部边距修正 (第{iteration+1}次): 向下移动 {correction_offset:.0f} 像素")
                                else:
                                    # 横图：使用5.5:4.5比例调整
                                    current_top_ratio = actual_top_margin / (actual_top_margin + actual_bottom_margin)
                                    target_top_ratio = 5.5 / (5.5 + 4.5)  # = 0.55 = 55%
                                    ratio_offset = target_top_ratio - current_top_ratio
                                    
                                    # 使用保守的修正策略，避免过度修正
                                    if iteration == 0:
                                        # 第一次修正：修正50%的偏差
                                        correction_factor = 0.5
                                    else:
                                        # 后续修正：更保守，修正30%的偏差
                                        correction_factor = 0.3
                                    
                                    # 计算需要向下移动的像素（正值向下，负值向上）
                                    correction_offset = ratio_offset * final_canvas_height * correction_factor
                                    original_center_y += correction_offset
                                    logger.info(f"    垂直比例修正 (第{iteration+1}次): 偏移 {correction_offset:.0f} 像素 (比例偏差: {ratio_offset:.1%}, 修正率: {correction_factor:.0%})")
                            
                            # 基于原图中心更新left, right, top, bottom（保持尺寸不变）
                            half_width = object_width / 2
                            half_height = object_height / 2
                            left = original_center_x - half_width
                            right = original_center_x + half_width
                            top = original_center_y - half_height
                            bottom = original_center_y + half_height
                            
                            logger.info(f"    更新原图鞋子坐标: 中心({original_center_x:.0f}, {original_center_y:.0f})")
                            logger.info(f"    新边界: 左{left:.0f}, 上{top:.0f}, 右{right:.0f}, 下{bottom:.0f}")
                        else:
                            logger.warning(f"检测结果异常，跳过调整 (检测宽度: {detected_object_width}, 原始宽度: {object_width})")
                            break
            except Exception as e:
                logger.warning(f"重新检测失败: {e}, 使用当前结果")
                break
        
        # 返回最佳结果
        if best_result is not None:
            logger.info(f"返回最佳结果，总误差: {best_margin_error:.1%}")
            return best_result
        else:
            logger.warning("未能生成有效结果，返回最后一次尝试的结果")
            return new_canvas
    
    def smart_crop(self, image: Image.Image, target_ratio: str = 'auto', min_resolution: int = 800, 
                   preserve_resolution: bool = False, use_margin_mode: bool = True, fast_mode: bool = True,
                   margin_ratio: float = 10.0) -> Image.Image:
        """
        智能裁剪图片，确保主体居中显示并保持高分辨率
        
        Args:
            image: PIL Image对象
            target_ratio: 目标比例 '4:3', '3:4', 'auto'
            min_resolution: 最小分辨率（短边）
            preserve_resolution: 是否优先保持分辨率（适合高分辨率图片）
            use_margin_mode: 是否使用新的边距模式（推荐）
            fast_mode: 是否使用快速模式（默认True，大幅提升性能）
            
        Returns:
            裁剪后的PIL Image对象
        """
        # 优先使用新的边距模式
        if use_margin_mode:
            # 将百分比转换为小数（例如10% -> 0.1）
            margin_ratio_decimal = margin_ratio / 100.0
            return self.smart_crop_with_margins(image, left_right_margin_ratio=margin_ratio_decimal, 
                                              target_ratio=target_ratio, min_resolution=min_resolution, fast_mode=fast_mode)
        
        # 获取原图尺寸
        original_width, original_height = image.size
        
        # 找到主体边界
        left, top, right, bottom = self.find_object_bounds(image)
        object_width = right - left
        object_height = bottom - top
        
        # 确定目标比例（新的智能选择逻辑）
        # 高宽比 = object_height / object_width
        aspect_ratio = object_height / object_width if object_width > 0 else 1.0
        keep_original_ratio = False  # 是否保持原比例
        
        if target_ratio == 'auto':
            if aspect_ratio < 0.75:
                # 高宽比 < 0.75：很宽的图，使用 4:3 横图比例
                target_ratio = '4:3'
                logger.info(f"检测到宽图（高宽比 {aspect_ratio:.2f} < 0.75），使用 4:3 横图比例")
            elif aspect_ratio >= 0.75 and aspect_ratio < 1.0:
                # 0.75 <= 高宽比 < 1：接近方形，保持原比例加边距
                keep_original_ratio = True
                logger.info(f"检测到接近方形图（高宽比 {aspect_ratio:.2f} 在 0.75-1.0 之间），保持原比例加边距")
            else:
                # 高宽比 >= 1：很高的图，使用 3:4 竖图比例
                target_ratio = '3:4'
                logger.info(f"检测到高图（高宽比 {aspect_ratio:.2f} >= 1.0），使用 3:4 竖图比例")
        else:
            # 用户指定了比例，使用指定比例
            logger.info(f"使用用户指定的比例: {target_ratio}")
        
        # 解析目标比例
        if keep_original_ratio:
            # 保持原比例模式：直接计算目标尺寸，保持对象的宽高比
            object_aspect_ratio = object_height / object_width if object_width > 0 else 1.0
            logger.info(f"保持原比例模式: 宽高比 {object_aspect_ratio:.2f} (约 {object_width/object_height:.2f}:1)")
            
            # 高分辨率模式：优先保持更多像素
            if preserve_resolution or min(original_width, original_height) > 2000:
                # 对于高分辨率图片，使用更保守的裁剪策略
                # 确保对象能完全显示，留5%边距
                needed_width = object_width * 1.05
                needed_height = object_height * 1.05
                
                # 从原图的最大尺寸开始，保持对象的宽高比
                max_width = original_width
                max_height = original_height
                
                # 计算在原图范围内能容纳的最大尺寸（保持宽高比）
                if max_width / max_height > object_width / object_height:
                    # 宽度是限制因素
                    target_width = max_width
                    target_height = target_width * object_aspect_ratio
                else:
                    # 高度是限制因素
                    target_height = max_height
                    target_width = target_height / object_aspect_ratio
                
                # 确保对象能完全显示
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
                
                # 计算保持高分辨率的目标尺寸（保持原宽高比）
                target_width = object_width * margin_factor
                target_height = object_height * margin_factor
                
                # 确保目标尺寸满足最小分辨率要求
                original_min_size = min(original_width, original_height)
                adaptive_min_resolution = min(min_resolution, int(original_min_size * 0.8))
                
                # 对于保持原比例的情况，确保短边满足最小分辨率
                if target_width < target_height:
                    # 宽度是短边
                    if target_width < adaptive_min_resolution:
                        scale = adaptive_min_resolution / target_width
                        target_width = adaptive_min_resolution
                        target_height = target_height * scale
                else:
                    # 高度是短边
                    if target_height < adaptive_min_resolution:
                        scale = adaptive_min_resolution / target_height
                        target_height = adaptive_min_resolution
                        target_width = target_width * scale
        else:
            # 固定比例模式
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
                # 使用与边距模式相同的自适应最小分辨率逻辑
                original_min_size = min(original_width, original_height)
                adaptive_min_resolution = min(min_resolution, int(original_min_size * 0.8))
                
                min_width = adaptive_min_resolution if ratio_w >= ratio_h else adaptive_min_resolution * ratio_w / ratio_h
                min_height = adaptive_min_resolution if ratio_h >= ratio_w else adaptive_min_resolution * ratio_h / ratio_w
                
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
                           high_quality: bool = True, preserve_resolution: bool = False, 
                           use_margin_mode: bool = True, fast_mode: bool = True, margin_ratio: float = 10.0) -> bool:
        """
        处理单张图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            target_ratio: 目标比例
            high_quality: 是否使用高质量保存
            preserve_resolution: 是否优先保持分辨率（适合高分辨率图片）
            use_margin_mode: 是否使用边距模式（确保10%左右边距）
            fast_mode: 是否使用快速模式（默认True，大幅提升性能）
            
        Returns:
            是否处理成功
        """
        try:
            logger.info(f"开始处理: {input_path} (快速模式: {'是' if fast_mode else '否'})")
            
            # 获取原文件大小
            original_file_size = os.path.getsize(input_path)
            
            # 读取图片
            with Image.open(input_path) as image:
                # 获取原始图片信息
                original_format = image.format
                original_mode = image.mode
                
                # 智能裁剪 - 传递快速模式参数和边距比例
                final_image = self.smart_crop(image, target_ratio, preserve_resolution=preserve_resolution, 
                                             use_margin_mode=use_margin_mode, fast_mode=fast_mode, margin_ratio=margin_ratio)
                
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
                     preserve_resolution: bool = False, use_margin_mode: bool = True,
                     fast_mode: bool = True, margin_ratio: float = 10.0) -> dict:
        """
        批量处理图片
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            target_ratio: 目标比例
            supported_formats: 支持的图片格式
            high_quality: 是否使用高质量保存
            preserve_resolution: 是否优先保持分辨率
            use_margin_mode: 是否使用边距模式（确保10%左右边距）
            fast_mode: 是否使用快速模式（默认True，大幅提升性能）
            
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
        
        logger.info(f"找到 {total_files} 张图片待处理 (快速模式: {'是' if fast_mode else '否'})")
        
        for i, image_file in enumerate(image_files, 1):
            logger.info(f"处理进度: {i}/{total_files}")
            
            # 构建输出文件路径 - 保持与源文件名一致
            # 注意：如果process_single_image中发生格式转换，文件扩展名可能会改变
            output_file = output_path / image_file.name  # 使用原文件名
            
            # 处理图片 - 传递快速模式参数和边距比例
            if self.process_single_image(str(image_file), str(output_file), target_ratio, 
                                       high_quality, preserve_resolution, use_margin_mode, fast_mode, margin_ratio):
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
    
    def detect_background_color(self, image: Image.Image, fast_mode: bool = True) -> tuple:
        """
        智能检测图片的背景颜色（优化性能版本）
        
        Args:
            image: PIL Image对象
            fast_mode: 是否使用快速模式（默认True，大幅提升性能）
            
        Returns:
            (R, G, B) 背景颜色元组
        """
        # 转换为numpy数组
        img_array = np.array(image)
        
        if len(img_array.shape) == 2:
            # 灰度图，转换为RGB
            img_array = np.stack([img_array] * 3, axis=-1)
        elif img_array.shape[2] == 4:
            # RGBA图，只取RGB通道
            img_array = img_array[:, :, :3]
        
        height, width = img_array.shape[:2]
        
        # 策略1: 分析图片边缘区域的颜色
        edge_thickness = min(50, min(width, height) // 15)  # 边缘采样厚度
        
        # 收集边缘像素
        edge_pixels = []
        
        # 上边缘
        edge_pixels.extend(img_array[:edge_thickness, :].reshape(-1, 3))
        # 下边缘
        edge_pixels.extend(img_array[-edge_thickness:, :].reshape(-1, 3))
        # 左边缘
        edge_pixels.extend(img_array[:, :edge_thickness].reshape(-1, 3))
        # 右边缘
        edge_pixels.extend(img_array[:, -edge_thickness:].reshape(-1, 3))
        
        edge_pixels = np.array(edge_pixels)
        
        # 快速模式：大幅减少像素采样和聚类计算
        if fast_mode:
            # 对于大图片，随机采样减少计算量
            if len(edge_pixels) > 5000:  # 如果边缘像素超过5000个
                indices = np.random.choice(len(edge_pixels), 5000, replace=False)
                edge_pixels = edge_pixels[indices]
            
            # 使用简化的聚类或直接使用中位数
            try:
                # 先尝试直接使用中位数（最快）
                bg_color = np.median(edge_pixels, axis=0)
                
                # 检查是否是明显的单一颜色（方差很小）
                color_variance = np.var(edge_pixels, axis=0).mean()
                if color_variance < 100:  # 颜色比较统一
                    logger.info(f"快速模式-中位数检测到背景颜色: RGB{tuple(bg_color.astype(int))}")
                    return tuple(bg_color.astype(int))
                
                # 如果颜色变化较大，使用简化的聚类
                from sklearn.cluster import KMeans
                kmeans = KMeans(n_clusters=2, random_state=42, n_init=3)  # 减少聚类数和初始化次数
                kmeans.fit(edge_pixels)
                
                # 找到最大的聚类
                labels = kmeans.labels_
                unique_labels, label_counts = np.unique(labels, return_counts=True)
                largest_cluster_idx = unique_labels[np.argmax(label_counts)]
                bg_color = kmeans.cluster_centers_[largest_cluster_idx]
                
                logger.info(f"快速模式-简化聚类检测到背景颜色: RGB{tuple(bg_color.astype(int))}")
                
            except ImportError:
                logger.warning("sklearn未安装，使用中位数方法")
                bg_color = np.median(edge_pixels, axis=0)
                logger.info(f"快速模式-中位数检测到背景颜色: RGB{tuple(bg_color.astype(int))}")
                
            except Exception as e:
                logger.warning(f"快速聚类检测失败: {e}，使用中位数")
                bg_color = np.median(edge_pixels, axis=0)
                logger.info(f"快速模式-中位数检测到背景颜色: RGB{tuple(bg_color.astype(int))}")
        
        else:
            # 原始精确模式（保留兼容性）
            # 策略2: 使用聚类找到主要的背景颜色
            try:
                # 对边缘像素进行颜色聚类
                from sklearn.cluster import KMeans
                
                # 使用K-means聚类找到3个主要颜色
                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                kmeans.fit(edge_pixels)
                
                # 找到最大的聚类（最可能是背景）
                labels = kmeans.labels_
                unique_labels, label_counts = np.unique(labels, return_counts=True)
                
                # 获取最大聚类的中心颜色
                largest_cluster_idx = unique_labels[np.argmax(label_counts)]
                bg_color = kmeans.cluster_centers_[largest_cluster_idx]
                
                logger.info(f"使用聚类检测到背景颜色: RGB{tuple(bg_color.astype(int))}")
                
            except ImportError:
                logger.warning("sklearn未安装，使用简化的背景颜色检测")
                # 简化方法：使用边缘像素的中位数
                bg_color = np.median(edge_pixels, axis=0)
                logger.info(f"使用中位数检测到背景颜色: RGB{tuple(bg_color.astype(int))}")
            
            except Exception as e:
                logger.warning(f"聚类背景检测失败: {e}，使用备选方法")
                # 备选方法：分析四个角落的颜色
                corner_pixels = []
                corner_size = min(20, min(width, height) // 10)
                
                # 四个角落
                corner_pixels.extend(img_array[:corner_size, :corner_size].reshape(-1, 3))  # 左上
                corner_pixels.extend(img_array[:corner_size, -corner_size:].reshape(-1, 3))  # 右上
                corner_pixels.extend(img_array[-corner_size:, :corner_size].reshape(-1, 3))  # 左下
                corner_pixels.extend(img_array[-corner_size:, -corner_size:].reshape(-1, 3))  # 右下
                
                corner_pixels = np.array(corner_pixels)
                bg_color = np.median(corner_pixels, axis=0)
                logger.info(f"使用角落检测到背景颜色: RGB{tuple(bg_color.astype(int))}")
        
        # 确保颜色值在有效范围内
        bg_color = np.clip(bg_color, 0, 255).astype(int)
        
        # 检查是否为接近白色的颜色
        if np.all(bg_color > 240):
            logger.info("检测到接近白色的背景")
        elif np.all(bg_color < 15):
            logger.info("检测到接近黑色的背景")
        else:
            logger.info(f"检测到彩色背景: RGB{tuple(bg_color)}")
        
        return tuple(bg_color)
    
    def find_object_contour_bounds(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        寻找图片中主体对象的实际轮廓边界（非矩形边界框）
        返回轮廓上最左、最右、最上、最下的像素点坐标
        
        Args:
            image: PIL Image对象
            
        Returns:
            (left, top, right, bottom) 轮廓边界坐标
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
        
        # 策略1: 基于亮度差异检测（适合商品图片）
        try:
            # 计算图片边缘的平均亮度（通常是背景色）
            edge_samples = []
            edge_thickness = min(50, min(width, height) // 20)
            
            # 采样四条边
            edge_samples.extend(gray[:edge_thickness, :].flatten())
            edge_samples.extend(gray[-edge_thickness:, :].flatten())
            edge_samples.extend(gray[:, :edge_thickness].flatten())
            edge_samples.extend(gray[:, -edge_thickness:].flatten())
            
            bg_brightness = np.median(edge_samples)
            logger.info(f"检测到背景亮度: {bg_brightness:.1f}")
            
            # 根据背景亮度动态调整阈值
            if bg_brightness > 200:  # 白色背景
                threshold_offset = 25
                _, binary = cv2.threshold(gray, bg_brightness - threshold_offset, 255, cv2.THRESH_BINARY_INV)
            else:  # 暗色背景
                threshold_offset = 25
                _, binary = cv2.threshold(gray, bg_brightness + threshold_offset, 255, cv2.THRESH_BINARY)
            
            # 形态学处理
            kernel = np.ones((5, 5), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # 去除边缘噪声
            border_size = max(3, min(width, height) // 150)
            binary[:border_size, :] = 0
            binary[-border_size:, :] = 0
            binary[:, :border_size] = 0
            binary[:, -border_size:] = 0
            
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > height * width * 0.05:  # 面积至少占图片的5%
                        if area > best_area:
                            best_area = area
                            best_contour = contour
                            
        except Exception as e:
            logger.warning(f"轮廓检测策略失败: {e}")
        
        if best_contour is not None:
            # 尝试过滤阴影部分
            # 需要先获取bg_brightness，如果try块失败则使用默认值
            try:
                edge_samples = []
                edge_thickness = min(50, min(width, height) // 20)
                edge_samples.extend(gray[:edge_thickness, :].flatten())
                edge_samples.extend(gray[-edge_thickness:, :].flatten())
                edge_samples.extend(gray[:, :edge_thickness].flatten())
                edge_samples.extend(gray[:, -edge_thickness:].flatten())
                bg_brightness = np.median(edge_samples)
            except:
                bg_brightness = 255  # 默认白色背景
            
            best_contour = self._filter_shadow_from_contour(best_contour, gray, bg_brightness)
            
            # 从轮廓中找到极值点
            contour_points = best_contour.reshape(-1, 2)
            
            left = np.min(contour_points[:, 0])    # 最左边的x坐标
            right = np.max(contour_points[:, 0])   # 最右边的x坐标
            top = np.min(contour_points[:, 1])     # 最上边的y坐标
            bottom = np.max(contour_points[:, 1])  # 最下边的y坐标
            
            # 验证检测结果的合理性
            contour_width = right - left
            contour_height = bottom - top
            contour_area = cv2.contourArea(best_contour)
            image_area = width * height
            
            area_ratio = contour_area / image_area
            logger.info(f"检测到轮廓边界（已过滤阴影）: 左{left}, 上{top}, 右{right}, 下{bottom}")
            logger.info(f"轮廓尺寸: {contour_width}x{contour_height}, 轮廓面积占比: {area_ratio:.1%}")
            
            # 如果检测结果合理，返回轮廓边界
            if 0.05 <= area_ratio <= 0.9:
                return left, top, right, bottom
            else:
                logger.warning(f"检测到的轮廓面积占比异常: {area_ratio:.1%}, 使用保守策略")
        
        # 如果轮廓检测失败，回退到矩形边界框检测
        logger.warning("轮廓检测失败，使用矩形边界框作为替代")
        return self.find_object_bounds(image)


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
    parser.add_argument('--margin-mode', action='store_true', default=True,
                       help='使用边距模式，确保鞋子左右边距各占10% (默认启用)')
    parser.add_argument('--no-margin-mode', action='store_true',
                       help='禁用边距模式，使用传统裁剪方式')
    
    args = parser.parse_args()
    
    try:
        # 创建处理器
        processor = ShoeImageProcessor()
        
        # 设置质量参数
        high_quality = args.quality == 'high'
        preserve_resolution = args.hires
        use_margin_mode = args.margin_mode and not args.no_margin_mode
        
        logger.info(f"处理参数: 比例={args.ratio}, 高质量={'是' if high_quality else '否'}, "
                   f"高分辨率={'是' if preserve_resolution else '否'}, "
                   f"边距模式={'是' if use_margin_mode else '否'}")
        
        if args.single or os.path.isfile(args.input):
            # 单张图片处理
            success = processor.process_single_image(
                args.input, args.output, args.ratio, high_quality, preserve_resolution, use_margin_mode)
            if success:
                print("✅ 图片处理成功!")
            else:
                print("❌ 图片处理失败!")
                sys.exit(1)
        else:
            # 批量处理
            stats = processor.process_batch(args.input, args.output, args.ratio, None, 
                                          high_quality, preserve_resolution, use_margin_mode)
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