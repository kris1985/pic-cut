#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阴影检测模块
提供多种阴影检测算法，用于从图像轮廓中过滤阴影区域
"""

import logging
from typing import Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ShadowDetector:
    """阴影检测器，整合多种科学方案"""
    
    def __init__(self):
        """初始化阴影检测器"""
        pass
    
    def detect_shadow_by_hsv_channels(self, bgr_image: np.ndarray, contour: np.ndarray, bg_brightness: float) -> np.ndarray:
        """
        方案1: 基于HSV通道的差异检测
        阴影区域的V通道明显低于背景，S通道可能略高于背景
        
        Args:
            bgr_image: BGR格式图像
            contour: 轮廓
            bg_brightness: 背景亮度值
            
        Returns:
            阴影mask（True=阴影，False=非阴影）
        """
        try:
            # 转换为HSV空间
            hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
            _, s, v = cv2.split(hsv)
            
            # 创建轮廓mask
            mask = np.zeros(v.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            
            # 获取轮廓内的像素
            contour_v = v[mask > 0]
            contour_s = s[mask > 0]
            
            if len(contour_v) == 0:
                return np.zeros_like(mask, dtype=bool)
            
            # 计算背景的V和S值（假设背景是白色，V高S低）
            # 注意：这些值用于理解背景特征，但实际检测使用主体分位数
            
            # 计算主体区域的典型V和S值
            p10_v = np.percentile(contour_v, 10)
            p50_v = np.percentile(contour_v, 50)
            p50_s = np.percentile(contour_s, 50)
            
            # 阴影检测条件：
            # 1. V通道明显低于主体（V < T1）
            # 2. S通道可能略高于背景（S > T2），因为阴影区域可能有漫反射
            v_threshold = min(p10_v + 20, p50_v - 30)  # V通道阈值
            s_threshold = max(5, p50_s * 0.3)  # S通道阈值（避免噪声）
            
            # 创建阴影mask
            shadow_mask = (
                (v < v_threshold) &  # V通道低于阈值
                (s > s_threshold) &  # S通道高于阈值（排除纯黑）
                (mask > 0)  # 在轮廓内
            )
            
            logger.info(f"HSV通道检测: V阈值={v_threshold:.1f}, S阈值={s_threshold:.1f}, 检测到{np.sum(shadow_mask)}个阴影像素")
            return shadow_mask
            
        except Exception as e:
            logger.warning(f"HSV通道检测失败: {e}")
            return np.zeros((bgr_image.shape[0], bgr_image.shape[1]), dtype=bool)
    
    def detect_shadow_by_background_subtraction(self, bgr_image: np.ndarray, contour: np.ndarray, bg_brightness: float) -> np.ndarray:
        """
        方案3: 基于背景估计的差分法
        通过生成虚拟纯白背景，计算差异，使用自适应阈值
        改进：只在轮廓边缘区域检测阴影，避免误判鞋子主体
        
        Args:
            bgr_image: BGR格式图像
            contour: 轮廓
            bg_brightness: 背景亮度值
            
        Returns:
            阴影mask（True=阴影，False=非阴影）
        """
        try:
            height, width = bgr_image.shape[:2]
            
            # 创建轮廓mask
            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            
            # 获取轮廓边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 只在轮廓边缘区域检测阴影（边缘30%的区域）
            # 这样可以避免误判鞋子主体
            edge_margin = min(w, h) * 0.3
            edge_left = x
            edge_right = x + w
            edge_top = y
            edge_bottom = y + h
            
            # 创建边缘区域mask
            y_coords, x_coords = np.ogrid[:height, :width]
            is_in_left_edge = (x_coords >= edge_left) & (x_coords <= edge_left + edge_margin)
            is_in_right_edge = (x_coords >= edge_right - edge_margin) & (x_coords <= edge_right)
            is_in_top_edge = (y_coords >= edge_top) & (y_coords <= edge_top + edge_margin)
            is_in_bottom_edge = (y_coords >= edge_bottom - edge_margin) & (y_coords <= edge_bottom)
            
            edge_mask = ((is_in_left_edge | is_in_right_edge | is_in_top_edge | is_in_bottom_edge) & 
                        (mask > 0)).astype(np.uint8) * 255
            
            # 如果背景是白色，创建纯白背景
            if bg_brightness > 200:
                # 创建纯白背景（BGR格式）
                white_bg = np.ones((height, width, 3), dtype=np.uint8) * 255
                
                # 计算绝对差异
                diff = cv2.absdiff(bgr_image, white_bg)
                
                # 转换为灰度差异图
                diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                
                # 高斯模糊预处理（5x5或7x7核）
                diff_blurred = cv2.GaussianBlur(diff_gray, (5, 5), 0)
                
                # 只对边缘区域应用自适应阈值
                edge_region = diff_blurred.copy()
                edge_region[edge_mask == 0] = 0  # 非边缘区域设为0
                
                # 计算边缘区域的亮度分布，用于设置更严格的阈值
                edge_pixels = diff_blurred[edge_mask > 0]
                if len(edge_pixels) > 0:
                    # 只检测明显比主体暗的区域（使用较低的百分位数）
                    edge_p10 = np.percentile(edge_pixels, 10)
                    edge_p25 = np.percentile(edge_pixels, 25)
                    edge_mean = np.mean(edge_pixels)
                    
                    # 阴影应该比边缘平均亮度暗很多
                    shadow_threshold_value = min(edge_p10 + 10, edge_p25, edge_mean * 0.5)
                    
                    # 使用固定阈值而不是自适应阈值，更可控
                    _, shadow_binary = cv2.threshold(
                        edge_region.astype(np.uint8),
                        max(10, int(shadow_threshold_value)),  # 至少10，避免噪声
                        255,
                        cv2.THRESH_BINARY
                    )
                else:
                    shadow_binary = np.zeros_like(edge_region, dtype=np.uint8)
                
                # 形态学平滑：开运算去掉零散像素
                kernel = np.ones((3, 3), np.uint8)
                shadow_binary = cv2.morphologyEx(shadow_binary, cv2.MORPH_OPEN, kernel)
                
                # 轻微膨胀以包含模糊的阴影边缘
                shadow_binary = cv2.dilate(shadow_binary, kernel, iterations=1)
                
                # 阴影mask：只在边缘区域且差异明显的区域
                shadow_mask = (shadow_binary > 0) & (edge_mask > 0)
                
                logger.info(f"背景差分法检测（边缘区域）: 检测到{np.sum(shadow_mask)}个阴影像素")
                return shadow_mask
            else:
                # 对于非白色背景，使用灰度差异
                gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
                diff = np.abs(gray.astype(np.float32) - bg_brightness)
                diff_normalized = (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)
                
                # 高斯模糊
                diff_blurred = cv2.GaussianBlur(diff_normalized, (5, 5), 0)
                
                # 只对边缘区域应用阈值
                edge_region = diff_blurred.copy()
                edge_region[edge_mask == 0] = 0
                
                # 计算边缘区域的亮度分布
                edge_pixels = diff_blurred[edge_mask > 0]
                if len(edge_pixels) > 0:
                    edge_p10 = np.percentile(edge_pixels, 10)
                    edge_p25 = np.percentile(edge_pixels, 25)
                    edge_mean = np.mean(edge_pixels)
                    
                    shadow_threshold_value = min(edge_p10 + 10, edge_p25, edge_mean * 0.5)
                    
                    _, shadow_binary = cv2.threshold(
                        edge_region.astype(np.uint8),
                        max(10, int(shadow_threshold_value)),
                        255,
                        cv2.THRESH_BINARY
                    )
                else:
                    shadow_binary = np.zeros_like(edge_region, dtype=np.uint8)
                
                # 形态学平滑
                kernel = np.ones((3, 3), np.uint8)
                shadow_binary = cv2.morphologyEx(shadow_binary, cv2.MORPH_OPEN, kernel)
                shadow_binary = cv2.dilate(shadow_binary, kernel, iterations=1)
                
                shadow_mask = (shadow_binary > 0) & (edge_mask > 0)
                logger.info(f"背景差分法检测（非白背景，边缘区域）: 检测到{np.sum(shadow_mask)}个阴影像素")
                return shadow_mask
                
        except Exception as e:
            logger.warning(f"背景差分法检测失败: {e}")
            return np.zeros((bgr_image.shape[0], bgr_image.shape[1]), dtype=bool)
    
    def grabcut_with_edge_assistance(self, bgr_image: np.ndarray, contour: np.ndarray) -> np.ndarray:
        """
        方案2: 改进的GrabCut算法，使用边缘检测辅助
        对于高光泽材质，阴影边缘往往也是高光的交界处
        
        Args:
            bgr_image: BGR格式图像
            contour: 初始轮廓
            
        Returns:
            前景mask（255=前景，0=背景）
        """
        try:
            height, width = bgr_image.shape[:2]
            
            # 创建初始mask
            mask = np.zeros((height, width), dtype=np.uint8)
            
            # 将轮廓区域标记为可能的前景
            cv2.drawContours(mask, [contour], -1, cv2.GC_PR_FGD, -1)
            
            # 获取边界框
            x, y, w, h = cv2.boundingRect(contour)
            margin = 20
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(width - x, w + 2 * margin)
            h = min(height - y, h + 2 * margin)
            
            # 边界框外的区域标记为确定的背景
            mask[0:y, :] = cv2.GC_BGD
            mask[y+h:height, :] = cv2.GC_BGD
            mask[:, 0:x] = cv2.GC_BGD
            mask[:, x+w:width] = cv2.GC_BGD
            
            # 使用边缘检测辅助：Canny边缘检测
            gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # 在边缘附近，如果像素在轮廓内且不是边缘，更可能是前景
            # 边缘像素可能是高光或阴影边界，需要GrabCut来区分
            kernel = np.ones((3, 3), np.uint8)
            edges_dilated = cv2.dilate(edges, kernel, iterations=2)
            
            # 在边缘区域，保持为可能的前景，让GrabCut判断
            # 不在边缘区域的轮廓内部，更可能是确定的前景
            contour_mask = np.zeros_like(gray)
            cv2.drawContours(contour_mask, [contour], -1, 255, -1)
            
            # 轮廓内且不在边缘附近的区域，标记为确定前景
            stable_foreground = (contour_mask > 0) & (edges_dilated == 0)
            mask[stable_foreground] = cv2.GC_FGD
            
            # 创建GMM模型
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # 运行GrabCut算法（增加迭代次数以提高精度）
            rect = (x, y, w, h)
            cv2.grabCut(bgr_image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)
            
            # 创建最终的前景mask
            foreground_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
            
            logger.info("使用边缘辅助的GrabCut算法进行分割")
            return foreground_mask
            
        except Exception as e:
            logger.warning(f"边缘辅助GrabCut失败: {e}")
            # Fallback: 返回原始轮廓mask
            height, width = bgr_image.shape[:2]
            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            return mask
    
    def _check_contour_anomaly(self, contour: np.ndarray) -> Tuple[bool, str, float]:
        """
        检查轮廓的异常情况，判断是否可能包含过多阴影
        
        检测多个指标：
        1. 对称性：阴影通常分布在鞋子的一侧，导致轮廓重心与边界框中心偏移过大
        2. 宽高比：如果轮廓过于扁平（宽高比>3或<0.3），可能包含阴影
        3. 面积占比：如果轮廓面积相对于边界框面积过小，可能有问题
        
        Args:
            contour: 轮廓
            
        Returns:
            (needs_disconnect, reason, score): 是否需要断开，原因，异常分数
        """
        try:
            # 计算轮廓的几何中心（重心）
            M = cv2.moments(contour)
            if M["m00"] == 0:
                return False, "invalid", 0.0
            
            centroid_x = int(M["m10"] / M["m00"])
            centroid_y = int(M["m01"] / M["m00"])
            
            # 计算边界框
            x, y, w, h = cv2.boundingRect(contour)
            bbox_center_x = x + w / 2
            bbox_center_y = y + h / 2
            
            # 指标1: 对称性分析
            offset_x = abs(centroid_x - bbox_center_x)
            offset_y = abs(centroid_y - bbox_center_y)
            offset_distance = np.sqrt(offset_x ** 2 + offset_y ** 2)
            bbox_diagonal = np.sqrt(w ** 2 + h ** 2)
            offset_ratio = offset_distance / bbox_diagonal if bbox_diagonal > 0 else 0.0
            
            # 指标2: 宽高比异常检测
            aspect_ratio = w / h if h > 0 else 0
            is_flat = aspect_ratio > 3.0 or aspect_ratio < 0.33  # 过于扁平
            
            # 指标3: 面积占比（轮廓面积/边界框面积）
            contour_area = cv2.contourArea(contour)
            bbox_area = w * h
            area_ratio = contour_area / bbox_area if bbox_area > 0 else 0
            # 正常鞋子的面积占比通常在40-60%，低于40%可能包含阴影
            is_sparse = area_ratio < 0.40  # 面积占比过小，可能包含大量阴影
            is_marginally_sparse = 0.35 <= area_ratio < 0.40  # 边界情况
            
            # 综合评分（0-1，越高越异常）
            anomaly_score = 0.0
            reasons = []
            
            # 对称性评分（降低阈值到3%）
            if offset_ratio > 0.03:
                # 3%-15%映射到0-1，超过15%直接给满分
                symmetry_score = min(1.0, (offset_ratio - 0.03) / 0.12) if offset_ratio < 0.15 else 1.0
                anomaly_score += symmetry_score * 0.40
                reasons.append(f"对称性偏移{offset_ratio:.1%}")
            
            # 宽高比评分（更激进的检测）
            if is_flat:
                # 宽高比越极端，分数越高
                if aspect_ratio > 3.0:
                    flat_score = min(1.0, (aspect_ratio - 3.0) / 1.5 + 0.6)  # 3-4.5映射到0.6-1.0
                elif aspect_ratio < 0.33:
                    flat_score = min(1.0, (0.33 - aspect_ratio) / 0.25 + 0.6)  # 0.33-0.08映射到0.6-1.0
                else:
                    flat_score = 0.6
                anomaly_score += flat_score * 0.40
                reasons.append(f"宽高比异常{aspect_ratio:.2f}")
            
            # 面积占比评分（更激进的检测）
            if is_sparse:
                # 面积占比越小，分数越高（0-40%映射到1-0）
                sparse_score = (0.40 - area_ratio) / 0.40
                anomaly_score += sparse_score * 0.20
                reasons.append(f"面积占比{area_ratio:.1%}")
            elif is_marginally_sparse:
                # 边界情况：35-40%也给少量分数
                sparse_score = (0.40 - area_ratio) / 0.05 * 0.3  # 35-40%映射到0.3-0
                anomaly_score += sparse_score * 0.20
                reasons.append(f"面积占比偏低{area_ratio:.1%}")
            
            # 如果异常分数超过0.20，认为需要断开（降低阈值）
            needs_disconnect = anomaly_score > 0.20
            reason_str = ", ".join(reasons) if reasons else "正常"
            
            logger.info(f"轮廓异常分析: 对称性偏移={offset_ratio:.1%}, 宽高比={aspect_ratio:.2f}, "
                       f"面积占比={area_ratio:.1%}, 异常分数={anomaly_score:.2f}, 需要断开={needs_disconnect}")
            if reasons:
                logger.info(f"  异常原因: {reason_str}")
            
            return needs_disconnect, reason_str, anomaly_score
            
        except Exception as e:
            logger.warning(f"轮廓异常分析失败: {e}")
            return False, "error", 0.0
    
    def _disconnect_shadow_by_erosion(self, contour: np.ndarray, gray: np.ndarray, anomaly_score: float = 0.5) -> np.ndarray:
        """
        通过智能腐蚀操作断开阴影和鞋子的连接，然后通过膨胀恢复主体
        
        改进策略：
        1. 使用矩形腐蚀核（适应横向长条状鞋子）
        2. 识别高梯度边缘（Canny边缘），保护这些区域不被腐蚀
        3. 只在非边缘区域进行腐蚀，保护细小结构（如蝴蝶结）
        4. 根据异常分数调整腐蚀强度
        
        Args:
            contour: 原始轮廓
            gray: 灰度图像
            anomaly_score: 异常分数（0-1），用于调整腐蚀强度
            
        Returns:
            处理后的轮廓（如果成功），否则返回原始轮廓
        """
        try:
            logger.info("=" * 60)
            logger.info("开始执行智能轮廓断开操作（矩形核+边缘保护）")
            logger.info("=" * 60)
            
            # 创建轮廓mask
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            
            original_area = cv2.contourArea(contour)
            logger.info(f"原始轮廓面积: {original_area:.0f}")
            
            # 获取轮廓边界框和宽高比
            _, _, w, h = cv2.boundingRect(contour)
            min_dimension = min(w, h)
            aspect_ratio = w / h if h > 0 else 1.0
            logger.info(f"轮廓尺寸: {w}x{h}, 宽高比: {aspect_ratio:.2f}, 最小维度: {min_dimension}")
            
            # 步骤1: 识别高梯度边缘（Canny边缘检测）
            # 策略：只保护轮廓中心区域的高对比度边缘，不保护边缘区域的边缘（可能是阴影）
            
            # 计算轮廓的中心区域（排除边缘30%的区域）
            x, y, w, h = cv2.boundingRect(contour)
            center_margin = min(w, h) * 0.3
            center_x1 = int(x + center_margin)
            center_y1 = int(y + center_margin)
            center_x2 = int(x + w - center_margin)
            center_y2 = int(y + h - center_margin)
            
            # 创建中心区域mask
            center_mask = np.zeros(gray.shape, dtype=np.uint8)
            center_mask[center_y1:center_y2, center_x1:center_x2] = 255
            center_mask = cv2.bitwise_and(center_mask, mask)  # 与轮廓mask交集
            
            # 在轮廓区域内进行边缘检测
            gray_roi = gray.copy()
            gray_roi[mask == 0] = 0  # 只保留轮廓区域
            
            # 使用更高的阈值进行Canny边缘检测，只检测高对比度边缘
            # 这样可以避免检测到阴影边缘
            median_val = np.median(gray_roi[gray_roi > 0]) if np.any(gray_roi > 0) else 128
            # 使用更高的阈值，只检测明显的边缘
            low_threshold = max(30, int(median_val * 0.7))
            high_threshold = max(80, int(median_val * 2.0))
            
            edges = cv2.Canny(gray_roi, low_threshold, high_threshold)
            
            # 只保护中心区域的边缘（真正的鞋子边缘）
            center_edges = cv2.bitwise_and(edges, center_mask)
            
            # 将边缘区域稍微膨胀，形成保护区域（保护边缘附近的像素）
            # 使用更小的膨胀，减少保护区域
            edge_protection_kernel = np.ones((3, 3), np.uint8)
            protected_edges = cv2.dilate(center_edges, edge_protection_kernel, iterations=1)
            
            # 创建保护mask：只保护中心区域的高对比度边缘
            protection_mask = (protected_edges > 0) & (mask > 0)
            protection_ratio = np.sum(protection_mask) / original_area if original_area > 0 else 0
            
            logger.info(f"边缘保护: 检测到 {np.sum(protection_mask)} 个受保护的像素 ({protection_ratio:.1%})")
            
            # 计算可腐蚀区域
            erodable_area = original_area - np.sum(protection_mask)
            erodable_ratio = erodable_area / original_area if original_area > 0 else 0
            logger.info(f"可腐蚀区域: {erodable_area:.0f} 像素 ({erodable_ratio:.1%})")
            
            # 步骤2: 根据轮廓形状创建矩形腐蚀核
            # 对于横向长条状（宽高比>1.5），使用横向矩形核
            # 对于纵向长条状（宽高比<0.67），使用纵向矩形核
            # 对于接近方形，使用接近方形的核
            
            base_size = max(3, int(min_dimension * (0.03 + anomaly_score * 0.03)))  # 3-6%的基础大小
            base_size = min(base_size, 15)  # 限制最大为15
            
            if aspect_ratio > 1.5:
                # 横向长条：使用横向矩形核（宽度>高度）
                kernel_w = max(3, int(base_size * (1.0 + (aspect_ratio - 1.5) * 0.5)))  # 宽度更大
                kernel_h = max(3, int(base_size * 0.6))  # 高度较小
                kernel_w = min(kernel_w, 25)  # 限制最大宽度
                kernel_h = min(kernel_h, 9)   # 限制最大高度
            elif aspect_ratio < 0.67:
                # 纵向长条：使用纵向矩形核（高度>宽度）
                kernel_w = max(3, int(base_size * 0.6))  # 宽度较小
                kernel_h = max(3, int(base_size * (1.0 + (0.67 - aspect_ratio) * 0.5)))  # 高度更大
                kernel_w = min(kernel_w, 9)   # 限制最大宽度
                kernel_h = min(kernel_h, 25)  # 限制最大高度
            else:
                # 接近方形：使用接近方形的核
                kernel_w = base_size
                kernel_h = base_size
            
            # 确保是奇数
            if kernel_w % 2 == 0:
                kernel_w += 1
            if kernel_h % 2 == 0:
                kernel_h += 1
            
            logger.info(f"执行智能轮廓断开: 矩形腐蚀核={kernel_w}x{kernel_h}, 宽高比={aspect_ratio:.2f}, 异常分数={anomaly_score:.2f}")
            
            # 步骤3: 创建可腐蚀区域mask（轮廓内但不在保护边缘内）
            erodable_mask = mask.copy()
            erodable_mask[protection_mask] = 0  # 保护边缘区域，不腐蚀
            
            # 步骤4: 尝试不同的腐蚀强度
            best_eroded_mask = None
            best_eroded_ratio = 0
            best_kernel_size = (kernel_w, kernel_h)
            
            # 尝试从当前核大小逐步减小
            best_erodable_reduction = 0  # 记录最佳的可腐蚀区域减少比例
            
            for scale in [1.0, 0.8, 0.6, 0.4, 0.3]:
                attempt_w = max(3, int(kernel_w * scale))
                attempt_h = max(3, int(kernel_h * scale))
                if attempt_w % 2 == 0:
                    attempt_w += 1
                if attempt_h % 2 == 0:
                    attempt_h += 1
                
                # 创建矩形腐蚀核
                attempt_kernel = np.ones((attempt_h, attempt_w), np.uint8)
                
                # 只对可腐蚀区域进行腐蚀
                erodable_eroded = cv2.erode(erodable_mask, attempt_kernel, iterations=1)
                
                # 计算可腐蚀区域的腐蚀效果
                erodable_eroded_area = np.sum(erodable_eroded > 0)
                erodable_eroded_ratio = erodable_eroded_area / erodable_area if erodable_area > 0 else 0
                erodable_reduction = 1.0 - erodable_eroded_ratio  # 可腐蚀区域减少的比例
                
                # 合并：保护区域 + 腐蚀后的可腐蚀区域
                attempt_eroded = erodable_eroded.copy()
                attempt_eroded[protection_mask] = mask[protection_mask]  # 恢复保护区域
                
                attempt_area = np.sum(attempt_eroded > 0)
                attempt_ratio = attempt_area / original_area if original_area > 0 else 0
                
                logger.info(f"尝试矩形腐蚀核 {attempt_w}x{attempt_h}: 总保留面积={attempt_ratio:.1%}, 可腐蚀区域减少={erodable_reduction:.1%}")
                
                # 智能判断逻辑：
                # 1. 如果边缘保护区域很大（>50%），主要看可腐蚀区域的腐蚀效果
                # 2. 如果边缘保护区域较小，看总保留面积
                if protection_ratio > 0.50:
                    # 边缘保护区域很大，主要看可腐蚀区域的腐蚀效果
                    # 如果可腐蚀区域减少了50%以上，认为有效（更激进，确保真正断开）
                    if erodable_reduction > 0.50:
                        best_eroded_mask = attempt_eroded
                        best_eroded_ratio = attempt_ratio
                        best_kernel_size = (attempt_w, attempt_h)
                        best_erodable_reduction = erodable_reduction
                        logger.info(f"找到合适的腐蚀强度（基于可腐蚀区域）: 核大小={attempt_w}x{attempt_h}, 总保留={attempt_ratio:.1%}, 可腐蚀区域减少={erodable_reduction:.1%}")
                        break
                    elif erodable_reduction > best_erodable_reduction:
                        # 可腐蚀区域有一定减少，记录最佳结果但继续尝试
                        best_eroded_mask = attempt_eroded
                        best_eroded_ratio = attempt_ratio
                        best_kernel_size = (attempt_w, attempt_h)
                        best_erodable_reduction = erodable_reduction
                else:
                    # 边缘保护区域较小，使用总保留面积判断
                    if 0.20 <= attempt_ratio <= 0.70:
                        best_eroded_mask = attempt_eroded
                        best_eroded_ratio = attempt_ratio
                        best_kernel_size = (attempt_w, attempt_h)
                        best_erodable_reduction = erodable_reduction
                        logger.info(f"找到合适的腐蚀强度: 核大小={attempt_w}x{attempt_h}, 保留面积={attempt_ratio:.1%}")
                        break
                    elif attempt_ratio > 0.70:
                        # 腐蚀不够，继续尝试更大的核
                        continue
                    else:
                        # 腐蚀过度，记录最佳结果（保留面积最大的）
                        if attempt_ratio > best_eroded_ratio:
                            best_eroded_mask = attempt_eroded
                            best_eroded_ratio = attempt_ratio
                            best_kernel_size = (attempt_w, attempt_h)
                            best_erodable_reduction = erodable_reduction
            
            # 如果边缘保护区域很大，即使总保留面积高，只要可腐蚀区域被有效腐蚀，也应该接受
            if best_eroded_mask is None:
                logger.warning("所有腐蚀尝试都完全失败（未找到任何有效结果），放弃断开操作")
                return contour
            elif protection_ratio > 0.50:
                # 边缘保护区域很大，检查可腐蚀区域的腐蚀效果
                # 要求可腐蚀区域减少40%以上，确保真正断开连接
                if best_erodable_reduction > 0.40:
                    logger.info(f"边缘保护区域大（{protection_ratio:.1%}），可腐蚀区域有效减少（{best_erodable_reduction:.1%}），继续处理")
                else:
                    logger.warning(f"边缘保护区域大，但可腐蚀区域减少不足（{best_erodable_reduction:.1%} < 40%），放弃断开操作")
                    return contour
            elif best_eroded_ratio < 0.05:
                logger.warning(f"所有腐蚀尝试都过度（最佳保留面积={best_eroded_ratio:.1%}，最佳核大小={best_kernel_size[0]}x{best_kernel_size[1]}），放弃断开操作")
                return contour
            elif best_eroded_ratio < 0.15:
                # 虽然过度，但至少保留了一些区域，记录警告但继续
                logger.warning(f"腐蚀过度但保留了一些区域（{best_eroded_ratio:.1%}，核大小={best_kernel_size[0]}x{best_kernel_size[1]}），继续尝试")
            
            eroded_mask = best_eroded_mask
            
            # 使用距离变换找到主体中心区域（更智能的恢复策略）
            # 即使边缘保护区域很大，也使用距离变换来找到真正的中心区域
            dist_transform = cv2.distanceTransform(eroded_mask, cv2.DIST_L2, 5)
            
            # 找到距离最大的点（主体中心）
            max_dist = dist_transform.max()
            if max_dist > 0:
                if protection_ratio > 0.50:
                    # 边缘保护区域很大，使用更宽松的阈值（保留更多区域）
                    # 保留距离大于最大距离30%的区域（主体部分）
                    threshold_ratio = 0.3
                    logger.info(f"边缘保护区域大（{protection_ratio:.1%}），使用宽松距离变换（阈值={threshold_ratio:.0%}）")
                else:
                    # 正常情况，保留距离大于最大距离50%的区域
                    threshold_ratio = 0.5
                
                _, sure_fg = cv2.threshold(dist_transform, max_dist * threshold_ratio, 255, cv2.THRESH_BINARY)
                sure_fg = sure_fg.astype(np.uint8)
            else:
                sure_fg = eroded_mask
            
            # 膨胀恢复主体（使用矩形核，匹配腐蚀核的形状）
            # 使用更保守的膨胀策略，避免恢复已断开的阴影
            if protection_ratio > 0.50:
                # 边缘保护区域很大，使用保守的膨胀策略（避免恢复阴影）
                # 膨胀核约为腐蚀核的50-70%（保守）
                dilation_ratio = 0.5 + (1 - anomaly_score) * 0.2  # 0.5-0.7
                dilation_iterations = 1 + int((1 - anomaly_score) * 0.5)  # 1-2次
                logger.info(f"边缘保护区域大，使用保守膨胀策略（避免恢复阴影）: 膨胀比例={dilation_ratio:.1%}, 迭代次数={dilation_iterations}")
            else:
                # 正常膨胀策略
                dilation_ratio = 0.6 + (1 - anomaly_score) * 0.2  # 异常分数越高，膨胀越小
                dilation_iterations = 1 + int((1 - anomaly_score) * 1)  # 1-2次
            
            dilation_w = max(3, int(best_kernel_size[0] * dilation_ratio))
            dilation_h = max(3, int(best_kernel_size[1] * dilation_ratio))
            
            # 限制膨胀核大小（不超过腐蚀核的1.2倍，更保守）
            dilation_w = min(dilation_w, int(best_kernel_size[0] * 1.2))
            dilation_h = min(dilation_h, int(best_kernel_size[1] * 1.2))
            
            # 确保是奇数
            if dilation_w % 2 == 0:
                dilation_w += 1
            if dilation_h % 2 == 0:
                dilation_h += 1
            
            dilation_kernel = np.ones((dilation_h, dilation_w), np.uint8)
            dilated_mask = cv2.dilate(sure_fg, dilation_kernel, iterations=dilation_iterations)
            
            # 限制膨胀范围：不要超出原始轮廓的边界框太多
            # 这样可以避免恢复已断开的阴影区域
            x, y, w, h = cv2.boundingRect(contour)
            # 允许膨胀超出边界框，但限制在边界框的10%范围内
            margin = max(10, int(min(w, h) * 0.1))
            expanded_bbox = (
                max(0, x - margin),
                max(0, y - margin),
                min(gray.shape[1], x + w + margin),
                min(gray.shape[0], y + h + margin)
            )
            
            # 创建边界框mask
            bbox_mask = np.zeros(gray.shape, dtype=np.uint8)
            bbox_mask[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]] = 255
            
            # 限制膨胀后的mask在边界框内
            dilated_mask = cv2.bitwise_and(dilated_mask, bbox_mask)
            
            # 清理步骤：使用形态学开运算移除可能恢复的细小阴影区域
            # 使用小的核进行开运算，只移除明显的噪声和细小区域
            cleanup_kernel = np.ones((3, 3), np.uint8)
            cleaned_mask = cv2.morphologyEx(dilated_mask, cv2.MORPH_OPEN, cleanup_kernel, iterations=1)
            
            # 从清理后的mask中提取轮廓
            contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 选择最大的轮廓
                disconnected_contour = max(contours, key=cv2.contourArea)
                disconnected_area = cv2.contourArea(disconnected_contour)
                disconnected_ratio = disconnected_area / original_area if original_area > 0 else 0
                
                # 验证断开后的轮廓是否合理
                # 1. 面积占比：至少保留一定比例的面积（根据边缘保护区域调整）
                # 2. 面积占比合理性：断开后的轮廓面积/边界框面积应该在合理范围内（>30%）
                _, _, dw, dh = cv2.boundingRect(disconnected_contour)
                disconnected_bbox_area = dw * dh
                disconnected_area_ratio = disconnected_area / disconnected_bbox_area if disconnected_bbox_area > 0 else 0
                
                # 当边缘保护区域很大时，放宽面积比的验证条件
                # 因为保护区域已经很大，断开后的面积可能相对较小
                min_area_ratio = 0.15 if protection_ratio > 0.50 else 0.30
                
                if disconnected_ratio > min_area_ratio and disconnected_area_ratio > 0.30:
                    logger.info(f"轮廓断开成功: 原始面积 {original_area:.0f} -> 断开后 {disconnected_area:.0f} ({disconnected_ratio:.1%}), 面积占比={disconnected_area_ratio:.1%}")
                    return disconnected_contour
                else:
                    logger.warning(f"断开后轮廓不合理 (面积比={disconnected_ratio:.1%} < {min_area_ratio:.1%}, 面积占比={disconnected_area_ratio:.1%})，保留原始轮廓")
                    return contour
            else:
                logger.warning("断开操作后未找到轮廓，保留原始轮廓")
                return contour
                
        except Exception as e:
            import traceback
            logger.error(f"轮廓断开操作失败: {e}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return contour
    
    def filter_shadow_from_contour(self, contour, gray, bg_brightness, bgr_image=None, detect_saliency_func=None):
        """
        从轮廓中过滤掉阴影部分
        整合三种科学方案：
        1. 基于HSV通道的差异检测（V通道和S通道组合）
        2. 边缘检测辅助的GrabCut算法（适用于高光泽材质）
        3. 基于背景估计的差分法（自适应阈值）
        
        新增：轮廓收缩保护机制
        - 通过对称性分析判断是否包含过多阴影
        - 使用腐蚀-膨胀操作断开阴影和鞋子的连接
        
        预处理：高斯模糊（5x5核）
        后处理：形态学开运算 + 轻微膨胀
        
        Args:
            contour: 检测到的轮廓
            gray: 灰度图像
            bg_brightness: 背景亮度值
            bgr_image: BGR格式的图像（可选，用于高级检测方法）
            detect_saliency_func: 显著性检测函数（可选）
            
        Returns:
            过滤后的轮廓
        """
        try:
            # 第一步：轮廓异常分析和断开保护机制
            # 在阴影检测之前，先判断轮廓是否可能包含过多阴影
            needs_disconnect, reason, anomaly_score = self._check_contour_anomaly(contour)
            
            # 如果检测到异常（可能包含阴影），先尝试断开连接
            if needs_disconnect:
                logger.info(f"检测到轮廓异常（{reason}，异常分数={anomaly_score:.2f}），尝试断开阴影连接")
                disconnected_contour = self._disconnect_shadow_by_erosion(contour, gray, anomaly_score)
                
                # 如果断开操作成功，评估断开后的轮廓是否更合理
                disconnected_area = cv2.contourArea(disconnected_contour)
                original_area = cv2.contourArea(contour)
                
                # 计算面积占比（轮廓面积/边界框面积）
                _, _, ow, oh = cv2.boundingRect(contour)
                original_bbox_area = ow * oh
                original_area_ratio = original_area / original_bbox_area if original_bbox_area > 0 else 0
                
                _, _, dw, dh = cv2.boundingRect(disconnected_contour)
                disconnected_bbox_area = dw * dh
                disconnected_area_ratio = disconnected_area / disconnected_bbox_area if disconnected_bbox_area > 0 else 0
                
                # 判断断开是否有效：
                # 1. 面积减少了15%以上（说明成功移除了阴影）
                # 2. 或者面积占比提高了（说明轮廓更紧凑，更合理）
                # 3. 或者面积增加了但面积占比也提高了（膨胀恢复了主体，但轮廓更合理）
                area_reduction = 1.0 - (disconnected_area / original_area) if original_area > 0 else 0
                area_ratio_improvement = disconnected_area_ratio - original_area_ratio
                
                is_effective = False
                reason_str = ""
                
                if area_reduction > 0.15:
                    is_effective = True
                    reason_str = f"面积减少 {area_reduction:.1%}"
                elif area_ratio_improvement > 0.05:  # 面积占比提高5%以上
                    is_effective = True
                    reason_str = f"面积占比提高 {area_ratio_improvement:.1%} ({original_area_ratio:.1%} -> {disconnected_area_ratio:.1%})"
                elif disconnected_area > original_area * 1.05 and disconnected_area_ratio > original_area_ratio:
                    # 面积增加了但面积占比也提高了，说明膨胀恢复了主体且轮廓更合理
                    is_effective = True
                    reason_str = f"面积增加但轮廓更合理 (面积占比: {original_area_ratio:.1%} -> {disconnected_area_ratio:.1%})"
                
                if is_effective:
                    logger.info(f"断开操作有效（{reason_str}），使用断开后的轮廓继续处理")
                    contour = disconnected_contour
                else:
                    logger.info(f"断开操作效果不明显（面积变化={area_reduction:+.1%}, 面积占比变化={area_ratio_improvement:+.1%}），继续使用原始轮廓")
            
            # 如果提供了BGR图像，优先使用改进的方法
            if bgr_image is not None:
                # 判断图像特征，选择最佳方法
                # 对于黑色或深色鞋子，使用GrabCut或显著性检测
                contour_pixels = gray[cv2.drawContours(np.zeros_like(gray), [contour], -1, 1, -1) > 0]
                if len(contour_pixels) > 0:
                    mean_brightness = np.mean(contour_pixels)
                    
                    # 如果主体较暗（可能是黑色鞋子或高光泽材质），使用边缘辅助GrabCut
                    if mean_brightness < 100:
                        logger.info(f"检测到深色主体（平均亮度={mean_brightness:.1f}），使用边缘辅助GrabCut算法")
                        try:
                            foreground_mask = self.grabcut_with_edge_assistance(bgr_image, contour)
                            # 从mask中提取轮廓
                            filtered_contours, _ = cv2.findContours(foreground_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                            if filtered_contours:
                                # 选择最大的轮廓
                                best_filtered = max(filtered_contours, key=cv2.contourArea)
                                filtered_area = cv2.contourArea(best_filtered)
                                original_area = cv2.contourArea(contour)
                                
                                if filtered_area > original_area * 0.5:
                                    logger.info(f"GrabCut成功过滤阴影: 原始面积 {original_area:.0f} -> 过滤后 {filtered_area:.0f}")
                                    return best_filtered
                        except Exception as e:
                            logger.warning(f"GrabCut失败: {e}，尝试其他方法")
                    
                    # 尝试显著性检测（如果提供了函数）
                    if detect_saliency_func is not None:
                        saliency_map = detect_saliency_func(bgr_image)
                        if saliency_map.max() > 0:
                            try:
                                # 使用显著性图来改进轮廓
                                # 将显著性图二值化
                                _, saliency_binary = cv2.threshold(saliency_map, saliency_map.max() * 0.3, 255, cv2.THRESH_BINARY)
                                # 与原始轮廓mask结合
                                contour_mask = np.zeros_like(gray)
                                cv2.drawContours(contour_mask, [contour], -1, 255, -1)
                                combined_mask = cv2.bitwise_and(saliency_binary, contour_mask)
                                
                                # 从组合mask中提取轮廓
                                filtered_contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                if filtered_contours:
                                    best_filtered = max(filtered_contours, key=cv2.contourArea)
                                    if cv2.contourArea(best_filtered) > cv2.contourArea(contour) * 0.5:
                                        logger.info("显著性检测成功改进轮廓")
                                        return best_filtered
                            except Exception as e:
                                logger.debug(f"显著性检测处理失败: {e}，继续使用其他方法")
            
                # 方案1和方案3: 组合使用HSV通道检测和背景差分法
                shadow_mask_hsv = self.detect_shadow_by_hsv_channels(bgr_image, contour, bg_brightness)
                shadow_mask_bg = self.detect_shadow_by_background_subtraction(bgr_image, contour, bg_brightness)
                
                # 合并两种方法的检测结果
                # 策略：HSV检测结果作为主要依据，背景差分法作为辅助
                hsv_count = np.sum(shadow_mask_hsv)
                bg_count = np.sum(shadow_mask_bg)
                
                # 创建轮廓mask用于计算占比
                contour_mask = np.zeros_like(gray)
                cv2.drawContours(contour_mask, [contour], -1, 1, -1)
                total_pixels_preview = np.sum(contour_mask > 0)
                
                hsv_ratio = hsv_count / total_pixels_preview if total_pixels_preview > 0 else 0
                bg_ratio = bg_count / total_pixels_preview if total_pixels_preview > 0 else 0
                
                # 智能合并策略：
                # 1. 如果背景差分法检测到的阴影占比过大（>30%），说明可能误判了鞋子主体，只使用HSV结果
                # 2. 如果HSV检测到的阴影占比很小（<5%），使用交集更保守
                # 3. 否则使用并集以捕获更多阴影
                if bg_ratio > 0.3:
                    # 背景差分法可能误判，只使用HSV结果
                    combined_shadow_mask = shadow_mask_hsv
                    logger.info(f"背景差分法检测占比过大 ({bg_ratio:.1%})，可能误判，仅使用HSV检测结果")
                elif hsv_count > 0 and hsv_ratio < 0.05:
                    # 保守策略：取交集，只移除两种方法都认为是阴影的区域
                    combined_shadow_mask = shadow_mask_hsv & shadow_mask_bg
                    logger.info(f"使用保守策略（交集）合并阴影检测结果: HSV={hsv_ratio:.1%}, BG={bg_ratio:.1%}")
                else:
                    # 积极策略：取并集，移除任一方法认为是阴影的区域
                    combined_shadow_mask = shadow_mask_hsv | shadow_mask_bg
                    logger.info(f"使用积极策略（并集）合并阴影检测结果: HSV={hsv_ratio:.1%}, BG={bg_ratio:.1%}")
                
                # 形态学平滑：开运算去掉零散像素
                kernel = np.ones((3, 3), np.uint8)
                shadow_binary = combined_shadow_mask.astype(np.uint8) * 255
                shadow_binary = cv2.morphologyEx(shadow_binary, cv2.MORPH_OPEN, kernel)
                
                # 轻微膨胀以包含模糊的阴影边缘
                shadow_binary = cv2.dilate(shadow_binary, kernel, iterations=1)
                combined_shadow_mask = shadow_binary > 0
                
                # 创建轮廓mask
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                
                # 创建过滤后的mask
                filtered_mask = mask.copy()
                filtered_mask[combined_shadow_mask] = 0
                
                # 统计移除的像素数量
                removed_pixels = np.sum(combined_shadow_mask)
                total_pixels = np.sum(mask > 0)
                removal_ratio = removed_pixels / total_pixels if total_pixels > 0 else 0
                
                logger.info(f"阴影检测统计: 总像素={total_pixels}, 移除={removed_pixels} ({removal_ratio:.1%})")
                logger.info(f"  HSV通道检测: {np.sum(shadow_mask_hsv)} 像素")
                logger.info(f"  背景差分法: {np.sum(shadow_mask_bg)} 像素")
                
                if removal_ratio > 0.01:  # 至少移除1%的像素
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
                            
                            # 二次检查：如果过滤后轮廓仍然异常，尝试断开操作
                            needs_recheck, recheck_reason, recheck_score = self._check_contour_anomaly(filtered_contour)
                            if needs_recheck:
                                logger.info(f"过滤后轮廓仍异常（{recheck_reason}，异常分数={recheck_score:.2f}），尝试二次断开")
                                final_contour = self._disconnect_shadow_by_erosion(filtered_contour, gray, recheck_score)
                                final_area = cv2.contourArea(final_contour)
                                
                                # 计算面积占比
                                _, _, fw, fh = cv2.boundingRect(filtered_contour)
                                filtered_bbox_area = fw * fh
                                filtered_area_ratio = filtered_area / filtered_bbox_area if filtered_bbox_area > 0 else 0
                                
                                _, _, final_w, final_h = cv2.boundingRect(final_contour)
                                final_bbox_area = final_w * final_h
                                final_area_ratio = final_area / final_bbox_area if final_bbox_area > 0 else 0
                                
                                # 判断二次断开是否有效
                                area_reduction = 1.0 - (final_area / filtered_area) if filtered_area > 0 else 0
                                area_ratio_improvement = final_area_ratio - filtered_area_ratio
                                
                                is_effective = False
                                reason_str = ""
                                
                                if area_reduction > 0.10:  # 面积减少10%以上
                                    is_effective = True
                                    reason_str = f"面积减少 {area_reduction:.1%}"
                                elif area_ratio_improvement > 0.05:  # 面积占比提高5%以上
                                    is_effective = True
                                    reason_str = f"面积占比提高 {area_ratio_improvement:.1%} ({filtered_area_ratio:.1%} -> {final_area_ratio:.1%})"
                                elif final_area > filtered_area * 1.05 and final_area_ratio > filtered_area_ratio:
                                    # 面积增加了但面积占比也提高了
                                    is_effective = True
                                    reason_str = f"面积增加但轮廓更合理 (面积占比: {filtered_area_ratio:.1%} -> {final_area_ratio:.1%})"
                                
                                if is_effective:
                                    logger.info(f"二次断开有效（{reason_str}），使用断开后的轮廓")
                                    return final_contour
                                else:
                                    logger.info(f"二次断开效果不明显（面积变化={area_reduction:+.1%}, 面积占比变化={area_ratio_improvement:+.1%}），使用过滤后的轮廓")
                            
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
            
            # Fallback: 如果没有BGR图像，使用简化的灰度方法
            logger.info("使用简化的灰度阈值方法过滤阴影")
            
            # 创建轮廓mask
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            
            # 获取轮廓内的所有像素
            contour_pixels = gray[mask > 0]
            
            if len(contour_pixels) == 0:
                return contour
            
            # 高斯模糊预处理
            gray_blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 计算亮度分位数
            p10 = np.percentile(contour_pixels, 10)
            p25 = np.percentile(contour_pixels, 25)
            p50 = np.percentile(contour_pixels, 50)
            
            # 计算阴影阈值
            if bg_brightness > 200:  # 白色背景
                shadow_threshold = min(p10 + 20, p25, p50 - 30)
            else:
                shadow_threshold = min(p10 + 20, p25, p50 - 30)
            
            # 创建阴影mask
            shadow_mask = (gray_blurred < shadow_threshold) & (mask > 0)
            
            # 形态学平滑
            kernel = np.ones((3, 3), np.uint8)
            shadow_binary = shadow_mask.astype(np.uint8) * 255
            shadow_binary = cv2.morphologyEx(shadow_binary, cv2.MORPH_OPEN, kernel)
            shadow_binary = cv2.dilate(shadow_binary, kernel, iterations=1)
            shadow_mask = shadow_binary > 0
            
            # 创建过滤后的mask
            filtered_mask = mask.copy()
            filtered_mask[shadow_mask] = 0
            
            # 统计
            removed_pixels = np.sum(shadow_mask)
            total_pixels = np.sum(mask > 0)
            removal_ratio = removed_pixels / total_pixels if total_pixels > 0 else 0
            
            logger.info(f"灰度方法阴影检测: 移除={removed_pixels} ({removal_ratio:.1%})")
            
            if removal_ratio > 0.01:
                contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    filtered_contour = max(contours, key=cv2.contourArea)
                    filtered_area = cv2.contourArea(filtered_contour)
                    original_area = cv2.contourArea(contour)
                    
                    if filtered_area > original_area * 0.3:
                        logger.info(f"阴影过滤成功: 原始面积 {original_area:.0f} -> 过滤后 {filtered_area:.0f}")
                        return filtered_contour
            
            return contour
                
        except Exception as e:
            logger.error(f"阴影过滤过程出错: {e}")
            return contour
