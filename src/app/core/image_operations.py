"""通用图像处理操作模块。

该模块包含一系列无状态的、可被任何分析器复用的底层图像处理函数。
这些函数封装了OpenCV、scikit-image等库的基础操作。
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any, List
from skimage.filters import threshold_niblack, threshold_sauvola

DEFAULT_GAUSSIAN_KERNEL = (5, 5)

def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """将彩色图像转换为灰度图。"""
    if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def apply_gaussian_blur(image: np.ndarray, kernel_size: Tuple[int, int] = None) -> np.ndarray:
    """对图像应用高斯滤波以减少噪点。"""
    ksize = kernel_size if kernel_size is not None else DEFAULT_GAUSSIAN_KERNEL
    return cv2.GaussianBlur(image, ksize, 0)

def apply_global_threshold(image: np.ndarray, threshold_value: int = 128) -> np.ndarray:
    """应用全局阈值分割。"""
    _, binary = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY_INV)
    return binary

def apply_adaptive_gaussian_threshold(image: np.ndarray, block_size: int = 11, c: int = 2) -> np.ndarray:
    """应用自适应高斯阈值分割。"""
    if block_size % 2 == 0:
        block_size += 1
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, c)

def apply_otsu_threshold(image: np.ndarray) -> Tuple[np.ndarray, int]:
    """应用Otsu阈值分割。"""
    otsu_thresh, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary, int(otsu_thresh)

def apply_niblack_threshold(image: np.ndarray, window_size: int = 25, k: float = 0.2) -> np.ndarray:
    """应用Niblack阈值分割。"""
    if window_size % 2 == 0:
        window_size += 1
    thresh_val = threshold_niblack(image, window_size=window_size, k=k)
    return (image < thresh_val).astype(np.uint8) * 255

def apply_sauvola_threshold(image: np.ndarray, window_size: int = 25, k: float = 0.2, r: float = 128) -> np.ndarray:
    """应用Sauvola阈值分割。"""
    print(f"[DEBUG image_ops] apply_sauvola_threshold called with: window_size={window_size}, k={k}, r={r}")
    if window_size % 2 == 0:
        window_size += 1
    thresh_val = threshold_sauvola(image, window_size=window_size, k=k, r=r)
    return (image < thresh_val).astype(np.uint8) * 255

def create_morphology_kernel(kernel_shape: str = 'rect', kernel_size: Tuple[int, int] = (5, 5)) -> np.ndarray:
    """创建形态学操作的核。"""
    shape_map = {
        'rect': cv2.MORPH_RECT,
        'cross': cv2.MORPH_CROSS,
        'ellipse': cv2.MORPH_ELLIPSE
    }
    shape = shape_map.get(kernel_shape.lower(), cv2.MORPH_RECT)
    return cv2.getStructuringElement(shape, kernel_size)

def _remove_small_noise_by_area(image: np.ndarray, min_area: int) -> np.ndarray:
    """通过连通域面积移除小的噪声点。"""
    output = np.zeros_like(image)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(image, connectivity=8)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            output[labels == i] = 255
    return output

def apply_morphological_postprocessing(
    binary_image: np.ndarray,
    opening_params: Dict[str, Any] = None,
    closing_params: Dict[str, Any] = None
) -> np.ndarray:
    """对二值图像应用形态学后处理（开运算和闭运算）。"""
    print(f"[DEBUG image_ops] apply_morphological_postprocessing called with:")
    print(f"  - opening_params: {opening_params}")
    print(f"  - closing_params: {closing_params}")
    processed_image = binary_image.copy()

    if opening_params and opening_params.get('enabled', False):
        kernel = create_morphology_kernel(opening_params['kernel_shape'], opening_params['kernel_size'])
        iterations = opening_params.get('iterations', 1)
        min_area = opening_params.get('min_area', 0)
        
        opened = cv2.morphologyEx(processed_image, cv2.MORPH_OPEN, kernel, iterations=iterations)
        if min_area > 0:
            processed_image = _remove_small_noise_by_area(opened, min_area)
        else:
            processed_image = opened

    if closing_params and closing_params.get('enabled', False):
        kernel = create_morphology_kernel(closing_params['kernel_shape'], closing_params['kernel_size'])
        iterations = closing_params.get('iterations', 1)
        processed_image = cv2.morphologyEx(processed_image, cv2.MORPH_CLOSE, kernel, iterations=iterations)

    return processed_image

def get_contour_endpoints(contour: np.ndarray) -> List[Tuple[int, int]]:
    """计算轮廓的两个端点。"""
    # 使用最小外接矩形来确定主轴方向
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = box.astype(int)

    # 矩形的四个角点
    p1, p2, p3, p4 = box

    # 计算相邻边的长度平方
    d12_sq = np.sum((p1 - p2)**2)
    d23_sq = np.sum((p2 - p3)**2)

    # 长边中点作为端点近似
    if d12_sq > d23_sq:
        # p1-p2 和 p3-p4 是长边
        mid1 = tuple(((p1 + p2) / 2).astype(int))
        mid2 = tuple(((p3 + p4) / 2).astype(int))
    else:
        # p2-p3 和 p4-p1 是长边
        mid1 = tuple(((p2 + p3) / 2).astype(int))
        mid2 = tuple(((p4 + p1) / 2).astype(int))
    
    # 找到轮廓上离这两个中点最近的点作为精确端点
    distances_to_mid1 = np.linalg.norm(contour.squeeze() - mid1, axis=1)
    endpoint1_idx = np.argmin(distances_to_mid1)
    
    distances_to_mid2 = np.linalg.norm(contour.squeeze() - mid2, axis=1)
    endpoint2_idx = np.argmin(distances_to_mid2)

    return [tuple(contour[endpoint1_idx][0]), tuple(contour[endpoint2_idx][0])]

def merge_contours(contour1: np.ndarray, contour2: np.ndarray) -> np.ndarray:
    """将两个轮廓合并成一个。"""
    # 将两个轮廓的点集合并
    combined_points = np.vstack((contour1, contour2))
    # 计算合并后点集的凸包作为新的轮廓
    merged_contour = cv2.convexHull(combined_points)
    return merged_contour 