"""该模块包含所有核心的图像处理功能。

它负责从图像中识别裂缝，并计算其相关参数。
这是数据处理层的核心部分。

Attributes:
    DEFAULT_GAUSSIAN_KERNEL (tuple): 高斯滤波的默认核大小。
"""

import cv2
import numpy as np
from PIL import Image
import os
from typing import Tuple, Optional, TypedDict, List
from skimage.morphology import skeletonize
from skimage.filters import threshold_niblack, threshold_sauvola

class FractureProperties(TypedDict):
    """单条裂缝的属性数据结构。"""
    contour: np.ndarray
    area_pixels: float
    length_pixels: float
    angle: float
    centroid_pixels: Tuple[float, float]

class ImageProcessor:
    """图像处理器类，包含所有图像处理相关的方法。"""
    
    # 定义默认的高斯滤波核大小
    DEFAULT_GAUSSIAN_KERNEL = (5, 5)
    
    def __init__(self):
        """初始化图像处理器。"""
        self.image = None
        self.dpi = None
    
    def load_image(self, file_path: str) -> Tuple[np.ndarray, Optional[Tuple[float, float]]]:
        """加载图像并获取DPI信息。
        
        使用OpenCV加载图像数据，使用PIL获取DPI信息。
        
        Args:
            file_path (str): 图像文件的路径。
            
        Returns:
            tuple: 包含以下元素的元组:
                - image (numpy.ndarray): OpenCV格式的图像数据
                - dpi (tuple): 图像的DPI信息，格式为(x_dpi, y_dpi)，如果无法获取则为None
                
        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件格式不支持
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        # 检查文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
            raise ValueError(f"不支持的文件格式: {ext}")
            
        # 使用OpenCV加载图像
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"无法加载图像: {file_path}")
            
        # 使用PIL获取DPI信息
        dpi = None
        try:
            with Image.open(file_path) as pil_image:
                dpi_info = pil_image.info.get('dpi')
                if dpi_info and isinstance(dpi_info, tuple) and len(dpi_info) == 2:
                    # 确保DPI值是有效的浮点数
                    x_dpi, y_dpi = float(dpi_info[0]), float(dpi_info[1])
                    if x_dpi > 0 and y_dpi > 0:
                        dpi = (x_dpi, y_dpi)
        except Exception as e:
            print(f"获取DPI信息时出错: {str(e)}")
            
        # 更新实例变量
        self.image = image
        self.dpi = dpi
        
        return image, dpi
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """将彩色图像转换为灰度图。
        
        Args:
            image (numpy.ndarray): 输入的彩色图像。
            
        Returns:
            numpy.ndarray: 转换后的灰度图像。
        """
        # 检查图像是否已经是灰度图
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            return image
            
        # 将彩色图像转换为灰度图
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray_image
    
    def apply_gaussian_blur(self, image: np.ndarray, kernel_size: Tuple[int, int] = None) -> np.ndarray:
        """对图像应用高斯滤波以减少噪点。
        
        Args:
            image (numpy.ndarray): 输入图像，可以是彩色图像或灰度图像。
            kernel_size (tuple, optional): 高斯核大小，格式为(width, height)。
                如果为None，则使用默认值DEFAULT_GAUSSIAN_KERNEL。
                
        Returns:
            numpy.ndarray: 应用高斯滤波后的图像。
        """
        # 如果未指定核大小，则使用默认值
        if kernel_size is None:
            kernel_size = self.DEFAULT_GAUSSIAN_KERNEL
            
        # 应用高斯滤波
        blurred_image = cv2.GaussianBlur(image, kernel_size, 0)
        return blurred_image
        
    def process_image(self, image: np.ndarray) -> np.ndarray:
        """处理图像以识别裂缝。
        
        将图像转换为灰度图，并应用高斯滤波减少噪点。
        这是图像处理流程的第一步。
        
        Args:
            image (numpy.ndarray): 输入图像。
            
        Returns:
            numpy.ndarray: 处理后的图像（灰度图，已去噪）。
        """
        # 1. 将图像转换为灰度图
        gray_image = self.convert_to_grayscale(image)
        
        # 2. 应用高斯滤波减少噪点
        processed_image = self.apply_gaussian_blur(gray_image)
        
        return processed_image

    def apply_global_threshold(self, image: np.ndarray, threshold_value: int = 128) -> np.ndarray:
        """应用全局阈值分割。
        
        Args:
            image: 输入的灰度图像
            threshold_value: 阈值 (0-255)
            
        Returns:
            二值图像
        """
        _, binary = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)
        return binary

    def apply_adaptive_gaussian_threshold(self, image: np.ndarray, block_size: int = 11, c: int = 2) -> np.ndarray:
        """应用自适应高斯阈值分割。
        
        Args:
            image: 输入的灰度图像
            block_size: 局部区域大小，必须是奇数
            c: 从平均值或加权平均值中减去的常数
            
        Returns:
            二值图像
        """
        # 确保block_size是奇数
        if block_size % 2 == 0:
            block_size += 1
            
        binary = cv2.adaptiveThreshold(
            image, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            block_size, 
            c
        )
        return binary

    def apply_otsu_threshold(self, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """应用Otsu阈值分割。
        
        Args:
            image: 输入的灰度图像
            
        Returns:
            tuple: (二值图像, 计算出的最优阈值)
        """
        otsu_thresh, binary = cv2.threshold(
            image, 
            0,  # 初始阈值，会被Otsu方法忽略
            255, 
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return binary, int(otsu_thresh)

    def apply_threshold(self, image: np.ndarray, method: str = 'global', params: dict = None) -> dict:
        """应用阈值分割，将灰度图像转换为二值图像。
        
        Args:
            image: 输入的灰度图像
            method: 阈值方法，可选值: 'global', 'adaptive_gaussian', 'otsu', 'niblack', 'sauvola'
            params: 方法参数字典，根据不同方法需要不同的参数
                - global: {'value': 阈值(0-255)}
                - adaptive_gaussian: {'block_size': 块大小, 'c': 常数}
                - otsu: 不需要参数
                - niblack: {'window_size': 窗口大小, 'k': k值}
                - sauvola: {'window_size': 窗口大小, 'k': k值, 'r': r值}
            
        Returns:
            dict: 包含以下键的字典:
                - 'binary': 二值图像
                - 'threshold': 使用的阈值(对于otsu/global方法)
                - 'method': 使用的方法名称
                - 'params': 使用的参数
        """
        if params is None:
            params = {}
            
        result = {
            'binary': None,
            'threshold': None,
            'method': method,
            'params': params
        }
        
        processed_image = self.process_image(image)
        
        if method == 'global':
            threshold = params.get('value', 128)
            result['binary'] = self.apply_global_threshold(processed_image, threshold)
            result['threshold'] = threshold
            
        elif method == 'adaptive_gaussian':
            block_size = params.get('block_size', 11)
            c = params.get('c', 2)
            result['binary'] = self.apply_adaptive_gaussian_threshold(processed_image, block_size, c)
            
        elif method == 'otsu':
            binary, otsu_thresh = self.apply_otsu_threshold(processed_image)
            result['binary'] = binary
            result['threshold'] = otsu_thresh

        elif method == 'niblack':
            window_size = params.get('window_size', 25)
            k = params.get('k', 0.2)
            if window_size % 2 == 0: window_size += 1
            thresh_val = threshold_niblack(processed_image, window_size=window_size, k=k)
            result['binary'] = (processed_image > thresh_val).astype(np.uint8) * 255

        elif method == 'sauvola':
            window_size = params.get('window_size', 25)
            k = params.get('k', 0.2)
            r = params.get('r', 128)
            if window_size % 2 == 0: window_size += 1
            thresh_val = threshold_sauvola(processed_image, window_size=window_size, k=k, r=r)
            result['binary'] = (processed_image > thresh_val).astype(np.uint8) * 255
        
        else:
            raise ValueError(f"未知的阈值方法: {method}")
        
        print("阈值分割结果:", result);
        return result 
    
    def create_morphology_kernel(self, kernel_shape: str = 'rect', kernel_size: Tuple[int, int] = (5, 5)) -> np.ndarray:
        """创建形态学操作的核。

        Args:
            kernel_shape (str): 核的形状，可选 'rect', 'ellipse', 'cross'。
            kernel_size (tuple): 核的大小。

        Returns:
            numpy.ndarray: 创建的形态学核。
        """
        if kernel_shape == 'rect':
            return cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        elif kernel_shape == 'ellipse':
            return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        elif kernel_shape == 'cross':
            return cv2.getStructuringElement(cv2.MORPH_CROSS, kernel_size)
        else:
            # 默认返回矩形核
            return cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)

    def _remove_small_noise_by_area(self, image: np.ndarray, min_area: int) -> np.ndarray:
        """通过面积阈值移除二值图像中的小噪点。

        Args:
            image (np.ndarray): 输入的二值图像 (噪点为白色)。
            min_area (int): 要保留的最小面积（像素）。

        Returns:
            np.ndarray: 去除小面积噪点后的图像。
        """
        # 查找所有轮廓
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        output_image = np.zeros_like(image)
        
        # 遍历轮廓，只保留面积大于阈值的
        for contour in contours:
            if cv2.contourArea(contour) > min_area:
                cv2.drawContours(output_image, [contour], -1, 255, thickness=cv2.FILLED)
                
        return output_image

    def apply_morphological_postprocessing(
        self, 
        binary_image: np.ndarray, 
        opening_strategy: str = 'standard',
        closing_strategy: str = 'standard',
        params: dict = None
    ) -> dict:
        """对二值图像进行形态学后处理。

        支持两种去噪（开运算）和两种连接（闭运算）策略。

        Args:
            binary_image (numpy.ndarray): 输入的二值图像。
            opening_strategy (str): 去噪策略, 'standard' 或 'area_based'。
            closing_strategy (str): 连接策略, 'standard' 或 'strong'。
            params (dict): 不同策略所需的参数字典。
                - 'opening': {'kernel_size': int, 'kernel_shape': str, 'iterations': int, 'min_area': int}
                - 'closing': {'kernel_size': int, 'kernel_shape': str, 'iterations': int}

        Returns:
            dict: 包含处理后图像及相关参数的字典。
        """
        if params is None:
            params = {}

        processed_image = binary_image.copy()

        # 解包参数
        opening_params = params.get('opening', {})
        opening_ksize = opening_params.get('kernel_size', 0)
        opening_kshape = opening_params.get('kernel_shape', 'rect')
        
        closing_params = params.get('closing', {})
        closing_ksize = closing_params.get('kernel_size', 0)
        closing_kshape = closing_params.get('kernel_shape', 'rect')

        # Step 1: Opening
        if opening_ksize > 0:
            if opening_strategy == 'standard':
                kernel = self.create_morphology_kernel(opening_kshape, (opening_ksize, opening_ksize))
                iterations = opening_params.get('iterations', 1)
                # 正确逻辑：反转 -> 开运算 -> 反转
                inverted_image = cv2.bitwise_not(processed_image)
                opened_inverted = cv2.morphologyEx(inverted_image, cv2.MORPH_OPEN, kernel, iterations=iterations)
                processed_image = cv2.bitwise_not(opened_inverted)
            elif opening_strategy == 'area_based':
                min_area = opening_params.get('min_area', 100)
                # 正确逻辑：反转 -> 移除小面积对象 -> 反转
                inverted_image = cv2.bitwise_not(processed_image)
                denoised_inverted = self._remove_small_noise_by_area(inverted_image, min_area)
                processed_image = cv2.bitwise_not(denoised_inverted)

        # Step 2: Closing
        if closing_ksize > 0:
            kernel = self.create_morphology_kernel(closing_kshape, (closing_ksize, closing_ksize))
            iterations = closing_params.get('iterations', 1)
            # 正确逻辑：反转 -> 闭运算 -> 反转
            inverted_image = cv2.bitwise_not(processed_image)
            closed_inverted = cv2.morphologyEx(inverted_image, cv2.MORPH_CLOSE, kernel, iterations=iterations)
            processed_image = cv2.bitwise_not(closed_inverted)

        return {
            'binary': processed_image,
            'params': params
        }

    def analyze_fractures(
        self, 
        binary_image: np.ndarray, 
        min_aspect_ratio: float = 5.0,
        min_length_pixels: float = 0.0
    ) -> List[FractureProperties]:
        """执行三步分析流水线来检测和测量裂缝。

        Args:
            binary_image (np.ndarray): 输入的二值图像 (形态学处理后)。
            min_aspect_ratio (float): 用于过滤噪声的最小长宽比。
            min_length_pixels (float): 过滤裂缝的最小长度（以像素为单位）。

        Returns:
            List[FractureProperties]: 一个包含所有有效裂缝属性的列表。
        """
        # DEBUG: 记录输入参数
        print(f"[DEBUG] analyze_fractures called with:")
        print(f"  - min_aspect_ratio: {min_aspect_ratio}")
        print(f"  - min_length_pixels: {min_length_pixels}")
        
        # 反转图像颜色，使裂缝（黑色）变为白色，背景（白色）变为黑色
        inverted_image = cv2.bitwise_not(binary_image)

        # 步骤1: 轮廓初筛
        contours, _ = cv2.findContours(inverted_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"[DEBUG] Found {len(contours)} contours in initial detection")
        
        valid_fractures: List[FractureProperties] = []
        
        for i, contour in enumerate(contours):
            # 步骤2: 特征提取与过滤
            if len(contour) < 5:  # minAreaRect 需要至少5个点
                continue

            rect = cv2.minAreaRect(contour)
            (center, (width, height), angle) = rect
            
            if width == 0 or height == 0:
                continue
            
            aspect_ratio = max(width, height) / min(width, height)
            
            # DEBUG: 记录关键轮廓信息
            if i < 10 or i % 50 == 0:  # 只打印前10个和之后每50个，避免太多输出
                print(f"[DEBUG] Contour {i}: width={width:.1f}, height={height:.1f}, aspect_ratio={aspect_ratio:.1f}")
            
            if aspect_ratio >= min_aspect_ratio:
                area_pixels = cv2.contourArea(contour)

                # 步骤3: 精确测量
                mask = np.zeros(binary_image.shape, dtype=np.uint8)
                cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
                skeleton = skeletonize(mask > 0)
                length_pixels = np.sum(skeleton)
                
                # 新增：根据最小长度进行过滤
                if length_pixels < min_length_pixels:
                    print(f"[DEBUG] Filtered out contour due to length: {length_pixels} < {min_length_pixels}")
                    continue

                fracture_props: FractureProperties = {
                    'contour': contour,
                    'area_pixels': area_pixels,
                    'length_pixels': length_pixels,
                    'angle': angle,
                    'centroid_pixels': center,
                }
                valid_fractures.append(fracture_props)
        
        print(f"[DEBUG] Final valid fractures count: {len(valid_fractures)}")
        return valid_fractures

    def merge_fractures(
        self, 
        fractures: List[FractureProperties], 
        max_distance: float, 
        max_angle_diff: float
    ) -> List[FractureProperties]:
        """(待实现) 智能合并距离近、角度相似的断裂轮廓。

        Args:
            fractures (List[FractureProperties]): 待合并的裂缝列表。
            max_distance (float): 合并两个轮廓端点的最大距离阈值。
            max_angle_diff (float): 合并两个轮廓的最大角度差阈值。

        Returns:
            List[FractureProperties]: 合并后的裂缝列表。
        """
        # TODO: 在此实现轮廓合并的详细逻辑。
        # 当前仅返回原始裂缝列表作为占位符。
        print("警告: 'merge_fractures' 功能尚未实现。")
        return fractures

    def draw_analysis_results(
        self, 
        original_image: np.ndarray, 
        fractures: List[FractureProperties]
    ) -> np.ndarray:
        """在图像上绘制检测到的裂缝轮廓。

        Args:
            original_image (np.ndarray): 要绘制的原始图像。
            fractures (List[FractureProperties]): 裂缝属性列表。

        Returns:
            np.ndarray: 带有高亮裂缝轮廓的新图像。
        """
        result_image = original_image.copy()
        
        # 确保图像是彩色的，以便绘制彩色轮廓
        if len(result_image.shape) == 2 or result_image.shape[2] == 1:
            result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)

        # 绘制所有有效裂缝的轮廓
        contours_to_draw = [fracture['contour'] for fracture in fractures]
        cv2.drawContours(result_image, contours_to_draw, -1, (0, 0, 255), 2)  # 红色轮廓
        
        return result_image 